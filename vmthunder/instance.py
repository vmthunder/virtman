#!/usr/bin/env python

import time
import os

from libfcg.fcg import FCG
from pydm.dmsetup import Dmsetup
from brick.initiator.connector import ISCSIConnector
from brick.iscsi.iscsi import TgtAdm

class Instance():
    def __init__(self):
        self.dm = Dmsetup()
        
    def _snapshot_name(self, vm_name):
        return 'snapshot_' + vm_name
    
    def connect_snapshot(self, connection):
        """Connect snapshot volume in cinder server
        """
        return NotImplementedError()
    def _snapshot_path(self, vm_name):
        snapshot_name = self._snapshot_name(vm_name)
        return self.dm.mapdev_prefix + snapshot_name
    
    def create_snapshot(self, image_id, vm_name, origin_path, snapshot_dev):
        snapshot_name = self._snapshot_name(vm_name)
        snapshot_path = self.dm.snapshot(origin_path, snapshot_name, snapshot_dev)
        return snapshot_path

    def delete_snapshot(self, vm_name):
	snapshot_name = self._snapshot_name(vm_name)
	self.dm.remove_table(snapshot_name)

    def star_vm(self, image_id, vm_name, origin_path, snapshot_dev):
        self.create_snapshot(image_id, vm_name, origin_path, snapshot_dev)
        
	
	
