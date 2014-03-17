#!/usr/bin/env python

from pydm.dmsetup import Dmsetup
from vmthunder.session import Session
from vmthunder.instance1 import InstanceCommon
from vmthunder.instance2 import InstanceSnapCache

class ComputeNode():
    
    def __init__(self):
        self.dict = {}
        self.instance = Instance1('fcg')
    
    def delete_vm(self, image_id, vm_name, connections, snapshot_dev):
        session = self.dict[image_id]
        self.instance.del_vm(vm_name, snapshot_dev)
        session.destroy(image_id, vm_name, connections)

    def star_vm(self, image_id, vm_name, connections, snapshot_dev):
        if(not self.dict.has_key(image_id)):
            self.dict[image_id] = Session('fcg', image_id)
        session = self.dict[image_id]
        origin_path = session.deploy_image(image_id, vm_name, connections)
        self.instance.star_vm(image_id, vm_name, origin_path, snapshot_dev)
        
    def adjust_structure(self, image_id, delete_connections, add_connections):
        session = self.dict[image_id]
        session.adjust_structure(image_id, delete_connections, add_connections)
