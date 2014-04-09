#!/usr/bin/env python

import time
import os

from libfcg.fcg import FCG
from pydm.dmsetup import Dmsetup
from brick.openstack.common import log as logging

LOG = logging.getLogger(__name__)

class Instance():
    def __init__(self, fcg_name, volume_name, vm_name, snapshot_dev):

        self.dm = Dmsetup()
        self.fcg_name = fcg_name
        self.vm_name = vm_name
        self.snapshot_dev = snapshot_dev
        self.volume_name = volume_name

        #self.log_filename = "log_file"
        #self.log_format = '%(filename)s [%(asctime)s] [%(levelname)s] %(message)s'
        #logging.basicConfig(filename = self.log_filename, filemode='a',format = self.log_format, datefmt = '%Y-%m-%d %H:%M:%S %p',level = logging.DEBUG)
        LOG.debug("creating a instance of name  ",self.vm_name)
    
    def _snapshot_name(self):
        return 'snapshot_' + self.vm_name
    
    def connect_snapshot(self, connection):
        """Connect snapshot volume in cinder server
        """
        return NotImplementedError()
    
    def _snapshot_path(self):
        snapshot_name = self._snapshot_name()
        return self.dm.mapdev_prefix + snapshot_name


    
    
	
	
