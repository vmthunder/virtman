#!/usr/bin/env python

import libfcg.fcg
from vmthunder.session import Session
from vmthunder.instancecommon import InstanceCommon
from vmthunder.instancesnapcache import InstanceSnapCache
from vmthunder.singleton import get_instance
from vmthunder.singleton import SingleTon

class Compute(SingleTon):
    def __init__(self, fcg_name, ssds, blocksize, pattern):
        self.session_dict = {}
        self.instance_dict = {}
        self.fcg_name = fcg_name
        fcg = FCG(fcg_name)
        fcg.create_group(ssds, blocksize, pattern)
    
    def delete_vm(self, vm_name, connections):
        instance = self.instance_dict[vm_name]
        session = self.session_dict[instance.image_id]
        instance.del_vm()
        session.destroy(vm_name, connections)
        del self.instance_dict[vm_name]

    def start_vm(self, image_id, vm_name, connections, snapshot_dev):
        if(not self.session_dict.has_key(image_id)):
            self.session_dict[image_id] = Session('fcg', image_id)
        session = self.session_dict[image_id]
        origin_path = session.deploy_image(vm_name, connections)
        self.instance_dict[vm_name] = InstanceSnapCache('fcg', image_id, vm_name, snapshot_dev)
        self.instance_dict[vm_name].start_vm(origin_path)
        
    def adjust_structure(self, image_id, delete_connections, add_connections):
        session = self.session_dict[image_id]
        session.adjust_structure(delete_connections, add_connections)

def get_compute(*args, **kv):
        return get_instance(Compute, *args, **kv)
