#!/usr/bin/env python

from pydm.dmsetup import Dmsetup
from vmthunder.instance import Instance
from brick.openstack.common import log as logging

LOG = logging.getLogger(__name__)

class InstanceCommon(Instance):
    
    def _create_snapshot(self, origin_path):
        snapshot_name = self._snapshot_name()
        snapshot_path = self.dm.snapshot(origin_path, snapshot_name, self.snapshot_dev)
        return snapshot_path

    def _delete_snapshot(self):
    	snapshot_name = self._snapshot_name()
        self.dm.remove_table(snapshot_name)

    def start_vm(self, origin_path):
        LOG.debug("instanceCommon start vm according origin_path %s" % origin_path)
        self._create_snapshot(origin_path)
        return self.vm_name

    def del_vm(self):
        LOG.debug("come to instanceSnapCache to delete vm %s" % self.vm_name)
        self._delete_snapshot()
        return self.vm_name