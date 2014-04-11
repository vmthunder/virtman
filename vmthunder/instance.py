#!/usr/bin/env python

import time
import os

from oslo.config import cfg
from libfcg.fcg import FCG
from pydm.dmsetup import Dmsetup
from vmthunder.openstack.common import log as logging

instance_opts = [
    cfg.StrOpt('instance_type',
               default='common',
               help='Instance snapshot type'),
]
CONF = cfg.CONF
CONF.register_opts(instance_opts)

LOG = logging.getLogger(__name__)


class Instance():
    def __init__(self, fcg_name, volume_name, vm_name, snapshot_dev):
        #TODO: Get fcg name from CONF, remove the arg from init
        self.dm = Dmsetup()
        self.fcg_name = fcg_name
        self.vm_name = vm_name
        self.snapshot_dev = snapshot_dev
        self.volume_name = volume_name
        self.snapshot_path = ''

        LOG.debug("creating a instance of name %s " % self.vm_name)

    @staticmethod
    def factory(fcg_name, volume_name, vm_name, snapshot_dev):
        from vmthunder.instancecommon import InstanceCommon
        from vmthunder.instancesnapcache import InstanceSnapCache
        if CONF.instance_type == 'common':
            return InstanceCommon(fcg_name, volume_name, vm_name, snapshot_dev)
        elif CONF.instance_type == 'snapcache':
            return InstanceSnapCache(fcg_name, volume_name, vm_name, snapshot_dev)
        else:
            msg = "Instance type %s not found" % CONF.instance_type
            LOG.error(msg)
            raise ValueError(msg)

    def _snapshot_name(self):
        return 'snapshot_' + self.vm_name
    
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
        return self.dm.mapdev_prefix + snapshot_name


    
    
	
	
