#!/usr/bin/env python

import eventlet
import time
import threading
from functools import partial
from oslo.config import cfg

from virtman.drivers import fcg
from virtman.drivers import dmsetup
from virtman.drivers import iscsi
from virtman.drivers import volt
from virtman.path import connection_to_str
from virtman.path import Path
from virtman.utils import utils
from virtman.utils.enum import Enum
from virtman.utils.chain import Chain


from virtman.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

STATUS = Enum(['empty', 'building', 'ok', 'destroying', 'error'])
ACTIONS = Enum(['build', 'destroy'])


class BaseImage(object):

    def __init__(self):
        pass

    def deploy_base_image(self):
        return NotImplementedError()

    def destroy_base_image(self):
        return NotImplementedError()


class BlockDeviceBaseImage(BaseImage):

    def __init__(self, image_name, image_connections):
        self.image_name = image_name
        self.image_connections = utils.reform_connections(image_connections)
        self.is_local_has_image = False
        self.paths = {}
        self.has_multipath = False
        self.has_cache = False
        self.has_origin = False
        self.has_target = False
        self.is_login = False
        self.iqn = self.image_connections[0]['target_iqn']
        self.multipath_name = 'multipath_' + self.image_name
        self.origin_name = 'origin_' + self.image_name
        self.multipath_path = None
        self.cached_path = None
        self.origin_path = None
        #TODO: all virtual machines called image
        self.peer_id = ''
        self.target_id = 0
        self.__status = STATUS.empty
        self.status_lock = threading.Lock()
        LOG.debug("Virtman: creating a base image of image_name %s" % self.image_name)

    def change_status(self, src_status, dst_status):
        with self.status_lock:
            flag = False
            if self.__status == src_status:
                self.__status = dst_status
                flag = True
            LOG.debug("Virtman: source status = %s, dst status = %s, flag = %s" % (src_status, dst_status, flag))
            return flag

    def adjust_for_heartbeat(self, parents):
        LOG.debug('Virtman: adjust_for_heartbeat according to connections: %s ' % parents)
        parent_connections = utils.reform_connections(parents)
        self.rebuild_multipath(parent_connections)

    def deploy_base_image(self):
        """
        build_chain = Chain()
        build_chain.add_step(lambda: self.rebuild_paths(), lambda: self.destroy_multipath())
        build_chain.add_step(lambda: self.create_cache(), lambda: self.destroy_cache())
        build_chain.add_step(lambda: self.create_origin(), lambda: self.destroy_origin())
        build_chain.add_step(lambda: self.create_target(), lambda: self.destroy_target())
        build_chain.add_step(lambda: self.login_master(), lambda: self.logout_master())
        build_chain.do()
        """
        success = self.change_status(STATUS.empty, STATUS.building)
        if not success:
            while self.__status == STATUS.building:
                LOG.debug("Virtman: in deploy_base_image, sleep 3 seconds waiting for build completed")
                eventlet.sleep(3)
        LOG.debug("Virtman: ..........begin to deploy base image")
        try:
            origin_path = self._deploy_base_image()
        except Exception, e:
            LOG.error(e)
            self.change_status(STATUS.building, STATUS.error)
            raise
        else:
            self.change_status(STATUS.building, STATUS.ok)
        LOG.debug("Virtman: ..........deploy base image completed")
        return origin_path

    def _deploy_base_image(self):
        #TODO: Roll back if failed !
        """
        deploy image in compute node, return the origin path to create snapshot
        :param image_connection: the connection towards to the base image
        :returns: origin path to create snapshot
        """
        LOG.debug("Virtman: in deploy_base_image, image name = %s, has multipath = %s, has origin = %s, has cache = %s, "
                  "is_login = %s" % (self.image_name, self.has_multipath, self.has_origin, self.has_cache, self.is_login))
        #Check if it had origin or not!
        if self.has_origin:
            return self.origin_path
        
        #save the base_image paths
        found = None
        for connection in self.image_connections:
            if connection['target_portal'].find(CONF.host_ip) >= 0:
                found = connection
                break
        if found is not None:
            self.image_connections = [found]
            self.is_local_has_image = True
        LOG.debug("Virtman: my host_ip = %s, is_local_has_image = %s!, now image_connections = %s"
                  % (CONF.host_ip, self.is_local_has_image, self.image_connections))

        #Reform connections
        if self.is_local_has_image:
            parent_connections = []
        else:
            parent_connections = utils.reform_connections(self._get_parent())
        LOG.debug("Virtman: parents for volt is %s" % parent_connections)
        self.rebuild_multipath(parent_connections)
        build_chain = Chain()
        build_chain.add_step(partial(self._create_cache),
                             partial(self._delete_cache))
        build_chain.add_step(partial(self._create_origin),
                             partial(self._delete_origin))
        build_chain.add_step(partial(self._create_target),
                             partial(self._delete_target))
        build_chain.add_step(partial(self._login_master),
                             partial(self._logout_master))
        build_chain.do()

        # self._create_cache()
        # self._create_origin()
        # self._create_target()
        # self._login_master()

        #print "target_id = ", self.target_id
        #print "origin_path = ", self.origin_path, " origin_name = ", self.origin_name
        #print "cached_path = ", self.cached_path, " No name"
        #print "multipath_path = ", self.multipath_path, "multipath_name = ", self.multipath_name
        print "Virtman: baseimage OK!"
        return self.origin_path

    def destroy_base_image(self):
        LOG.debug("Virtman: destroy base_image = %s, peer_id = %s" % (self.image_name, self.peer_id))
        if self.is_local_has_image:
            return False
        self._logout_master()
        if self.has_target:
            if iscsi.is_connected(self.target_id):
                LOG.debug("Virtman: destroy base image Failed! base_image = %s, peer_id = %s" % (self.image_name, self.peer_id))
                return False
            else:
                self._delete_target()
        if self.has_origin:
            self._delete_origin()
        time.sleep(1)
        if not self.has_origin and not self.has_target:
            self._delete_cache()
        if not self.has_cache:
            self._delete_multipath()
        if not self.has_multipath:
            for key in self.paths.keys():
                self.paths[key].disconnect()
                del self.paths[key]
            LOG.debug("Virtman: destroy base image SUCCESS! base_image = %s, peer_id = %s" % (self.image_name, self.peer_id))
            return True
        return False

    def rebuild_multipath(self, parent_connections):
        """
        :param parent_connections: list
        """
        LOG.debug("Virtman: begin to rebuild multipath...")
        #If it has image on the local node or no path to connect, connect to root
        if self.is_local_has_image or len(parent_connections) == 0:
            parent_connections = self.image_connections
            LOG.debug("Virtman: the parents were modified! now parents = %s" % parent_connections)

        #Get keys of paths to remove, and add new paths
        paths_to_remove = []
        for key in self.paths.keys():
            found = False
            for connection in parent_connections:
                if key == connection_to_str(connection):
                    found = True
                    break
            if not found:
                paths_to_remove.append(key)
        for connection in parent_connections:
            if not isinstance(connection, dict):
                raise (Exception("Unknown %s type of %s " % (type(connection), connection)))
            key = connection_to_str(connection)
            if not self.paths.has_key(key):
                self.paths[key] = Path(connection)

        #Connect new paths
        for key in self.paths.keys():
            if key not in paths_to_remove and not self.paths[key].connected:
                self.paths[key].connect()

        #Rebuild multipath device
        disks = [self.paths[key].device_path for key in self.paths.keys()
                 if key not in paths_to_remove and self.paths[key].connected]
        if len(disks) > 0:
            if not self.has_multipath:
                self._create_multipath(disks)
            else:
                self._reload_multipath(disks)
            #TODO:fix here, wait for multipath device ready
            time.sleep(2)

        #Disconnect paths to remove
        for key in paths_to_remove:
            if self.paths[key].connected:
                self.paths[key].disconnect()
            del self.paths[key]

        LOG.debug("Virtman: rebuild multipath completed, multipath = %s" % self.multipath_path)

    def _create_multipath(self, disks):
        if not self.has_multipath:
            self.multipath_path = dmsetup.multipath(self.multipath_name, disks)
            self.has_multipath = True
            LOG.debug("Virtman: create multipath according connection :")
            LOG.debug(disks)
        return self.multipath_path

    def _reload_multipath(self, disks):
        dmsetup.reload_multipath(self.multipath_name, disks)

    def _delete_multipath(self):
        LOG.debug("Virtman: delete multipath %s start!" % self.multipath_name)
        dmsetup.remove_table(self.multipath_name)
        self.has_multipath = False
        LOG.debug("Virtman: delete multipath %s completed  !" % self.multipath_name)

    def _create_cache(self):
        if not self.has_cache:
            LOG.debug("Virtman: create cache for base image %s" % self.image_name)
            LOG.debug("Virtman: create cache according to multipath %s" % self.multipath_path)
            self.cached_path = fcg.add_disk(self.multipath_path)
            self.has_cache = True
            LOG.debug("Virtman: create cache completed, cache path = %s" % self.cached_path)
        return self.cached_path

    def _delete_cache(self):
        LOG.debug("Virtman: start to delete cache according to multipath %s " % self.multipath_path)
        fcg.rm_disk(self.multipath_path)
        self.has_cache = False
        LOG.debug("Virtman: delete cache according to multipath %s completed" % self.multipath_path)

    def _create_origin(self):
        if not self.has_origin:
            LOG.debug("Virtman: start to create origin, cache path = %s" % self.cached_path)
            self.origin_path = dmsetup.origin(self.origin_name, self.cached_path)
            self.has_origin = True
            LOG.debug("Virtman: create origin complete, origin path = %s" % self.origin_path)
        return self.origin_path

    def _delete_origin(self):
        LOG.debug("Virtman: start to remove origin %s " % self.origin_name)
        dmsetup.remove_table(self.origin_name)
        self.has_origin = False
        LOG.debug("Virtman: remove origin %s completed" % self.origin_name)

    def _create_target(self):
        if self.is_local_has_image:
            return
        if not self.has_target:
            LOG.debug("Virtman: start to create target, cache path = %s" % self.cached_path)
            if iscsi.exists(self.iqn):
                self.has_target = True
            else:
                self.target_id = iscsi.create_iscsi_target(self.iqn, self.cached_path)
                self.has_target = True
                LOG.debug("Virtman: create target complete, target id = %s" % self.target_id)

    def _delete_target(self):
        LOG.debug("Virtman: start to remove target %s (%s)" % (self.target_id, self.image_name))
        iscsi.remove_iscsi_target(self.image_name, self.image_name)
        self.has_target = False
        LOG.debug("Virtman: successful remove target %s (%s)" % (self.target_id, self.image_name))

    def _login_master(self):
        if self.is_local_has_image:
            return
        LOG.debug("Virtman: try to login to master server")
        if not self.is_login:
            info = volt.login(session_name=self.image_name, peer_id=self.peer_id,
                              host=CONF.host_ip, port='3260', iqn=self.iqn, lun='1')
            LOG.debug("Virtman: login to master server %s" % info)
            self.is_login = True

    def _logout_master(self):
        if self.is_login:
            volt.logout(self.image_name, peer_id=self.peer_id)
            self.is_login = False
            LOG.debug("Virtman: logout master session = %s, peer_id = %s" % (self.image_name, self.peer_id))

    def _get_parent(self):
        max_try_count = 120
        host_ip = CONF.host_ip
        try_times = 0
        while True:
            try:
                self.peer_id, parent_list = volt.get(session_name=self.image_name, host=host_ip)
                LOG.debug(
                    "Virtman: in get_parent function, peer_id = %s, parent_list = %s:" % (self.peer_id, parent_list))
                if len(parent_list) == 1 and parent_list[0].peer_id is None:
                    raise Exception("parents is in pending")
                return parent_list
            except Exception, e:
                LOG.debug(
                    "Virtman: get parent info from volt server failed due to %s, tried %d times" % (e, try_times))
                if try_times < max_try_count:
                    time.sleep(5)
                    try_times += 1
                    continue
                else:
                    raise Exception("Virtman: Get parent info failed due to %s! " % e)


class Qcow2BaseImage(BaseImage):
    pass
