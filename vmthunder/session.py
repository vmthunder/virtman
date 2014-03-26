#!/usr/bin/env python

import time
import os

from pydm.common import utils
from libfcg.fcg import FCG
from pydm.dmsetup import Dmsetup
from brick.initiator.connector import ISCSIConnector
from brick.iscsi.iscsi import TgtAdm


class Session():
    def __init__(self, fcg_name , volume_name):
        self.fcg_name = fcg_name
        self.fcg = FCG(fcg_name)
        self.iscsi = ISCSIConnector('')
        self.tgt = TgtAdm('', '/etc/tgt/conf.d')
        self.dm = Dmsetup()
        self.volume_name = volume_name
        self.connections = []
        self.target_path_dict = {}
        self.has_multipath = False
        self.has_cache = False
        self.has_origin = False
        self.has_target = False
        self.vm = []
        
    def _connection_to_string(self, connection):
        return connection['target_portal'] + connection['target_iqn']
    
    def _add_target_path_dict(self, connection, path):
        key = self._connection_to_string(connection)
        self.target_path_dict[key] = path

    def _delete_target_path_dict(self, connection):
        key = self._connection_to_string(connection)
        if(self.target_path_dict.has_key(key)):
            del self.target_path_dict[key]

    def _origin_name(self):
        return 'origin_' + self.volume_name

    def _multipath_name(self):
        return 'multipath_' + self.volume_name

    def _multipath(self):
        multipath_name = self._multipath_name()
        multipath = self.dm.mapdev_prefix + multipath_name
        return multipath
    
    def _cached_path(self, image_path):
        cached_disk_name = self.fcg._cached_disk_name(image_path)
        return self.dm.mapdev_prefix + cached_disk_name

    def _origin_path(self):
        origin_name = self._origin_name()
        return self.dm.mapdev_prefix + origin_name

    def _connection_exits(self, connection):
        if connection in self.connections:
            return True
        else:
            return False

    #This method is to login target and return the connected_paths
    def _login_target(self, connections):
        """connection_properties for iSCSI must include:
        target_portal - ip and optional port
        target_iqn - iSCSI Qualified Name
        target_lun - LUN id of the volume_name
        """ 
        connected_paths = []
        print "path to login_target"        
        print self.connections

        for connection in connections:
            if(self._connection_exits(connection) is False):
                try:
                    print "------ iscsi connect volume_name"
                    device_info = self.iscsi.connect_volume(connection)
                    path = device_info['path']
                    path = os.path.realpath(path)
                    self._add_target_path_dict(connection, path)
                    connected_paths.append(path)
                    self.connections.append(connection)
                except Exception, e:
                    print e
        return connected_paths
    
    def _logout_target(self, connection):
        """ parameter device_info is no be used """
        tmp_string = self._connection_to_string(connection)
        if(self.target_path_dict.has_key(tmp_string)):
            try:
                self.iscsi.disconnect_volume(connection, '')
                self._delete_target_path_dict(connection)
            except Exception, e:
                print e

    def connect_image(self, connection):
        """Connect image volume_name in cinder server
        """
        return NotImplementedError()

    def _create_target(self, iqn, path):
        try:
            self.tgt.create_iscsi_target(iqn, path)
            self.has_target = True
        except Exception, e:
            print e
        
    def _delete_target(self):
        try:
            self.tgt.remove_iscsi_target(0, 0, self.volume_name, self.volume_name)
            self.has_target = False
        except  Exception, e:
            print e
  
    def _create_multipath(self, disks):
        multipath_name = self._multipath_name()
        try:
            multipath_path = self.dm.multipath(multipath_name, disks)
            self.has_multipath = True
        except Exception, e:
            print e
        return multipath_path
   
    def _delete_multipath(self):
        multipath_name = self._multipath_name()
        try:
            self.dm.remove_table(multipath_name)
            self.has_multipath = False
        except Exception, e:
            print e
    
    def _create_cache(self, multipath):
        try:
            cached_path = self.fcg.add_disk(multipath)
            self.has_cache = True
        except Exception, e:
            print e
        return cached_path

    def _delete_cache(self, multipath):
        try:
            self.fcg.rm_disk(multipath)
            self.has_cache = False
        except Exception, e:
            print e
    
    def _create_origin(self, origin_dev):
        origin_name = self._origin_name()
        origin_path = ''
        if self.has_origin:
            origin_path = self._origin_path()
        else:
            try:
                origin_path = self.dm.origin(origin_name, origin_dev)
                self.has_origin = True
            except Exception, e:
                print e
        return origin_path
   
    def _delete_origin(self):
        origin_name = self._origin_name()
        try:
            self.dm.remove_table(origin_name)
            self.has_origin = False
        except Exception, e:
                print e
    
    def deploy_image(self, vm_name, connections):
        #TODO: Roll back if failed !
        if vm_name not in self.vm:
            self.vm.append(vm_name)
        connected_path = self._login_target(connections)
        print "end"
        multipath_name = self._multipath_name()
        multipath  = self._multipath()
        cached_path = ''
        if  self.has_multipath:
            cached_disk_name = self.fcg._cached_disk_name(multipath)
            cached_path = self.dm.mapdev_prefix + cached_disk_name
            self._add_path()
        else:
            multi_path = self._create_multipath(connected_path)
            cached_path = self._create_cache(multi_path)
            connection = connections[0]
            iqn = connection['target_iqn']
            self._create_target(iqn, cached_path)
        origin_path = self._create_origin(cached_path)
        return origin_path
    def destroy(self, vm_name):
        self.vm.remove(vm_name)

    def Destroy_for_adjust_structure(self):
        multipath = self._multipath()
        if(len(self.vm) == 0):
            self._delete_origin()
        if(self.has_target):
            self._delete_target()
        time.sleep(1)
        if(self.has_origin is False and self.has_target is False):
            self._delete_cache(multipath)
        if(self.has_cache is False):
            self._delete_multipath()
    
    def _add_path(self):
        if(len(self.connections) == 0):
            return 
        multipath_name = self._multipath_name()
        key = self._connection_to_string(self.connections[0])
        size = utils.get_dev_sector_count(self.target_path_dict[key])
        multipath_table = '0 %d multipath 0 0 1 1 queue-length 0 %d 1 ' % (size, len(self.connections))
        for connection in self.connections:
                temp = self._connection_to_string(connection)
                multipath_table += self.target_path_dict[temp]+' 128 '
        multipath_table += '\n'
        print 'multipath_table = %s' % multipath_table
        self.dm.reload_table(multipath_name, multipath_table)
        
    def adjust_structure(self, delete_connections, add_connections):
        self._login_target(add_connections)
        for connection in delete_connections:
            if(self._connection_exits(connection)):
                self.connections.remove(connection)
        self._add_path()
        for connection in delete_connections:
            self._logout_target(connection)
        self.Destroy_for_adjust_structure()
                
                
        
           

    
    
