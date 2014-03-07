#!/usr/bin/env python

import time
import os

from libfcg.fcg import FCG
from pydm.dmsetup import Dmsetup
from brick.initiator.connector import ISCSIConnector
from brick.iscsi.iscsi import TgtAdm

class ComputeNode():
    def __init__(self, fcg_name='fcg'):
        self.fcg_name = fcg_name
        self.iscsi = ISCSIConnector('')
        self.tgt = TgtAdm('', '/etc/tgt/conf.d')
    
    def _origin_name(self, image_id):
        return 'origin_' + image_id

    def _snapshot_name(self, vm_name):
        return 'snapshot_' + vm_name

    def _multipath_name(self, image_id):
        return 'multipath_' + image_id
        
    def connect_image_paths(self, image_id, connections):
        """Attach the paths of image

        connection_properties for iSCSI must include:
        target_portal - ip and optional port
        target_iqn - iSCSI Qualified Name
        target_lun - LUN id of the volume
        """
        image_path = ''
        connected_paths = []
        for connection in connections:
            device_info = self.iscsi.connect_volume(connection)
            path = device_info['path']
            path = os.path.realpath(path)
            connected_paths.append(path)
        path_count = len(connected_paths)
        if path_count == 0:
            #TODO: No available path, connect image storage server directly
            raise(Exception('No available path, connect image storage server directly !')) 
        else:
            image_path = self.create_multipath(image_id, connected_paths)
        return image_path

    def connect_image(self, connection):
        """Connect image volume in cinder server
        """
        return NotImplementedError()

    def connect_snapshot(self, connection):
        """Connect snapshot volume in cinder server
        """
        return NotImplementedError()

    def create_target(self, iqn, path):
        self.tgt.create_iscsi_target(iqn, path)

    def delete_target(self, image_id):
        try:
		    self.tgt.remove_iscsi_target(0, 0, image_id, image_id)
        except Exception, e:
            print e
            raise(Exception('delete target failed!'))

    def create_multipath(self, image_id, disks):
        dm = Dmsetup()
        multipath_name = self._multipath_name(image_id)
        multipath_path = dm.multipath(multipath_name, disks)
        return multipath_path
   
    def delete_multipath(self, image_id):
        dm = Dmsetup()
        multipath_name = self._multipath_name(image_id) 
        dm.remove_table(multipath_name)

    def logout_target(self, connection):
        """ parameter device_info is no be used """
        self.iscsi.disconnect_volume(connection, '')

    def create_cache(self, image_path):
        fcg = FCG(self.fcg_name)
        cached_path = fcg.add_disk(image_path)
        return cached_path

    def delete_cache(self, image_path):
        fcg = FCG(self.fcg_name)
        fcg.rm_disk(image_path)
        
    def create_snapshot(self, image_id, vm_name, origin_dev, snapshot_dev):
        dm = Dmsetup()
        origin_name = self._origin_name(image_id)
        origin_path = ''
        if dm.is_exist(origin_name):
            origin_path = dm.mapdev_prefix + origin_name
        else:
            origin_path = dm.origin(origin_name, origin_dev)
        snapshot_name = self._snapshot_name(vm_name)
        snapshot_path = dm.snapshot(origin_path, snapshot_name, snapshot_dev)
        return snapshot_path

    def delete_snapshot(self, vm_name):
		dm = Dmsetup()
		snapshot_name = self._snapshot_name(vm_name)
		dm.remove_table(snapshot_name)
   
    def delete_origin(self, image_id):
		dm = Dmsetup()
		origin_name = self._origin_name(image_id)
		dm.remove_table(origin_name)
    
    def launch_vms(self, image_id, vms):
        #TODO: Call 
        #TODO: Call fetch_connections 
        #TODO: If no path available, connect image storage directly
        #TODO: If more than one path available, call deplaoy image
        return NotImplementedError()
        

    def fetch_connections(self, image_id):
        """Fetch the image connections from master
        """
        #TODO: Get connection form master
        #TODO Check the connections here !
        return NotImplementedError()

    def deploy_image(self, image_id, connections):
        #TODO: Roll back if failed !
        image_path = self.connect_image_paths(image_id, connections)
        assert image_path != '', 'No image has been connected !'
        cached_path = self.create_cache(image_path)
        connection = connections[0]
        iqn = connection['target_iqn']
        self.create_target(iqn, cached_path)
        return cached_path
    
    def destroy(self, image_id, vm_name, connections, snapshot_dev):
        mapdev_prefix = '/dev/mapper/'
        fcg = FCG(self.fcg_name)
        multipath_name = self._multipath_name(image_id)
        image_path = mapdev_prefix + multipath_name
        try:
            self.delete_snapshot(vm_name)
        except Exception, e:
            print e
            return
        try:
            self.delete_origin(image_id)
        except Exception, e:
            print e
            return
        try:
            self.delete_target(image_id)
        except Exception, e:
            print e
            return
        try:
            self.delete_cache(image_path)
        except Exception, e:
            print e
            return
        try:
            self.delete_multipath(image_id)
        except Exception, e:
            print e
            return
        time.sleep(1)
        for connection in connections:
            try:
                self.logout_target(connection)
            except Exception, e:
                print e
 
    def fake_code(self, image_id, vm_name, connections, snapshot_dev):
        #For TEST purpose only !
        cached_path = self.deploy_image(image_id, connections)
        self.create_snapshot(image_id, vm_name, cached_path, snapshot_dev)
