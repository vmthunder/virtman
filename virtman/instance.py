
import os

from virtman.utils import commands
from virtman.drivers import dmsetup
from virtman.snapshot import LocalSnapshot
from virtman.snapshot import BlockDeviceSnapshot

from virtman.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class Instance(object):

    def __init__(self):
        pass


class LocalInstance(Instance):
    def __init__(self, origin_path, instance_name, snapshot_dev):
        self.instance_path = None
        self.instance_name = instance_name
        self.origin_path = origin_path
        self.snapshot = LocalSnapshot(snapshot_dev)
        self.snapshot_name = "snapshot_" + instance_name

    def create(self):
        LOG.debug("Virtman: start VM instance %s according origin_path %s" %(self.instance_name, self.origin_path))
        snapshot_path = self.snapshot.create_snapshot()
        self.instance_path = dmsetup.snapshot(self.origin_path, self.snapshot_name, snapshot_path)
        LOG.debug("Virtman: success! instance_path = %s" % self.instance_path)
        return self.instance_path

    def destroy(self):
        LOG.debug("Virtman: destroy VM instance %s according snapshot_name %s" %(self.instance_name, self.snapshot_name))
        dmsetup.remove_table(self.snapshot_name)
        self.snapshot.destroy_snapshot()
        LOG.debug("Virtman: succeed to destroy the VM instance!")
        return True


class BlockDeviceInstance(Instance):
    """
    Block device instance for OpenStack
    """
    def __init__(self, origin_path, instance_name, snapshot_connection):
        self.instance_path = None
        self.instance_name = instance_name
        self.origin_path = origin_path
        self.snapshot = BlockDeviceSnapshot(snapshot_connection)
        self.snapshot_name = "snapshot_" + instance_name
        self.snapshot_link = None

    def create(self):
        LOG.debug("Virtman: start VM instance %s according origin_path %s" %(self.instance_name, self.origin_path))
        snapshot_path, self.snapshot_link = self.snapshot.create_snapshot()
        self.instance_path = dmsetup.snapshot(self.origin_path, self.snapshot_name, snapshot_path)
        #change link for OpenStack
        commands.unlink(self.snapshot_link)
        if not os.path.exists(self.snapshot_link):
            commands.link(self.instance_path, self.snapshot_link)
        LOG.debug("Virtman: success! snapshot_link = %s" % self.snapshot_link)
        return self.snapshot_link

    def destroy(self):
        LOG.debug("Virtman: destroy VM instance %s according snapshot_name %s" %(self.instance_name, self.snapshot_name))
        #unlink snapshot
        if os.path.exists(self.snapshot_link):
            commands.unlink(self.snapshot_link)
        dmsetup.remove_table(self.snapshot_name)
        self.snapshot.destroy_snapshot()
        LOG.debug("Virtman: success!")
        return True






