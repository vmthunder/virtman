#!/usr/bin/env python

import time
import os

from oslo.config import cfg

from vmthunder.openstack.common import log as logging
from vmthunder.drivers import dmsetup

instance_opts = [
    cfg.StrOpt('instance_type',
               default='common',
               help='Instance snapshot type'),
]
CONF = cfg.CONF
CONF.register_opts(instance_opts)

LOG = logging.getLogger(__name__)

iscsi_disk_format = "ip-%s-iscsi-%s-lun-%s"


class Instance():
    def __init__(self, vm_name, session, snapshot_dev):
        self.vm_name = vm_name
        self.snapshot_dev = snapshot_dev
        self.session = session
        self.volume_name = session.volume_name
        self.snapshot_path = ''
        self.has_link = False

        LOG.debug("creating a instance of name %s " % self.vm_name)

    @staticmethod
    def factory(volume_name, vm_name, snapshot_dev):
        from vmthunder.instancecommon import InstanceCommon
        from vmthunder.instancesnapcache import InstanceSnapCache
        if CONF.instance_type == 'common':
            return InstanceCommon(volume_name, vm_name, snapshot_dev)
        elif CONF.instance_type == 'snapcache':
            return InstanceSnapCache( volume_name, vm_name, snapshot_dev)
        else:
            msg = "Instance type %s not found" % CONF.instance_type
            LOG.error(msg)
            raise ValueError(msg)

    def _snapshot_name(self):
        return 'snapshot_' + self.vm_name

    def link_snapshot(self):
        #TODO: 0 is a problem!!!
        root = self.session.root[0]
        target_dev = iscsi_disk_format % (root['target_portal'], root['target_iqn'], root['target_lun'])
        if not os.path.exists(target_dev):
            os.symlink(self.snapshot_path, target_dev)

    def unlink_snapshot(self):
        #TODO: 0 is a problem!!!
        root = self.session.root[0]
        target_dev = iscsi_disk_format % (root['target_portal'], root['target_iqn'], root['target_lun'])
        if os.path.exists(target_dev):
            os.unlink(target_dev)

    def connect_snapshot(self, connection):
        """Connect snapshot volume in cinder server
        """
        return NotImplementedError()

    def start_vm(self, origin_path):
        return NotImplementedError()

    def del_vm(self):
        return NotImplementedError()
    
    def _snapshot_path(self):
        snapshot_name = self._snapshot_name()
        return dmsetup.prefix + snapshot_name