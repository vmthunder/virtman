#!/usr/bin/env python

import time
import os

from libfcg.fcg import FCG
from pydm.dmsetup import Dmsetup
from brick.initiator.connector import ISCSIConnector
from brick.iscsi.iscsi import TgtAdm
from vmthunder.instance import Instance
from vmthunder.session import Session
class ComputeNode():
    def __init__(self):
        self.dict = {}
        self.instance = Instance()
    
    def delete_vm(self, image_id, vm_name, connections, snapshot_dev):
        session = self.dict[image_id]
        self.instance.delete_snapshot(vm_name)
        session.destroy(image_id, vm_name, connections)

    def star_vm(self, image_id, vm_name, connections, snapshot_dev):
        if(not self.dict.has_key(image_id)):
            self.dict[image_id] = Session('fcg', image_id)
        session = self.dict[image_id]
        origin_path = session.deploy_image(image_id, vm_name, connections)
        self.instance.star_vm(image_id, vm_name, origin_path, snapshot_dev)
        
    def adjust_structurt(self, image_id, delete_connections, add_connections):
        session = self.dict[image_id]
        session.adjust_structure(image_id, delete_connections, add_connections)
