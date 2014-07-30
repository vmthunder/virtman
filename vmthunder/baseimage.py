#!/usr/bin/env python

import eventlet
import time
import socket
import fcntl
import struct
import threading

from oslo.config import cfg

from vmthunder.openstack.common import log as logging
from vmthunder.path import connection_to_str
from vmthunder.path import Path
from vmthunder.enum import Enum
from vmthunder.drivers import fcg
from vmthunder.drivers import dmsetup
from vmthunder.drivers import iscsi
from vmthunder.drivers import volt
from vmthunder.chain import Chain

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
        if not image_name.startswith("image-"):
            image_name = "image-" + image_name
        self.image_name = image_name
        self.image_connections = self.reform_connections(image_connections)
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
        LOG.debug("VMThunder: creating a base image of image_name %s" % self.image_name)

    def change_status(self, src_status, dst_status):
        with self.status_lock:
            flag = False
            if self.__status == src_status:
                self.__status = dst_status
                flag = True
            LOG.debug("VMThunder: source status = %s, dst status = %s, flag = %s" % (src_status, dst_status, flag))
            return flag

    def adjust_for_heartbeat(self, parents):
        LOG.debug('VMThunder: adjust_for_heartbeat according to connections: %s ' % parents)
        self.rebuild_multipath(parents)

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
                LOG.debug("VMThunder: in deploy_base_image, sleep 3 seconds waiting for build completed")
                eventlet.sleep(3)
        LOG.debug("VMThunder: ..........begin to deploy base image")
        try:
            origin_path = self._deploy_base_image()
        except Exception, e:
            LOG.error(e)
            self.change_status(STATUS.building, STATUS.error)
            raise
        else:
            self.change_status(STATUS.building, STATUS.ok)
        LOG.debug("VMThunder: ..........deploy base image completed")
        return origin_path

    def _deploy_base_image(self):
        #TODO: Roll back if failed !
        """
        deploy image in compute node, return the origin path to create snapshot
        :param image_connection: the connection towards to the base image
        :return: origin path to create snapshot
        """
        LOG.debug("VMThunder: in deploy_base_image, image name = %s, has multipath = %s, has origin = %s, has cache = %s, "
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

        #Reform connections
        parent_connections = self.reform_connections(self._get_parent())
        self.rebuild_multipath(parent_connections)
        self._create_cache()
        self._create_origin()
        self._create_target()
        self._login_master()

        print "target_id = ", self.target_id
        print "origin_path = ", self.origin_path, " origin_name = ", self.origin_name
        print "cached_path = ", self.cached_path, " No name"
        print "multipath_path = ", self.multipath_path, "multipath_name = ", self.multipath_name

        return self.origin_path

    def destroy_base_image(self):
        LOG.debug("VMThunder: destroy base_image = %s, peer_id = %s" % (self.image_name, self.peer_id))
        self._logout_master()
        if self.has_target:
            if iscsi.is_connected(self.target_id):
                LOG.debug("VMThunder: destroy base image failed! base_image = %s, peer_id = %s" % (self.image_name, self.peer_id))
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
            LOG.debug("VMThunder: destroy base image success! base_image = %s, peer_id = %s" % (self.image_name, self.peer_id))
            return True
        return False

    def rebuild_multipath(self, parent_connections):
        """
        :param parent_connections: list
        """
        LOG.debug("VMThunder: begin to rebuild multipath...")
        #If it has image on the local node or no path to connect, connect to root
        if self.is_local_has_image or len(parent_connections) == 0:
            parent_connections = self.image_connections

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

        LOG.debug("VMThunder: rebuild multipath completed, multipath = %s" % self.multipath_path)

    def _create_multipath(self, disks):
        if not self.has_multipath:
            self.multipath_path = dmsetup.multipath(self.multipath_name, disks)
            self.has_multipath = True
            LOG.debug("VMThunder: create multipath according connection :")
            LOG.debug(disks)
        return self.multipath_path

    def _reload_multipath(self, disks):
        dmsetup.reload_multipath(self.multipath_name, disks)

    def _delete_multipath(self):
        dmsetup.remove_table(self.multipath_name)
        self.has_multipath = False
        LOG.debug("VMThunder: delete multipath of %s" % self.multipath_name)

    def _create_cache(self):
        if not self.has_cache:
            LOG.debug("VMThunder: create cache for base image %s" % self.image_name)
            LOG.debug("VMThunder: create cache according to multipath %s" % self.multipath_path)
            self.cached_path = fcg.add_disk(self.multipath_path)
            self.has_cache = True
            LOG.debug("VMThunder: create cache completed, cache path = %s" % self.cached_path)
        return self.cached_path

    def _delete_cache(self):
        fcg.rm_disk(self.multipath_path)
        self.has_cache = False
        LOG.debug("VMThunder: delete cache according to multipath %s " % self.multipath_path)

    def _create_origin(self):
        if not self.has_origin:
            LOG.debug("VMThunder: start to create origin, cache path = %s" % self.cached_path)
            self.origin_path = dmsetup.origin(self.origin_name, self.cached_path)
            self.has_origin = True
            LOG.debug("VMThunder: create origin complete, origin path = %s" % self.origin_path)
        return self.origin_path

    def _delete_origin(self):
        dmsetup.remove_table(self.origin_name)
        self.has_origin = False
        LOG.debug("VMThunder: remove origin %s " % self.origin_name)

    def _create_target(self):
        if self.is_local_has_image:
            return
        if not self.has_target:
            LOG.debug("VMThunder: start to create target, cache path = %s" % self.cached_path)
            if iscsi.exists(self.iqn):
                self.has_target = True
            else:
                self.target_id = iscsi.create_iscsi_target(self.iqn, self.cached_path)
                self.has_target = True
                LOG.debug("VMThunder: create target complete, target id = %s" % self.target_id)

    def _delete_target(self):
        iscsi.remove_iscsi_target(0, 0, self.image_name, self.image_name)
        self.has_target = False
        LOG.debug("VMThunder: successful remove target %s " % self.target_id)

    def _login_master(self):
        if self.is_local_has_image:
            return
        LOG.debug("VMThunder: try to login to master server")
        if not self.is_login:
            info = volt.login(session_name=self.image_name, peer_id=self.peer_id,
                              host=CONF.host_ip, port='3260', iqn=self.iqn, lun='1')
            LOG.debug("VMThunder: login to master server %s" % info)
            self.is_login = True

    def _logout_master(self):
        if self.is_login:
            volt.logout(self.image_name, peer_id=self.peer_id)
            self.is_login = False
            LOG.debug("VMThunder: logout master session = %s, peer_id = %s" % (self.image_name, self.peer_id))

    def _get_parent(self):
        max_try_count = 10
        host_ip = CONF.host_ip
        try_times = 0
        while True:
            try:
                self.peer_id, parent_list = volt.get(session_name=self.image_name, host=host_ip)
                LOG.debug(
                    "VMThunder: in get_parent function, peer_id = %s, parent_list = %s:" % (self.peer_id, parent_list))
                return parent_list
            except Exception, e:
                LOG.debug(
                    "VMThunder: get parent info from volt server failed due to %s, tried %d times" % (e, try_times))
                if try_times < max_try_count:
                    time.sleep(3)
                    try_times += 1
                    continue
                else:
                    raise Exception("VMThunder: Get parent info failed due to %s! " % e)

    @staticmethod
    def reform_connection(connection):
        """
        :return new_connection: a list includes 'target_portal', 'target_iqn' and 'target_lun'.
        """
        LOG.debug("old connection is :")
        LOG.debug(connection)
        if isinstance(connection, dict):
            new_connection = {'target_portal': connection['target_portal'],
                              'target_iqn': connection['target_iqn'],
                              'target_lun': connection['target_lun'],
            }
        else:
            new_connection = {
                'target_portal': "%s:%s" % (connection.host, connection.port),
                'target_iqn': connection.iqn,
                'target_lun': connection.lun,
            }
        LOG.debug("new connection is :")
        LOG.debug(new_connection)
        return new_connection

    def reform_connections(self, connections):
        """
        :param connections: a tuple or list
        """
        if not (isinstance(connections, list) or isinstance(connections, tuple)):
            raise Exception('VMThunder: Unknown connections type: connection: {0:s}, type: {1:s}'.format(
                connections, type(connections)))
        new_connections = []
        for connection in connections:
            new_connections.append(self.reform_connection(connection))
        return new_connections

    @staticmethod
    def _get_ip_address(ifname):
        LOG.debug("acquire ip address of %s" % ifname)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack('256s', ifname[:15]))[20:24])


class Qcow2BaseImage(BaseImage):
    pass
