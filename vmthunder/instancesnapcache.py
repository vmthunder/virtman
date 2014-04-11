#!/usr/bin/env python

from vmthunder.drivers import fcg
from vmthunder.drivers import dmsetup
from vmthunder.instance import Instance
from vmthunder.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class InstanceSnapCache(Instance):
    
    def _create_cache(self):
        cached_path = fcg.add_disk(self.snapshot_dev)
        return cached_path
    
    def _delete_cache(self):
        fcg.rm_disk(self.snapshot_dev)
    
    def _create_snapshot(self, origin_path):
        cached_path = self._create_cache()
        snapshot_name = self._snapshot_name()
        snapshot_path = dmsetup.snapshot(origin_path, snapshot_name, cached_path)
        self.snapshot_path = snapshot_path
        return snapshot_path

    def _delete_snapshot(self):
        snapshot_name = self._snapshot_name()
        dmsetup.remove_table(snapshot_name)
        self._delete_cache()

    def start_vm(self, origin_path):
        LOG.debug("instanceSnapCache start vm according origin_path %s" % origin_path)
        self._create_snapshot(origin_path)
        return self.vm_name

    def del_vm(self):
        LOG.debug("come to instanceSnapCache to delete vm %s" % self.vm_name)
        self._delete_snapshot()
        return self.vm_name