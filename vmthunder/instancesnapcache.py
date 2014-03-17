#!/usr/bin/env python

from libfcg.fcg import FCG
from pydm.dmsetup import Dmsetup
from vmthunder.instance import Instance

class InstanceSnapCache(Instance):
    
    def _create_cache(self, snapshot_dev):
        fcg = FCG(self.fcg_name)
        cached_path = fcg.add_disk(snapshot_dev)
        return cached_path
    
    def _delete_cache(self, snapshot_dev):
        fcg = FCG(self.fcg_name)
        fcg.rm_disk(snapshot_dev)
    
    def _create_snapshot(self, vm_name, origin_path, snapshot_dev):
        cached_path = self._create_cache(snapshot_dev)
        snapshot_name = self._snapshot_name(vm_name)
        snapshot_path = self.dm.snapshot(origin_path, snapshot_name, cached_path)
        return snapshot_path

    def _delete_snapshot(self, vm_name, snapshot_dev):
	snapshot_name = self._snapshot_name(vm_name)
	self.dm.remove_table(snapshot_name)
	self._delete_cache(snapshot_dev)

    def star_vm(self, vm_name, origin_path, snapshot_dev):
        self._create_snapshot(vm_name, origin_path, snapshot_dev)

    def del_vm(self, vm_name, snapshot_dev):
        self.delete_snapshot(vm_name, snapshot_dev)
        
