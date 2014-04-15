#!/usr/bin/env python
import threading
import thread
import time

from vmthunder.drivers import fcg
from vmthunder.session import Session
from vmthunder.instance import Instance
from vmthunder.singleton import SingleTon
from vmthunder.openstack.common import log as logging
from vmthunder.drivers import volt


LOG = logging.getLogger(__name__)


@SingleTon
class Compute():
    def __init__(self):
        self.sessions = {}
        self.instances = {}
        self.cache_group = fcg.create_group()
        LOG.debug("creating a Compute_node")

    def heartbeat(self):
        info = volt.heartbeat()
        to_delete_session = []
        for each_key in self.sessions:
            for session in info:
                if self.sessions[each_key].peer_id == session['peer_id']:
                    self.sessions[each_key].adjust_for_heartbeat(session['parents'])
                    break
            if not self.sessions[each_key].has_vm():
                if self.sessions[each_key].destroy():
                    to_delete_session.append(each_key)
        for key in to_delete_session:
            del self.sessions[key]

    def destroy(self, vm_name):
        if self.instances.has_key(vm_name):
            instance = self.instances[vm_name]
            #session = self.sessions[instance.volume_name]
            instance.del_vm()
            #session.destroy(vm_name)
            del self.instances[vm_name]

    def list(self):
        def build_list_object(instances):
            instance_list = []
            for instance in instances.keys():
                instance_list.append({
                    'vm_name': instances[instance].vm_name,
                })
            return dict(instances=instance_list)

        return build_list_object(self.instances)

    def create(self, volume_name, vm_name, connections, snapshot_dev):
        if vm_name not in self.instances.keys():
            LOG.debug("in compute to execute the method create")
            if not self.sessions.has_key(volume_name):
                self.sessions[volume_name] = Session(volume_name)
            session = self.sessions[volume_name]
            origin_path = session.deploy_image(connections)
            self.instances[vm_name] = Instance.factory(vm_name, session, snapshot_dev)
            LOG.debug("origin is %s" % origin_path)
            self.instances[vm_name].start_vm(origin_path)
            return self.instances[vm_name].snapshot_path

    def adjust_structure(self, volume_name, delete_connections, add_connections):
        if volume_name in self.sessions.keys():
            session = self.sessions[volume_name]
            session.adjust_structure(delete_connections, add_connections)

