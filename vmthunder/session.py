#!/usr/bin/env python

import time
import socket
import fcntl
import struct
import threading

from oslo.config import cfg

from vmthunder.openstack.common import log as logging
from vmthunder.path import connection_to_str
from vmthunder.path import Path
from vmthunder.drivers import fcg
from vmthunder.drivers import dmsetup
from vmthunder.drivers import iscsi
from vmthunder.drivers import volt

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Enum(set):
    def __getattr__(self, item):
        if item in self:
            return item
        return AttributeError

STATUS = Enum(['empty', 'building', 'ok', 'destroying', 'error'])
ACTIONS = Enum(['build', 'destroy'])


class Session(object):
    def __init__(self, volume_name):
        self.volume_name = volume_name
        self.root = {}
        self.paths = {}
        self.cached_path = ''
        self.has_multipath = False
        self.has_cache = False
        self.has_origin = False
        self.has_target = False
        self.is_login = False
        #TODO: all virtual machines called instance
        self.vm = []
        self.peer_id = ''
        self.target_id = 0
        self.__status = STATUS.empty
        self.status_lock = threading.Lock()
        LOG.debug("VMThunder: create a session of volume_name %s" % self.volume_name)

    @property
    def origin_name(self):
        return 'origin_' + self.volume_name

    @property
    def origin_path(self):
        return dmsetup.prefix + self.origin_name

    @property
    def multipath_name(self):
        return 'multipath_' + self.volume_name

    @property
    def multipath_path(self):
        return dmsetup.prefix + self.multipath_name

    #@synchronized("status_lock")
    def change_status(self, src_status, dst_status):
        with self.status_lock:
            ret = False
            if self.__status == src_status:
                self.__status = dst_status
                ret = True
            LOG.debug("VMThunder: source status = %s, dst status = %s, ret = %s" % (src_status, dst_status, ret))
            return ret

    def deploy_image(self, image_connection):
        success = self.change_status(STATUS.empty, STATUS.building)
        if not success:
            while self.__status == STATUS.building:
                LOG.debug("VMThunder: in deploy_image, sleep 3 seconds waiting for build completed")
                time.sleep(3)
        try:
            origin_path = self._deploy_image(image_connection)
        except Exception, e:
            LOG.error(e)
            self.change_status(STATUS.building, STATUS.error)
            raise
        else:
            self.change_status(STATUS.building, STATUS.ok)
        return origin_path

    def _deploy_image(self, image_connection):
        #TODO: Roll back if failed !
        """
        deploy image in compute node, return the origin path to create snapshot
        :param image_connection: the connection towards to the base image
        :return: origin path to create snapshot
        """
        LOG.debug("VMThunder: in deploy_image, volume name = %s, has origin = %s, is_login = %s" %
                  (self.volume_name, self.has_origin, self.is_login))

        #Check current status

        if self.has_origin:
            return self.origin_path

        image_path = Path(self.reform_connection(image_connection))
        self.root[str(image_path)] = image_path

        if len(self.paths) == 0:
            parent_list = self._get_parent()
            self.rebuild_paths(parent_list)

        if not self.has_cache:
            self.cached_path = self._create_cache(self.multipath_path)

        if not self.has_origin:
            self._create_origin(self.cached_path)

        if not self.has_target:
            iqn = image_connection['target_iqn']
            self._create_target(iqn, self.cached_path)
        #TODO: A potential bug here, what happen if a error happened, threads are waiting for build ok.
        return self.origin_path

    def destroy(self):
        LOG.debug("VMThunder: destroy session %s" % self.volume_name)
        assert not self.has_vm(), 'Destroy session %s failed, still has vm' % self.volume_name
        if self.is_login is True:
            volt.logout(self.volume_name, peer_id=self.peer_id)
            self.is_login = False
        if self.has_target:
            if iscsi.is_connected(self.target_id):
                return False
            else:
                self._delete_target()

        if self.has_origin:
            self._delete_origin()
        time.sleep(1)
        multipath = self.multipath_path
        if not self.has_origin and not self.has_target:
            self._delete_cache(multipath)
        if not self.has_cache:
            self._delete_multipath()
        if not self.has_multipath:
            for key in self.paths.keys():
                self.paths[key].disconnect()
                del self.paths[key]
        return True

    def adjust_for_heartbeat(self, parent_list):
        self.rebuild_paths(parent_list)
        LOG.debug('VMThunder: adjust_for_heartbeat according to connections:')
        LOG.debug(parent_list)

    def has_vm(self):
        if len(self.vm) > 0:
            return True
        else:
            return False

    def add_vm(self, vm_name):
        if vm_name not in self.vm:
            self.vm.append(vm_name)
        else:
            LOG.error("Add vm failed, VM %s existed" % vm_name)

    def rm_vm(self, vm_name):
        try:
            self.vm.remove(vm_name)
        except ValueError:
            LOG.error("remove vm failed. VM %s does not existed" % vm_name)

    def rebuild_paths(self, parents_list):
        #Reform connections
        parent_connections = self.reform_connections(parents_list)
        #Get keys of paths to remove
        keys_to_remove = []
        for key in self.paths.keys():
            found = False
            for connection in parent_connections:
                if str(self.paths[key]) == connection_to_str(connection):
                    found = True
                    break
            if not found:
                keys_to_remove.append(key)
        #If no path to connect, connect to root
        if len(parents_list) == 0:
            self.paths = self.root
        #Add paths to self.paths
        else:
            for parent in parent_connections:
                if isinstance(parent, dict):
                    parent_str = connection_to_str(parent)
                    if parent_str not in self.paths.keys():
                        self.paths[parent_str] = Path(parent)
                elif isinstance(parent, Path):
                    if str(parent) not in self.paths.keys():
                        self.paths[str(parent)] = parent
                else:
                    raise(Exception("Unknown %s type of %s "%(type(parent), parent)))
        #Connect new paths
        print type(self.paths)
        for key in self.paths.keys():
            if key not in keys_to_remove and not self.paths[key].connected:
                self.paths[key].connect()
        #Rebuild multipath device
        disks = [self.paths[key].device_path for key in self.paths
                 if key not in keys_to_remove and self.paths[key].connected]
        if self.has_multipath:
            self._reload_multipath(disks)
        else:
            self._create_multipath(disks)

        #Disconnect path to remove
        for key in keys_to_remove:
            if self.paths[key].connected:
                self.paths[key].disconnect()
            del self.paths[key]

    @staticmethod
    def _get_ip_address(ifname):
        LOG.debug("acquire ip address of %s" % ifname)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack('256s', ifname[:15]))[20:24])

    @staticmethod
    def reform_connection(connection):
        LOG.debug("old connection is :")
        LOG.debug(connection)
        new_connection = {'target_portal': connection['target_portal'],
                          'target_iqn': connection['target_iqn'],
                          'target_lun': connection['target_lun'],
        }
        LOG.debug("new connection is :")
        LOG.debug(new_connection)
        return new_connection

    def reform_connections(self, connections):
        new_connections = []
        for connection in connections:
            new_connections.append(self.reform_connection(connection))
        return new_connections

    def _create_target(self, iqn, path):
        if iscsi.exists(iqn) is False:
            self.target_id = iscsi.create_iscsi_target(iqn, path)
            LOG.debug("VMThunder: create a target and it's id is %s" % self.target_id)
            self.has_target = True
        #don't dynamic gain host_id and host_port
        #TODO: eth0? br100?
        host_ip = self._get_ip_address('br100')
        LOG.debug("VMThunder: try to login to master server")
        #TODO: port? lun? what is info
        if not self.is_login:
            info = volt.login(session_name=self.volume_name, peer_id=self.peer_id,
                              host=host_ip, port='3260', iqn=iqn, lun='1')
            LOG.debug("VMThunder: login to master server %s" % info)
            self.is_login = True

    def _delete_target(self):
        iscsi.remove_iscsi_target(0, 0, self.volume_name, self.volume_name)
        self.has_target = False
        LOG.debug("successful remove target %s " % self.target_id)

    def _create_multipath(self, disks):
        multipath_name = self.multipath_name
        multipath_path = dmsetup.multipath(multipath_name, disks)
        self.has_multipath = True
        LOG.debug("create multipath according connection :")
        LOG.debug(disks)
        return multipath_path

    def _delete_multipath(self):
        multipath_name = self.multipath_name
        dmsetup.remove_table(multipath_name)
        self.has_multipath = False
        LOG.debug("delete multipath of %s" % multipath_name)

    def _reload_multipath(self, disks):
        dmsetup.reload_multipath(self.multipath_name, disks)

    def _create_cache(self, multipath):
        cached_path = fcg.add_disk(multipath)
        self.has_cache = True
        LOG.debug("VMThunder: create cache according to multipath %s" % multipath)
        return cached_path

    def _delete_cache(self, multipath):
        fcg.rm_disk(multipath)
        self.has_cache = False
        LOG.debug("VMThunder: delete cache according to multipath %s " % multipath)

    def _create_origin(self, origin_dev):
        origin_name = self.origin_name
        if self.has_origin:
            origin_path = self.origin_path
        else:
            origin_path = dmsetup.origin(origin_name, origin_dev)
            LOG.debug("VMThunder: create origin on %s" % origin_dev)
            self.has_origin = True
        return origin_path

    def _delete_origin(self):
        origin_name = self.origin_name
        dmsetup.remove_table(origin_name)
        LOG.debug("VMThunder: remove origin %s " % origin_name)
        self.has_origin = False

    def _get_parent(self):
        #TODO: br100???
        host_ip = self._get_ip_address('br100')
        while True:
            self.peer_id, parent_list = volt.get(session_name=self.volume_name, host=host_ip)
            LOG.debug("VMThunder: in get_parent function to get parent_list :")
            LOG.debug(parent_list)
            #Wait for parents are ready
            bo = True
            for parent in parent_list:
                if parent.status == "pending":
                    bo = False
                    break
            if bo:
                return parent_list
            #TODO: sleep???
            time.sleep(1)