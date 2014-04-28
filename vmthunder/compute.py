#!/usr/bin/env python
import time
import threading

from vmthunder.drivers import fcg
from vmthunder.session import Session
from vmthunder.image import StackBDImage
from vmthunder.singleton import singleton
from vmthunder.openstack.common import log as logging
from vmthunder.drivers import volt


LOG = logging.getLogger(__name__)


@singleton
class Compute():
    def __init__(self):
        self.sessions = {}
        self.instances = {}
        self.cache_group = fcg.create_group()
        self.rlock = threading.RLock()
        LOG.debug("VMThunder: creating a Compute_node")

    def heartbeat(self):
        with self.rlock:
            self._heartbeat()

    def _heartbeat(self):
        LOG.debug("VMThunder: heartbeat start @ %s" % time.asctime())
        to_delete_sessions = []
        for each_key in self.sessions:
            LOG.debug("VMThunder: session_name = %s, instances in session = " % self.sessions[each_key].volume_name)
            LOG.debug(self.sessions[each_key].vm)
            if not self.sessions[each_key].has_vm():
                if self.sessions[each_key].destroy():
                    to_delete_sessions.append(each_key)

        for key in to_delete_sessions:
            del self.sessions[key]

        info = volt.heartbeat()

        for each_key in self.sessions:
            for session in info:
                if self.sessions[each_key].peer_id == session['peer_id']:
                    self.sessions[each_key].adjust_for_heartbeat(session['parents'])
                    break
        LOG.debug("VMThunder: heartbeat end @ %s" % time.asctime())

    def destroy(self, vm_name):
        with self.rlock:
            self._destroy(vm_name)

    def _destroy(self, vm_name):
        LOG.debug("VMThunder: destroy vm started, vm_name = %s" % (vm_name))
        if self.instances.has_key(vm_name):
            instance = self.instances[vm_name]
            instance.deconfig_volume()
            del self.instances[vm_name]
        LOG.debug("VMThunder: destroy vm completed, vm_name = %s" % vm_name)

    def list(self):
        with self.rlock:
            return self._list()

    def _list(self):
        def build_list_object(instances):
            instance_list = []
            for instance in instances.keys():
                instance_list.append({
                    'vm_name': instances[instance].vm_name,
                })
            self.rlock.release()
        return build_list_object(self.instances)

    def create(self, volume_name, vm_name, image_connection, snapshot_link):
        with self.rlock:
            return self._create(volume_name, vm_name, image_connection, snapshot_link)

    def _create(self, volume_name, vm_name, image_connection, snapshot_link):
        #TODO: roll back if failed
        if vm_name not in self.instances.keys():
            LOG.debug("VMThunder: create vm started, volume_name = %s, vm_name = %s" % (volume_name, vm_name))
            if not self.sessions.has_key(volume_name):
                self.sessions[volume_name] = Session(volume_name)
            session = self.sessions[volume_name]
            self.instances[vm_name] = StackBDImage(session, vm_name, snapshot_link)
            origin_path = session.deploy_image(image_connection)
            LOG.debug("origin is %s" % origin_path)
            self.instances[vm_name].config_volume(origin_path)
            LOG.debug("VMThunder: create vm completed, volume_name = %s, vm_name = %s, snapshot = %s" %
                      (volume_name, vm_name, self.instances[vm_name].snapshot_path))
            return self.instances[vm_name].snapshot_link