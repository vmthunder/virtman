#!/usr/bin/env python

import time
import os

from libfcg.fcg import FCG
from pydm.dmsetup import Dmsetup

class Instance():
    def __init__(self, fcg_name):
        self.dm = Dmsetup()
        self.fcg_name = fcg_name
    
    def _snapshot_name(self, vm_name):
        return 'snapshot_' + vm_name
    
    def connect_snapshot(self, connection):
        """Connect snapshot volume in cinder server
        """
        return NotImplementedError()
    
    def _snapshot_path(self, vm_name):
        snapshot_name = self._snapshot_name(vm_name)
        return self.dm.mapdev_prefix + snapshot_name


    
    
	
	
