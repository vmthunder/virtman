#!/usr/bin/env python

import time
import os

from libfcg.fcg import FCG
from pydm.dmsetup import Dmsetup
from brick.initiator.connector import ISCSIConnector
from brick.iscsi.iscsi import TgtAdm


class Session():
    def __init__(self, fcg_name ,image_id ):
        self.fcg_name = fcg_name
        self.iscsi = ISCSIConnector('')
        self.tgt = TgtAdm('', '/etc/tgt/conf.d')
        self.dm = Dmsetup()
        self.image_id = image_id
        self.connections = []
        self.target_path_dict = {}
        self.multipath = 0
        self.cache = 0
        self.origin = 0
        self.target = 0
        self.vm = []
        
    def change_connection(self, connection):
        return connection[target_portal] + connection[target_iqn]
    
    def add_target_path_dict(self, connection, path):
        key = self.change_connection(connection)
        self.target_path_dict[key] = path

    def _origin_name(self, image_id):
        return 'origin_' + image_id

    def _multipath_name(self, image_id):
        return 'multipath_' + image_id

    def _multipath(self, image_id):
        multipath_name = self._multipath_name(image_id)
        multipath = self.dm.mapdev_prefix + multipath_name
        return multipath
    
    def _image_path(self, image_id):
        multipath_name = self._multipath_name(image_id)
        image_path = self.dm.mapdev_prefix + multipath_name
        return image_path

    def _cached_path(self, image_path):
        fcg = FCG(self.fcg_name)
        cached_disk_name = self.fcg._cached_disk_name(image_path)
        return self.dm.mapdev_prefix + cached_disk_name

    def _origin_path(self, image_id):
        origin_name = self._origin_name(image_id)
        return self.dm.mapdev_prefix + origin_name

    def connection_exits(self, connection):
        for conn in self.connections:
            if(conn == connection):
                return 1
        return 0

    #This method is to login target and return the connected_paths
    def login_target(self, connections):
        """connection_properties for iSCSI must include:
        target_portal - ip and optional port
        target_iqn - iSCSI Qualified Name
        target_lun - LUN id of the volume
        """ 
        connected_paths = []
        
        for connection in connections:
            if(not self.connection_exits(connection)):
                self.connections.append(connection)
                device_info = self.iscsi.connect_volume(connection)
                path = device_info['path']
                path = os.path.realpath(path)
                self.add_target_path_dict(connection, path)
                connected_paths.append(path)
        return connected_paths
    
    def logout_target(self, connection):
        """ parameter device_info is no be used """
        self.iscsi.disconnect_volume(connection, '')
        self.connections.remove(connection)
        key = self.change_connection(connection)
        del self.target_path_dict[key]
    
    def connect_image(self, connection):
        """Connect image volume in cinder server
        """
        return NotImplementedError()

    def create_target(self, iqn, path):
        self.tgt.create_iscsi_target(iqn, path)
        self.target = 1
        
    def delete_target(self, image_id):
        try:
            self.tgt.remove_iscsi_target(0, 0, image_id, image_id)
            self.target=0
        except  Exception, e:
            print e
  
    def create_multipath(self, image_id, disks):
        multipath_name = self._multipath_name(image_id)
        multipath_path = self.dm.multipath(multipath_name, disks)
        self.multipath = 1
        return multipath_path
   
    def delete_multipath(self, image_id):
        multipath_name = self._multipath_name(image_id) 
        self.dm.remove_table(multipath_name)
        self.multipath = 0

    def create_cache(self, image_path):
        fcg = FCG(self.fcg_name)
        cached_path = fcg.add_disk(image_path)
        self.cache = 1
        return cached_path

    def delete_cache(self, image_path):
        fcg = FCG(self.fcg_name)
        fcg.rm_disk(image_path)
        self.cache = 0
        
    def create_origin(self, image_id, origin_dev):
        origin_name = self._origin_name(image_id)
        origin_path = ''
        if self.dm.is_exist(origin_name):
            origin_path = self._origin_path(image_id)
        else:
            origin_path = self.dm.origin(origin_name, origin_dev)
            self.origin = 1
        return origin_path
   
    def delete_origin(self, image_id):
	origin_name = self._origin_name(image_id)
	self.dm.remove_table(origin_name)
        self.origin = 0
    
    def deploy_image(self, image_id, vm_name, connections):
        #TODO: Roll back if failed !
        self.vm.append(vm_name)
        connected_path = self.login_target(connections)
        assert connected_path != '', 'No image has been connected !'
        multipath_name = self._multipath_name(image_id)
        multipath  = self._multipath(image_id)
        cached_path = ''
        if  self.multipath:
            fcg = FCG(self.fcg_name)
            cached_disk_name = fcg._cached_disk_name(multipath)
            cached_path = self.dm.mapdev_prefix + cached_disk_name
            self.add_path(image_id)
        else:
            image_path = self.create_multipath(image_id, connected_path)
            cached_path = self.create_cache(image_path)
            connection = connections[0]
            iqn = connection['target_iqn']
            self.create_target(iqn, cached_path)
        origin_path = self.create_origin(image_id, cached_path)
        return origin_path

    def destroy(self, image_id, vm_name, connections):
        vm.remove(vm_name)
        fcg = FCG(self.fcg_name)
        multipath_name = self._multipath_name(image_id)
        image_path = self._image_path(image_id)
        if(len(self.vm) == 0):
            self.delete_origin(image_id)
        self.delete_target(image_id)
        if(self.origin == 0):
            self.delete_cache(image_path)
        if(self.cache == 0):
            self.delete_multipath(image_id)
        for connection in connections:
            self.logout_target(connection)
        add_path(image_id)
    
    def add_path(self, image_id):
        if(len(self.connections) == 0):
            return 
        multipath_name = self._multipath_name(image_id)
        size = utils.get_dev_sector_count(self.target_path_dict[self.connections[0]])
        multipath_table = '0 %d multipath 0 0 1 1 queue-length 0 %d 1 ' % (size, len(self.connections))
        for connection in self.connections:
            multipath_table += self.target_path_dict[connection]+' 128 '
        multipath_table += '\n'
        print 'multipath_table = %s' % multipath_table
        self.dm.reload_table(multipath_name, multipath_table)
        
    def adjust_structurt(self, image_id, delete_connections, add_connections):
        for connection in delete_connections:
            if(self.connection_exits(connection)):
                self.logout_target(connection)
        self.login_target(add_connections)
        add_path(image_id)
                
                
                
        
           

    
    
