#!/usr/bin/env python

from vmthunder.instance import Instance
from vmthunder.openstack.common import log as logging
from vmthunder.drivers import dmsetup

LOG = logging.getLogger(__name__)


class InstanceCommon(Instance):
    def _create_snapshot(self, origin_path):
        snapshot_name = self._snapshot_name()
        snapshot_path = dmsetup.snapshot(origin_path, snapshot_name, self.snapshot_dev)
        self.snapshot_path = snapshot_path
        return snapshot_path

    def _delete_snapshot(self):
        snapshot_name = self._snapshot_name()
        dmsetup.remove_table(snapshot_name)

    def start_vm(self, origin_path):
        LOG.debug("instanceCommon start vm according origin_path %s" % origin_path)
        self._create_snapshot(origin_path)
        self.link_snapshot()
        self.session.add_vm(self.vm_name)
        return self.vm_name

    def del_vm(self):
        LOG.debug("come to instanceSnapCache to delete vm %s" % self.vm_name)
        self._delete_snapshot()
        self.unlink_snapshot()
        self.session.rm_vm(self.vm_name)
        return self.vm_name