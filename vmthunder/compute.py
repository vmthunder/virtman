#!/usr/bin/env python
import logging

from libfcg.fcg import FCG
from vmthunder.session import Session
from vmthunder.instancesnapcache import InstanceSnapCache
from vmthunder.singleton import SingleTon

@SingleTon
class Compute():
    def __init__(self, fcg_name='fcg', ssds="ssds", blocksize="blo", pattern="pat"):
        self.session_dict = {}
        self.instance_dict = {}
        self.fcg_name = fcg_name
        fcg = FCG(fcg_name)
        fcg.create_group(ssds, blocksize, pattern)
        self.log_filename = "log_file"
        self.log_format = '%(filename)s [%(asctime)s] [%(levelname)s] %(message)s'
        logging.basicConfig(filename = self.log_filename, filemode='a',format = self.log_format, datefmt = '%Y-%m-%d %H:%M:%S %p',level = logging.DEBUG)
        logging.debug("creating a Compute_node of name ")


    def list(self):
        def build_list_object(instances):
            instance_list = []
            for instance in instances.keys():
                instance_list.append({
                    'vm_name':instances[instance].vm_name,
                    })
            return { 'instances': instance_list}
        return build_list_object(self.instance_dict)

    def destroy(self, vm_name):
        if self.instance_dict.has_key(vm_name):
            instance = self.instance_dict[vm_name]
            session = self.session_dict[instance.volume_name]
            instance.del_vm()
            session.destroy(vm_name)
            del self.instance_dict[vm_name]

    def create(self, volume_name, vm_name, connections, snapshot_dev):
        if not self.instance_dict.has_key(vm_name):
            print "------- create a example "
            if(not self.session_dict.has_key(volume_name)):
                self.session_dict[volume_name] = Session('fcg', volume_name)
            session = self.session_dict[volume_name]
            origin_path = session.deploy_image(vm_name, connections)
            self.instance_dict[vm_name] = InstanceSnapCache('fcg', volume_name, vm_name, snapshot_dev)
            print '--------- ' + origin_path
            self.instance_dict[vm_name].start_vm(origin_path)

    def adjust_structure(self, volume_name, delete_connections, add_connections):
        if self.session_dict.has_key(volume_name):
            session = self.session_dict[volume_name]
            session.adjust_structure(delete_connections, add_connections)

