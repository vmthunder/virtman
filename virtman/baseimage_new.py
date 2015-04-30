import time
from functools import partial
from oslo.config import cfg

from virtman.drivers import fcg
from virtman.drivers import dmsetup
from virtman.drivers import iscsi
from virtman.drivers import volt
from virtman.path import Path
from virtman.utils import utils
from virtman.utils.chain import Chain

from virtman.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class BaseImage(object):
    def __init__(self):
        pass

    def deploy_base_image(self):
        return NotImplementedError()

    def destroy_base_image(self):
        return NotImplementedError()


class BlockDeviceBaseImage(BaseImage):
    def __init__(self, image_name, image_connections):
        super(BlockDeviceBaseImage, self).__init__()
        self.image_name = image_name
        self.multipath_name = 'multipath_' + self.image_name
        self.origin_name = 'origin_' + self.image_name
        self.image_connections = utils.reform_connections(image_connections)
        self.is_local_has_image = False
        self.paths = {}
        self.has_target = False
        self.is_login = False
        self.iqn = self.image_connections[0]['target_iqn']
        self.multipath_path = None
        self.cached_path = None
        self.origin_path = None
        self.peer_id = ''
        self.target_id = 0
        LOG.debug("Virtman: initialize base image of image_name %s" %
                  self.image_name)

    @staticmethod
    def adjust_for_heartbeat(base_image, parents):
        """
        :type base_image: BlockDeviceBaseImage
        """
        LOG.debug('Virtman: adjust_for_heartbeat according to '
                  'connections: %s ' % parents)
        parent_connections = utils.reform_connections(parents)
        BlockDeviceBaseImage.rebuild_multipath(base_image, parent_connections)

    @staticmethod
    def deploy_base_image(base_image):
        try:
            origin_path = BlockDeviceBaseImage.deploy(base_image)
        except Exception as e:
            LOG.error(e)
            raise
        else:
            return origin_path

    @staticmethod
    def check_local_image(base_image):
        """
        :type base_image: object
        """
        found = None
        for connection in base_image.image_connections:
            if connection['target_portal'].find(CONF.host_ip) >= 0:
                found = connection
                break
        if found is not None:
            base_image.image_connections = [found]
            base_image.is_local_has_image = True
        LOG.debug("Virtman: my host_ip = %s, is_local_has_image = %s!,"
                  " now image_connections = %s" %
                  (CONF.host_ip, base_image.is_local_has_image,
                   base_image.image_connections))

    @staticmethod
    def deploy(base_image):
        """
        deploy image in compute node, return the origin path to create snapshot
        :param image_connection: the connection towards to the base image
        :returns: origin path to create snapshot
        """
        LOG.debug("Virtman: in deploy_base_image, image name = %s, "
                  "has multipath = %s, has origin = %s, has cache = %s, "
                  "is_login = %s" %
                  (base_image.image_name, base_image.has_multipath,
                   base_image.has_origin, base_image.has_cache,
                   base_image.is_login))
        # Check if it had origin or not!
        if base_image.origin_path:
            return base_image.origin_path

        # save the base_image paths
        base_image.check_local_image(base_image)

        # Reform connections
        if base_image.is_local_has_image:
            parent_connections = []
        else:
            parent_connections = \
                utils.reform_connections(base_image.get_parent())

        # rebuild multipath
        base_image.rebuild_multipath(parent_connections)

        build_chain = Chain()
        build_chain.add_step(
            partial(BlockDeviceBaseImage.create_cache, base_image),
            partial(BlockDeviceBaseImage.delete_cache, base_image))
        build_chain.add_step(
            partial(BlockDeviceBaseImage.create_origin, base_image),
            partial(BlockDeviceBaseImage.delete_origin, base_image))
        build_chain.add_step(
            partial(BlockDeviceBaseImage.create_target, base_image),
            partial(BlockDeviceBaseImage.delete_target, base_image))
        build_chain.add_step(
            partial(BlockDeviceBaseImage.login_master, base_image),
            partial(BlockDeviceBaseImage.logout_master, base_image))
        build_chain.do()

        # self._create_cache()
        # self._create_origin()
        # self._create_target()
        # self._login_master()

        LOG.debug("Virtman: baseimage OK!\n"
                  "target_id =  %s, origin_path = %s, origin_name = %s, "
                  "cached_path = %s, multipath_path = %s, multipath_name = %s" %
                  (base_image.target_id, base_image.origin_path,
                   base_image.origin_name, base_image.cached_path,
                   base_image.multipath_path, base_image.multipath_name))

        return base_image.origin_path

    @staticmethod
    def destroy_base_image(base_image):
        LOG.debug("Virtman: destroy base_image = %s, peer_id = %s" %
                  (base_image.image_name, base_image.peer_id))
        # if base_image.is_local_has_image:
        #     return False
        if base_image.is_login:
            BlockDeviceBaseImage.logout_master(base_image)

        if base_image.has_target:
            if iscsi.is_connected(base_image.target_id):
                LOG.debug("Virtman: destroy base image Failed! iscsi target "
                          "for this base image is connected.")
                return False
            try:
                BlockDeviceBaseImage.delete_target(base_image)
            except Exception as ex:
                LOG.debug("Virtman: delete target for base image %s fail, "
                          "due to %s" % (base_image.image_name, ex))
                return False

        if base_image.origin_path:
            try:
                BlockDeviceBaseImage.delete_origin(base_image)
            except Exception as ex:
                LOG.debug("Virtman: delete origin for base image %s fail, "
                          "due to %s" % (base_image.image_name, ex))
                return False

        time.sleep(1)

        if base_image.cached_path:
            try:
                BlockDeviceBaseImage.delete_cache(base_image)
            except Exception as ex:
                LOG.debug("Virtman: delete cache for base image %s fail, "
                          "due to %s" % (base_image.image_name, ex))
                return False

        if base_image.multipath_path:
            try:
                BlockDeviceBaseImage.delete_multipath(base_image)
            except Exception as ex:
                LOG.debug("Virtman: delete multipath for base image %s fail, "
                          "due to %s" % (base_image.image_name, ex))
                return False
        try:
            for key in base_image.paths.keys():
                base_image.paths[key].disconnect()
                del base_image.paths[key]
            LOG.debug("Virtman: destroy base image SUCCESS! base_image = %s, "
                      "peer_id = %s" % (base_image.image_name,
                                        base_image.peer_id))
            return True
        except Exception as ex:
            LOG.debug("Virtman: destroy base image base %s fail, due to %s" %
                      (base_image.image_name, ex))
            return False


    @staticmethod
    def rebuild_multipath(base_image, parent_connections):
        """
        :param parent_connections: list
        """
        LOG.debug("Virtman: begin to rebuild multipath...")
        # If it has image on the local node or no path to connect, connect to
        # root
        if base_image.is_local_has_image or len(parent_connections) == 0:
            parent_connections = base_image.image_connections
            LOG.debug("Virtman: the parents were modified! now parents = %s" %
                      parent_connections)

        # Get keys of paths to remove, and add new paths
        paths_to_remove = []
        for key in base_image.paths.keys():
            found = False
            for connection in parent_connections:
                if key == Path.connection_to_str(connection):
                    found = True
                    break
            if not found:
                paths_to_remove.append(key)
        for connection in parent_connections:
            if not isinstance(connection, dict):
                raise (Exception("Unknown %s type of %s " %
                                 (type(connection), connection)))
            key = Path.connection_to_str(connection)
            if key not in base_image.paths:
                base_image.paths[key] = Path(connection)

        # Connect new paths
        for key in base_image.paths.keys():
            if key not in paths_to_remove and \
                    not base_image.paths[key].connected:
                base_image.paths[key].connect()

        # Rebuild multipath device
        disks = [base_image.paths[key].device_path for key in
                 base_image.paths.keys() if key not in paths_to_remove and
                 base_image.paths[key].connected]
        if len(disks) > 0:
            if not base_image.has_multipath:
                base_image.create_multipath(disks)
            else:
                base_image.reload_multipath(disks)
            # TODO:fix here, wait for multipath device ready
            time.sleep(2)

        # Disconnect paths to remove
        for key in paths_to_remove:
            if base_image.paths[key].connected:
                base_image.paths[key].disconnect()
            del base_image.paths[key]

        LOG.debug("Virtman: rebuild multipath completed, multipath = %s" %
                  base_image.multipath_path)

    @staticmethod
    def create_multipath(base_image, disks):
        if not base_image.has_multipath:
            base_image.multipath_path = \
                dmsetup.multipath(base_image.multipath_name, disks)
            base_image.has_multipath = True
            LOG.debug("Virtman: create multipath according connection %s:" %
                      disks)
        return base_image.multipath_path

    @staticmethod
    def reload_multipath(bae_image, disks):
        dmsetup.reload_multipath(bae_image.multipath_name, disks)

    @staticmethod
    def delete_multipath(base_image):
        LOG.debug("Virtman: delete multipath %s start!" %
                  base_image.multipath_name)
        dmsetup.remove_table(base_image.multipath_name)
        base_image.multipath_path = None
        LOG.debug("Virtman: delete multipath %s completed  !" %
                  base_image.multipath_name)

    @staticmethod
    def create_cache(base_image):
        if not base_image.has_cache:
            LOG.debug("Virtman: create cache for base image %s according to "
                      "multipath %s" %
                      (base_image.image_name, base_image.multipath_path))
            base_image.cached_path = fcg.add_disk(base_image.multipath_path)
            base_image.has_cache = True
            LOG.debug("Virtman: create cache completed, cache path = %s" %
                      base_image.cached_path)
        return base_image.cached_path

    @staticmethod
    def delete_cache(base_image):
        LOG.debug("Virtman: start to delete cache according to multipath %s " %
                  base_image.multipath_path)
        fcg.rm_disk(base_image.multipath_path)
        base_image.cached_path = None
        LOG.debug("Virtman: delete cache according to multipath %s completed" %
                  base_image.multipath_path)

    @staticmethod
    def create_origin(base_image):
        if not base_image.has_origin:
            LOG.debug("Virtman: start to create origin, cache path = %s" %
                      base_image.cached_path)
            base_image.origin_path = dmsetup.origin(base_image.origin_name,
                                              base_image.cached_path)
            base_image.has_origin = True
            LOG.debug("Virtman: create origin complete, origin path = %s" %
                      base_image.origin_path)
        return base_image.origin_path

    @staticmethod
    def delete_origin(base_image):
        LOG.debug("Virtman: start to remove origin %s " %
                  base_image.origin_name)
        dmsetup.remove_table(base_image.origin_name)
        base_image.origin_path = None
        LOG.debug("Virtman: remove origin %s completed" %
                  base_image.origin_name)

    @staticmethod
    def create_target(base_image):
        if base_image.is_local_has_image:
            return
        if not base_image.has_target:
            LOG.debug("Virtman: start to create target, cache path = %s" %
                      base_image.cached_path)
            if iscsi.exists(base_image.iqn):
                base_image.has_target = True
            else:
                base_image.target_id = \
                    iscsi.create_iscsi_target(base_image.iqn,
                                              base_image.cached_path)
                base_image.has_target = True
                LOG.debug("Virtman: create target complete, target id = %s" %
                          base_image.target_id)

    @staticmethod
    def delete_target(base_image):
        LOG.debug("Virtman: start to remove target %s (%s)" %
                  (base_image.target_id, base_image.image_name))
        iscsi.remove_iscsi_target(base_image.image_name, base_image.image_name)
        base_image.has_target = False
        LOG.debug("Virtman: successful remove target %s (%s)" %
                  (base_image.target_id, base_image.image_name))

    @staticmethod
    def login_master(base_image):
        if base_image.is_local_has_image:
            return
        LOG.debug("Virtman: try to login to master server")
        if not base_image.is_login:
            info = volt.login(session_name=base_image.image_name,
                              peer_id=base_image.peer_id,
                              host=CONF.host_ip,
                              port='3260',
                              iqn=base_image.iqn,
                              lun='1')
            LOG.debug("Virtman: login to master server %s" % info)
            base_image.is_login = True

    @staticmethod
    def logout_master(base_image):
        if base_image.is_login:
            volt.logout(base_image.image_name, peer_id=base_image.peer_id)
            base_image.is_login = False
            LOG.debug("Virtman: logout master session = %s, peer_id = %s" %
                      (base_image.image_name, base_image.peer_id))

    @staticmethod
    def get_parent(base_image):
        max_try_count = 120
        host_ip = CONF.host_ip
        try_times = 0
        while True:
            try:
                base_image.peer_id, parent_list = \
                    volt.get(session_name=base_image.image_name, host=host_ip)
                LOG.debug("Virtman: in get_parent function, peer_id = %s, "
                          "parent_list = %s:" % (base_image.peer_id,
                                                 parent_list))
                if len(parent_list) == 1 and parent_list[0].peer_id is None:
                    raise Exception("parents is in pending")
                return parent_list
            except Exception, e:
                LOG.warn("Virtman: get parent info from volt server failed "
                         "due to %s, tried %d times" % (e, try_times))
                if try_times < max_try_count:
                    time.sleep(5)
                    try_times += 1
                    continue
                else:
                    raise Exception("get parent info timeout")


class Qcow2BaseImage(BaseImage):
    pass


class Cache(object):
    def create_cache(multipath_path):
        LOG.debug("Virtman: create cache for baseimage according to "
                  "multipath %s" % multipath_path)
        try:
            cached_path = fcg.add_disk(multipath_path)
        except Exception:
            raise
        LOG.debug("Virtman: create cache completed, cache path = %s" %
                  cached_path)
        return cached_path

    def delete_cache(multipath_path):
        LOG.debug("Virtman: start to delete cache according to multipath %s " %
                  multipath_path)
        try:
            fcg.rm_disk(multipath_path)
        except Exception:
            raise
        LOG.debug("Virtman: delete cache according to multipath %s completed" %
                  multipath_path)


class Origin(object):
    @staticmethod
    def create_origin(origin_name, cached_path):
        LOG.debug("Virtman: start to create origin, cache path = %s" %
                  cached_path)
        try:
            origin_path = dmsetup.origin(origin_name,
                                         cached_path)
        except Exception:
            raise
        LOG.debug("Virtman: create origin complete, origin path = %s" %
                  origin_path)
        return origin_path

    @staticmethod
    def delete_origin(origin_name):
        LOG.debug("Virtman: start to remove origin %s " % origin_name)
        try:
            dmsetup.remove_table(origin_name)
        except Exception:
            raise
        LOG.debug("Virtman: remove origin %s completed" % origin_name)


class Target(object):
    @staticmethod
    def create_target(iqn, cached_path):
        LOG.debug("Virtman: start to create target, cache path = %s" %
                  cached_path)
        if iscsi.exists(iqn):
            return
        else:
            try:
                target_id = iscsi.create_iscsi_target(iqn, cached_path)
            except Exception:
                raise
        LOG.debug("Virtman: create target complete, target id = %s" %
                  target_id)
        return target_id

    @staticmethod
    def delete_target(target_id, image_name):
        LOG.debug("Virtman: start to remove target %s (%s)" %
                  (target_id, image_name))
        try:
            iscsi.remove_iscsi_target(image_name, image_name)
        except Exception:
            raise
        LOG.debug("Virtman: successful remove target %s (%s)" %
                  (target_id, image_name))


class Master(object):
    @staticmethod
    def login_master(image_name, peer_id, iqn):
        LOG.debug("Virtman: try to login to master server")
        try:
            info = volt.login(session_name=image_name,
                              peer_id=peer_id,
                              host=CONF.host_ip,
                              port='3260',
                              iqn=iqn,
                              lun='1')
        except Exception:
            raise
        LOG.debug("Virtman: login to master server %s" % info)

    @staticmethod
    def logout_master(image_name, peer_id):
        LOG.debug("Virtman: logout master session = %s, peer_id = %s" %
                  (image_name, peer_id))
        try:
            volt.logout(session_name=image_name, peer_id=peer_id)
        except Exception:
            raise