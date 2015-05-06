
import os
from oslo.config import cfg

from virtman.utils import commands
from virtman.drivers import dmsetup
from virtman import blockservice
from virtman.drivers import connector
from virtman.drivers import fcg

from virtman.openstack.common import log as logging

snapshot_opts = [
    cfg.BoolOpt('snapshot_with_cache',
                default=False,
                help='Whether snapshot can have cache'),
]
CONF = cfg.CONF
CONF.register_opts(snapshot_opts)

LOG = logging.getLogger(__name__)


class Instance(object):

    def __init__(self):
        pass

    def create(self):
        return NotImplementedError()

    def destroy(self):
        return NotImplementedError()

    @staticmethod
    def _create_cache(snapshot):
        cached_path = fcg.add_disk(snapshot)
        return cached_path

    @staticmethod
    def _delete_cache(snapshot):
        fcg.rm_disk(snapshot)
        return True


class LocalInstance(Instance):
    def __init__(self, origin_path, instance_name, snapshot_dev=None):
        super(LocalInstance, self).__init__()
        self.instance_path = None
        self.instance_name = instance_name
        self.origin_path = origin_path
        self.snapshot_with_cache = CONF.snapshot_with_cache
        self.snapshot_dev = snapshot_dev
        self.snapshot_name = "snapshot_" + instance_name

    def create(self):
        LOG.debug("Virtman: start VM instance %s according origin_path %s" %
                  (self.instance_name, self.origin_path))
        snapshot_path = self._create_snap_dev()
        self.instance_path = dmsetup.snapshot(self.origin_path,
                                              self.snapshot_name, snapshot_path)
        LOG.debug("Virtman: success! instance_path = %s" % self.instance_path)
        return self.instance_path

    def _create_snap_dev(self):
        LOG.debug("Virtman: creating a snapshot for the VM instance")
        if self.snapshot_dev is None:
            self.snapshot_dev = blockservice.findloop()
        blockservice.try_linkloop(self.snapshot_dev)
        if self.snapshot_with_cache:
            snapshot_path = self._create_cache(self.snapshot_dev)
        else:
            snapshot_path = self.snapshot_dev
        LOG.debug("Virtman: success! snapshot_path = %s" % snapshot_path)
        return snapshot_path

    def destroy(self):
        LOG.debug("Virtman: destroy VM instance %s according "
                  "snapshot_name %s" % (self.instance_name, self.snapshot_name))
        dmsetup.remove_table(self.snapshot_name)
        self._destroy_snap_dev()
        LOG.debug("Virtman: succeed to destroy the VM instance!")
        return True

    def _destroy_snap_dev(self):
        LOG.debug("Virtman: deleting the snapshot for the VM instance")
        if self.snapshot_with_cache:
            self._delete_cache(self.snapshot_dev)
        blockservice.unlinkloop(self.snapshot_dev)
        LOG.debug("Virtman: succeed to delete snapshot!")
        return True


class BlockDeviceInstance(Instance):
    """
    Block device instance for OpenStack
    """
    def __init__(self, origin_path, instance_name, snapshot_connection):
        super(BlockDeviceInstance, self).__init__()
        self.instance_path = None
        self.instance_name = instance_name
        self.origin_path = origin_path
        self.snapshot_with_cache = CONF.snapshot_with_cache
        self.snapshot_connection = snapshot_connection
        self.snapshot_dev = None
        self.snapshot_name = "snapshot_" + instance_name
        self.device_info = None
        self.snapshot_link = None

    def create(self):
        LOG.debug("Virtman: start VM instance %s according origin_path %s" %
                  (self.instance_name, self.origin_path))
        snapshot_path, self.snapshot_link = self._create_snap_dev()
        self.instance_path = dmsetup.snapshot(self.origin_path,
                                              self.snapshot_name,
                                              snapshot_path)
        # change link for OpenStack
        commands.unlink(self.snapshot_link)
        if not os.path.exists(self.snapshot_link):
            commands.link(self.instance_path, self.snapshot_link)
        LOG.debug("Virtman: success! snapshot_link = %s" % self.snapshot_link)
        return self.snapshot_link

    def _create_snap_dev(self):
        LOG.debug("Virtman: creating a snapshot for the VM instance")
        self.device_info = connector.connect_volume(self.snapshot_connection)
        # snapshot_link is a symlink, like /dev/disk/by-path/xxx
        self.snapshot_link = self.device_info['path']
        if not os.path.exists(self.snapshot_link):
            raise Exception("ERROR! Could NOT find snapshot path file %s!" %
                            self.snapshot_link)
        # snapshot_dev: like /dev/sd*, mounted from remote volume,
        # like Cinder Volume
        self.snapshot_dev = os.path.realpath(self.snapshot_link)
        if not os.path.exists(self.snapshot_dev):
            raise Exception("ERROR! Could NOT find snapshot device %s!" %
                            self.snapshot_dev)

        if self.snapshot_with_cache:
            snapshot_path = self._create_cache(self.snapshot_dev)
        else:
            snapshot_path = self.snapshot_dev
        LOG.debug("Virtman: success! snapshot_path = %s snapshot_link = %s" %
                  (snapshot_path, self.snapshot_link))
        return snapshot_path, self.snapshot_link

    def destroy(self):
        LOG.debug("Virtman: destroy VM instance %s according "
                  "snapshot_name %s" % (self.instance_name, self.snapshot_name))
        # unlink snapshot
        if os.path.exists(self.snapshot_link):
            commands.unlink(self.snapshot_link)
        dmsetup.remove_table(self.snapshot_name)
        self._destroy_snap_dev()
        LOG.debug("Virtman: success!")
        return True

    def _destroy_snap_dev(self):
        LOG.debug("Virtman: deleting the snapshot for the VM instance")
        if self.snapshot_with_cache:
            self._delete_cache(self.snapshot_dev)
        connector.disconnect_volume(self.snapshot_connection, self.device_info)
        LOG.debug("Virtman: succeed to delete snapshot!")
        return True


class Snapshot(object):
    def __init__(self):
        self.snapshot_with_cache = CONF.snapshot_with_cache

    def create_snapshot(self):
        return NotImplementedError()

    def destroy_snapshot(self):
        return NotImplementedError()

    @staticmethod
    def _create_cache(snapshot):
        cached_path = fcg.add_disk(snapshot)
        return cached_path

    @staticmethod
    def _delete_cache(snapshot):
        fcg.rm_disk(snapshot)
        return True


class LocalSnapshot(Snapshot):
    def __init__(self, snapshot_dev=None):
        super(LocalSnapshot, self).__init__()
        self.snapshot_path = None
        self.snapshot_dev = snapshot_dev

    def create_snapshot(self):
        LOG.debug("Virtman: creating a snapshot for the VM instance")
        if self.snapshot_dev is None:
            self.snapshot_dev = blockservice.findloop()
        blockservice.try_linkloop(self.snapshot_dev)
        if self.snapshot_with_cache:
            self.snapshot_path = self._create_cache(self.snapshot_dev)
        else:
            self.snapshot_path = self.snapshot_dev
        LOG.debug("Virtman: success! snapshot_path = %s" % self.snapshot_path)
        return self.snapshot_path

    def destroy_snapshot(self):
        LOG.debug("Virtman: deleting the snapshot for the VM instance")
        if self.snapshot_with_cache:
            self._delete_cache(self.snapshot_dev)
        blockservice.unlinkloop(self.snapshot_dev)
        LOG.debug("Virtman: succeed to delete snapshot!")
        return True


class BlockDeviceSnapshot(Snapshot):
    def __init__(self, snapshot_connection):
        super(BlockDeviceSnapshot, self).__init__()
        self.snapshot_path = None
        self.snapshot_link = None
        self.snapshot_dev = None
        self.connection = snapshot_connection
        self.device_info = None

    def create_snapshot(self):
        LOG.debug("Virtman: creating a snapshot for the VM instance")
        self.device_info = connector.connect_volume(self.connection)
        # snapshot_link is a symlink, like /dev/disk/by-path/xxx
        self.snapshot_link = self.device_info['path']
        if not os.path.exists(self.snapshot_link):
            raise Exception("ERROR! Could NOT find snapshot path file %s!" %
                            self.snapshot_link)
        # snapshot_dev: like /dev/sd*, mounted from remote volume,
        # like Cinder Volume
        self.snapshot_dev = os.path.realpath(self.snapshot_link)
        if not os.path.exists(self.snapshot_dev):
            raise Exception("ERROR! Could NOT find snapshot device %s!" %
                            self.snapshot_dev)

        if self.snapshot_with_cache:
            self.snapshot_path = self._create_cache(self.snapshot_dev)
        else:
            self.snapshot_path = self.snapshot_dev
        LOG.debug("Virtman: success! snapshot_path = %s snapshot_link = %s" %
                  (self.snapshot_path, self.snapshot_link))
        return self.snapshot_path, self.snapshot_link

    def destroy_snapshot(self):
        LOG.debug("Virtman: deleting the snapshot for the VM instance")
        if self.snapshot_with_cache:
            self._delete_cache(self.snapshot_dev)
        connector.disconnect_volume(self.connection, self.device_info)
        LOG.debug("Virtman: succeed to delete snapshot!")
        return True

