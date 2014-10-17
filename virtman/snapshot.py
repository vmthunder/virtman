#!/usr/bin/env python

import os
from oslo.config import cfg

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


class Snapshot(object):
    def __init__(self):
        self.snapshot_with_cache = CONF.snapshot_with_cache

    def create_snapshot(self):
        return NotImplementedError()

    def destroy_snapshot(self):
        return NotImplementedError()

    def _create_cache(self, snapshot):
        cached_path = fcg.add_disk(snapshot)
        return cached_path

    def _delete_cache(self, snapshot):
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
        #snapshot_link is a symlink, like /dev/disk/by-path/xxx
        self.snapshot_link = self.device_info['path']
        if not os.path.exists(self.snapshot_link):
            raise Exception("ERROR! Could NOT find snapshot path file %s!" % self.snapshot_link)
        #snapshot_dev: like /dev/sd*, mounted from remote volume, like Cinder Volume
        self.snapshot_dev = os.path.realpath(self.snapshot_link)
        if not os.path.exists(self.snapshot_dev):
            raise Exception("ERROR! Could NOT find snapshot device %s!" % self.snapshot_dev)

        if self.snapshot_with_cache:
            self.snapshot_path = self._create_cache(self.snapshot_dev)
        else:
            self.snapshot_path = self.snapshot_dev
        LOG.debug(
            "Virtman: success! snapshot_path = %s snapshot_link = %s" % (self.snapshot_path, self.snapshot_link))
        return self.snapshot_path, self.snapshot_link

    def destroy_snapshot(self):
        LOG.debug("Virtman: deleting the snapshot for the VM instance")
        if self.snapshot_with_cache:
            self._delete_cache(self.snapshot_dev)
        connector.disconnect_volume(self.connection, self.device_info)
        LOG.debug("Virtman: success!")
        return True


class QCOW2Snapshot(Snapshot):
    pass


class RAWSnapshot(Snapshot):
    pass

