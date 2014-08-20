#!/usr/bin/env python

import os
from oslo.config import cfg

from vmthunder.drivers import connector
from vmthunder.drivers import fcg

from vmthunder.openstack.common import log as logging


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

    def __init__(self, snapshot_dev):
        super(LocalSnapshot, self).__init__()
        if not os.path.exists(snapshot_dev):
            raise Exception("ERROR! Could NOT find snapshot device %s!" % snapshot_dev)
        self.snapshot_path = None
        self.snapshot_dev = snapshot_dev

    def create_snapshot(self):
        if self.snapshot_with_cache:
            self.snapshot_path = self._create_cache(self.snapshot_dev)
        else:
            self.snapshot_path = self.snapshot_dev
        return self.snapshot_path

    def destroy_snapshot(self):
        if self.snapshot_with_cache:
            self._delete_cache(self.snapshot_dev)


class BlockDeviceSnapshot(Snapshot):

    def __init__(self, snapshot_connection):
        super(BlockDeviceSnapshot, self).__init__()
        self.snapshot_path = None
        self.snapshot_link = None
        self.snapshot_dev = None
        self.connection = snapshot_connection
        self.device_info = None

    def create_snapshot(self):
        LOG.debug("VMThunder: creating a snapshot for the VM instance")
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

        return self.snapshot_path, self.snapshot_link

    def destroy_snapshot(self):
        LOG.debug("VMThunder: deleting the snapshot for the VM instance")
        if self.snapshot_with_cache:
            self._delete_cache(self.snapshot_dev)
        connector.disconnect_volume(self.connection, self.device_info)
        return True


class QCOW2Snapshot(Snapshot):
    pass


class RAWSnapshot(Snapshot):
    pass

