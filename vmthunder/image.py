#!/usr/bin/env python

import os

from oslo.config import cfg

#try:
#    from brick.openstack.common import log as logging
#except ImportError:
from vmthunder.openstack.common import log as logging
from vmthunder.drivers import dmsetup
from vmthunder.drivers import connector
from vmthunder.drivers import fcg

instance_opts = [
    cfg.BoolOpt('snapshot_with_cache',
                default=False,
                help='Whether snapshot can have cache'),
]
CONF = cfg.CONF
CONF.register_opts(instance_opts)

LOG = logging.getLogger(__name__)

iscsi_disk_format = "ip-%s-iscsi-%s-lun-%s"


class Image(object):
    def __init__(self, session, name):
        self._final_path = ''

    def config_volume(self, location):
        """ configure the instance's private delta volume, location is
            the place where the instance's delta volume is or should be
            placed. The delta volume is created on-demand.

            returns the path to access the final volume
        """
        return NotImplementedError()

    def deconfig_volume(self):
        """ close the instance's private delta volume
        """
        return NotImplementedError()

    def get_volume_path(self):
        """ returns the path to access the final volume
        """
        return self._final_path


class BDImage(Image):
    """
    Block device image
    """
    def __init__(self, session, name, snapshot_dev):
        super(BDImage, self).__init__(session, name)
        self.vm_name = name
        self.snapshot_dev = snapshot_dev
        self.session = session
        self.snapshot_with_cache = CONF.snapshot_with_cache

    @property
    def snapshot_name(self):
        return 'snapshot_' + self.vm_name

    @property
    def snapshot_path(self):
        return dmsetup.prefix + self.snapshot_name

    def config_volume(self, origin_path):
        LOG.debug("VMThunder: start vm %s according origin_path %s" % (self.vm_name, origin_path))
        self._create_snapshot(origin_path)
        self.session.add_vm(self.vm_name)
        return self.vm_name

    def deconfig_volume(self):
        LOG.debug("VMThunder: come to instanceSnapCache to delete vm %s" % self.vm_name)
        self._delete_snapshot()
        self.session.rm_vm(self.vm_name)

    def _create_cache(self):
        cached_path = fcg.add_disk(self.snapshot_dev)
        return cached_path

    def _delete_cache(self):
        fcg.rm_disk(self.snapshot_dev)

    def _create_snapshot(self, origin_path):
        if self.snapshot_with_cache:
            snap_path = self._create_cache()
        else:
            snap_path = self.snapshot_dev
        snapshot_name = self.snapshot_name
        snapshot_path = dmsetup.snapshot(origin_path, snapshot_name, snap_path)
        self._final_path = snapshot_path
        return snapshot_path

    def _delete_snapshot(self):
        snapshot_name = self.snapshot_name
        dmsetup.remove_table(snapshot_name)
        if self.snapshot_with_cache:
            self._delete_cache()


class StackBDImage(BDImage):
    """
    Block device image suite for OpenStack
    """
    def __init__(self, session, name, snapshot_connection):
        self.connection = snapshot_connection
        snapshot_info = connector.connect_volume(snapshot_connection)
        snapshot_link = snapshot_info['path']
        if os.path.exists(snapshot_link):
            self.snapshot_link = snapshot_link
        else:
            raise Exception("Could NOT find snapshot link file %s!" % snapshot_link)

        snapshot_dev = os.path.realpath(self.snapshot_link)
        if os.path.exists(snapshot_dev) or snapshot_dev == snapshot_link:
            super(StackBDImage, self).__init__(session, name, snapshot_dev)
        else:
            raise Exception("Could NOT find snapshot device %s!" % snapshot_dev)

    def config_volume(self, origin_path):
        super(StackBDImage, self).config_volume(origin_path)
        self.link_snapshot()

    def deconfig_volume(self):
        super(StackBDImage, self).deconfig_volume()
        self.unlink_snapshot()

    def link_snapshot(self):
        target_dev = self.snapshot_link
        os.unlink(target_dev)
        if not os.path.exists(target_dev):
            os.symlink(self._final_path, target_dev)

    def unlink_snapshot(self):
        target_dev = self.snapshot_link
        if os.path.exists(target_dev):
            os.unlink(target_dev)