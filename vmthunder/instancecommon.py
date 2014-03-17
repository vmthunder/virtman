#!/usr/bin/env python

from pydm.dmsetup import Dmsetup
from vmthunder.instance import Instance

class InstanceCommon(Instance):
    
    def _create_snapshot(self, vm_name, origin_path, snapshot_dev):
        snapshot_name = self._snapshot_name(vm_name)
        snapshot_path = self.dm.snapshot(origin_path, snapshot_name, snapshot_dev)
        return snapshot_path

    def _delete_snapshot(self, vm_name):
	snapshot_name = self._snapshot_name(vm_name)
	self.dm.remove_table(snapshot_name)

    def star_vm(self, image_id, vm_name, origin_path, snapshot_dev):
        self._create_snapshot(vm_name, origin_path, snapshot_dev)

    def del_vm(self, vm_name):
        self._delete_snapshot(vm_name)
