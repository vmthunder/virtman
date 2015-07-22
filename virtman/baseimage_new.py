import time
from oslo.config import cfg
from taskflow.utils.misc import Failure as ft
from taskflow import engines
from taskflow.patterns import linear_flow
from taskflow import task

from virtman.drivers import fcg
from virtman.drivers import dmsetup
from virtman.drivers import iscsi
from virtman.drivers import volt
from virtman.path import Path
from virtman.path import Paths
from virtman.utils import utils

from virtman.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

MAX_COUNT = 120
WAIT_TIME = 5


class BaseImage(object):
    def __init__(self):
        pass

    def deploy_base_image(self):
        raise NotImplementedError()

    def destroy_base_image(self):
        raise NotImplementedError()


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

    def adjust_for_heartbeat(self, parents):
        LOG.debug('Virtman: adjust_for_heartbeat according to '
                  'connections: %s ' % parents)
        parent_connections = utils.reform_connections(parents)
        if self.is_local_has_image or len(parent_connections) == 0:
            parent_connections = self.image_connections
        self.rebuild_multipath(parent_connections)

    def deploy_base_image(self):
        try:
            self.deploy()
        except Exception as ex:
            LOG.error("Virtman: fail to deploy base image '%s', duo to %s" %
                      (self.image_name, ex))
            raise
        else:
            return self.origin_path

    def check_local_image(self):
        found = None
        for connection in self.image_connections:
            if connection['target_portal'].find(CONF.host_ip) >= 0:
                found = connection
                break
        if found is not None:
            self.image_connections = [found]
            self.is_local_has_image = True
        else:
            self.is_local_has_image = False
        LOG.debug("Virtman: my host_ip = %s, is_local_has_image = %s!,"
                  " now image_connections = %s" %
                  (CONF.host_ip, self.is_local_has_image,
                   self.image_connections))

    def modify_parent_connection(self):
        if self.is_local_has_image:
            parent_connections = self.image_connections
        else:
            parent_connections = \
                utils.reform_connections(self.get_parent()) or \
                self.image_connections

        return parent_connections

    def deploy(self):
        """
        deploy image in compute node, return the origin path to create snapshot
        :returns origin_path: origin path to create snapshot
        """
        LOG.debug("Virtman: in deploy_base_image, image name = %s, "
                  "multipath_path = %s, origin_path = %s, cached_path = %s, "
                  "is_login = %s" %
                  (self.image_name, self.multipath_path,
                   self.origin_path, self.cached_path,
                   self.is_login))

        # Check if it had origin or not!
        if self.origin_path:
            return self.origin_path

        # check local image and save the image connections
        self.check_local_image()

        # Reform connections
        # If it has image on the local node or no path to connect, connect to
        # root
        parent_connections = self.modify_parent_connection()

        # rebuild multipath
        self.rebuild_multipath(parent_connections)

        # build_chain = Chain()
        # build_chain.add_step(
        #     partial(Cache.create_cache, base_image),
        #     partial(Cache.delete_cache, base_image))
        # build_chain.add_step(
        #     partial(Origin.create_origin, base_image),
        #     partial(Origin.delete_origin, base_image))
        # build_chain.add_step(
        #     partial(Target.create_target, base_image),
        #     partial(Target.delete_target, base_image))
        # build_chain.add_step(
        #     partial(Register.login_master, base_image),
        #     partial(Register.logout_master, base_image))
        # build_chain.do()

        wf = linear_flow.Flow("base_image_flow")
        wf.add(CreateCacheTask(),
               CreateOriginTask(),
               CreateTargetTask(),
               LoginMasterTask()
               )

        dict_for_task = dict(base_image=self)
        en = engines.load(wf, store=dict_for_task)
        en.run()

        LOG.debug("Virtman: baseimage OK!\n"
                  "target_id =  %s, origin_path = %s, origin_name = %s, "
                  "cached_path = %s, multipath_path = %s, multipath_name = %s" %
                  (self.target_id, self.origin_path,
                   self.origin_name, self.cached_path,
                   self.multipath_path, self.multipath_name))

    def destroy_base_image(self):
        LOG.debug("Virtman: destroy base_image = %s, peer_id = %s" %
                  (self.image_name, self.peer_id))
        # if base_image.is_local_has_image:
        #     return False
        if self.is_login:
            Volt.logout_master(self)

        if self.has_target:
            if iscsi.is_connected(self.target_id):
                LOG.debug("Virtman: destroy base image Failed! iscsi target "
                          "for this base image is connected.")
                return False
            try:
                Target.delete_target(self)
            except Exception as ex:
                LOG.debug("Virtman: delete target for base image %s fail, "
                          "due to %s" % (self.image_name, ex))
                return False

        if self.origin_path:
            try:
                Origin.delete_origin(self)
            except Exception as ex:
                LOG.debug("Virtman: delete origin for base image %s fail, "
                          "due to %s" % (self.image_name, ex))
                return False

        time.sleep(1)

        if self.cached_path:
            try:
                Cache.delete_cache(self)
            except Exception as ex:
                LOG.debug("Virtman: delete cache for base image %s fail, "
                          "due to %s" % (self.image_name, ex))
                return False

        if self.multipath_path:
            try:
                self.delete_multipath()
            except Exception as ex:
                LOG.debug("Virtman: delete multipath for base image %s fail, "
                          "due to %s" % (self.image_name, ex))
                return False
        try:
            for key in self.paths.keys():
                Path.disconnect(self.paths[key])
                del self.paths[key]
            LOG.debug("Virtman: destroy base image SUCCESS! base_image = %s, "
                      "peer_id = %s" % (self.image_name,
                                        self.peer_id))
            return True
        except Exception as ex:
            LOG.debug("Virtman: destroy base image %s fail, due to %s" %
                      (self.image_name, ex))
            return False

    def rebuild_multipath(self, parent_connections):
        """
        :type parent_connections: list
        """
        self.multipath_path = \
            Paths.rebuild_multipath(self.paths, parent_connections,
                                    self.multipath_name,
                                    self.multipath_path)

    def delete_multipath(self):
        if self.multipath_path:
            LOG.debug("Virtman: delete multipath path '%s'" %
                      self.multipath_path)
            Paths.delete_multipath(self.multipath_name)
            self.multipath_path = None

    def get_parent(self):
        max_try_count = MAX_COUNT
        host_ip = CONF.host_ip
        try_times = 0
        while True:
            try:
                self.peer_id, parent_list = \
                    volt.get(session_name=self.image_name, host=host_ip)
                LOG.debug("Virtman: in get_parent function, peer_id = %s, "
                          "parent_list = %s:" % (self.peer_id,
                                                 parent_list))
                if len(parent_list) == 1 and parent_list[0].peer_id is None:
                    raise Exception("parents is in pending")
                return parent_list
            except Exception, e:
                LOG.warn("Virtman: get parent info from volt server failed "
                         "due to %s, tried %d times" % (e, try_times))
                if try_times < max_try_count:
                    time.sleep(WAIT_TIME)
                    try_times += 1
                    continue
                else:
                    raise Exception("get parent info timeout")


class Qcow2BaseImage(BaseImage):
    pass


class Cache(object):
    @staticmethod
    def create_cache(base_image):
        """
        :type base_image: BlockDeviceBaseImage
        """
        if not base_image.cached_path:
            LOG.debug("Virtman: create cache for base image %s according to "
                      "multipath %s" %
                      (base_image.image_name, base_image.multipath_path))
            base_image.cached_path = fcg.add_disk(base_image.multipath_path)
            LOG.debug("Virtman: create cache completed, cache path = %s" %
                      base_image.cached_path)
        # return base_image.cached_path

    @staticmethod
    def delete_cache(base_image):
        """
        :type base_image: BlockDeviceBaseImage
        """
        if base_image.cached_path:
            LOG.debug("Virtman: start to delete cache according to multipath %s " %
                      base_image.multipath_path)
            fcg.rm_disk(base_image.multipath_path)
            base_image.cached_path = None
            LOG.debug("Virtman: delete cache according to multipath %s "
                      "completed" %
                      base_image.multipath_path)


class Origin(object):
    @staticmethod
    def create_origin(base_image):
        """
        :type base_image: BlockDeviceBaseImage
        """
        if not base_image.origin_path:
            LOG.debug("Virtman: start to create origin, cache path = %s" %
                      base_image.cached_path)
            base_image.origin_path = dmsetup.origin(base_image.origin_name,
                                                    base_image.cached_path)
            LOG.debug("Virtman: create origin complete, origin path = %s" %
                      base_image.origin_path)
        return base_image.origin_path

    @staticmethod
    def delete_origin(base_image):
        """
        :type base_image: BlockDeviceBaseImage
        """
        if base_image.origin_path:
            LOG.debug("Virtman: start to remove origin %s " %
                      base_image.origin_name)
            dmsetup.remove_table(base_image.origin_name)
            base_image.origin_path = None
            LOG.debug("Virtman: remove origin %s completed" %
                      base_image.origin_name)


class Target(object):
    @staticmethod
    def create_target(base_image):
        """
        :type base_image: BlockDeviceBaseImage
        """
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
        """
        :type base_image: BlockDeviceBaseImage
        """
        if base_image.has_target:
            LOG.debug("Virtman: start to remove target %s (%s)" %
                      (base_image.target_id, base_image.image_name))
            iscsi.remove_iscsi_target(base_image.image_name,
                                      base_image.image_name)
            LOG.debug("Virtman: successful remove target %s (%s)" %
                      (base_image.target_id, base_image.image_name))
            base_image.has_target = False
            base_image.target_id = 0



class Volt(object):
    @staticmethod
    def login_master(base_image):
        """
        :type base_image: BlockDeviceBaseImage
        """
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
        """
        :type base_image: BlockDeviceBaseImage
        """
        if base_image.is_login:
            volt.logout(base_image.image_name, peer_id=base_image.peer_id)
            base_image.is_login = False
            LOG.debug("Virtman: logout master session = %s, peer_id = %s" %
                      (base_image.image_name, base_image.peer_id))


class CreateCacheTask(task.Task):
    def execute(self, base_image, **kwargs):
        Cache.create_cache(base_image)

    def revert(self, base_image, result, **kwargs):
        if isinstance(result, ft.Failure):
            LOG.exception("Virtman: base image '%s' create caceh failed, "
                          "due to %s" %
                          (base_image.image_name, result.exception_str))
        Cache.delete_cache(base_image)


class CreateOriginTask(task.Task):
    def execute(self, base_image, **kwargs):
        Origin.create_origin(base_image)

    def revert(self, base_image, result, **kwargs):
        if isinstance(result, ft.Failure):
            LOG.exception("Virtman: base image '%s' create origin failed, "
                          "due to %s" %
                          (base_image.image_name, result.exception_str))
        Origin.delete_origin(base_image)


class CreateTargetTask(task.Task):
    def execute(self, base_image,  **kwargs):
        Target.create_target(base_image)

    def revert(self, base_image, result, **kwargs):
        if isinstance(result, ft.Failure):
            LOG.exception("Virtman: base image '%s' create target failed, "
                          "due to %s" %
                          (base_image.image_name, result.exception_str))
        Target.delete_target(base_image)


class LoginMasterTask(task.Task):
    def execute(self, base_image, **kwargs):
        Volt.login_master(base_image)

    def revert(self, base_image, result, **kwargs):
        if isinstance(result, ft.Failure):
            LOG.exception("Virtman: base image '%s' login failed, due to %s" %
                          (base_image.image_name, result.exception_str))
        Volt.logout_master(base_image)


class FakeBaseImage(BaseImage):
    def __init__(self, image_name, image_connections):
        super(FakeBaseImage, self).__init__()
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

    def deploy_base_image(self):
        self.target_id = 1
        self.has_target = True
        self.origin_path = '/dev/mapper/test_origin'
        self.origin_name = 'origin_test_baseimage'
        self.cached_path = '/dev/mapper/test_cached'
        self.multipath_path = '/dev/mapper/test_multipath'
        self.multipath_name = 'multipath_test_baseimage'
        self.peer_id = 'test_peer_id'
        return self.origin_path

    def destroy_base_image(self):
        self.has_target = False
        self.target_id = 0
        self.origin_path = None
        self.cached_path = None
        self.multipath_path = None
        return True
