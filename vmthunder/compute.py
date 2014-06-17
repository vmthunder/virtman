#!/usr/bin/env python
import time
import os
import sys
import threading
import traceback

from oslo.config import cfg

from vmthunder.openstack.common import log as logging

from vmthunder.drivers import fcg
from vmthunder.session import Session
from vmthunder.image import StackBDImage
from vmthunder.image import BDImage
from vmthunder.singleton import singleton
from vmthunder.drivers import volt

host_opts = [
    cfg.StrOpt('host_ip',
               default='10.107.11.120',
               help='localhost ip provide VMThunder service'),
    cfg.StrOpt('host_port',
               default='8001',
               help='localhost port to provide VMThunder service'),
    cfg.IntOpt('heartbeat_interval',
               default=20,
               help='localhost heartbeat interval'),
]

compute_opts = [
    cfg.IntOpt('thread_pool_size',
               default=100,
               help='The count of work threads'),
]
CONF = cfg.CONF
CONF.register_opts(compute_opts)
CONF.register_opts(host_opts)

logging.setup('vmthunder')

LOG = logging.getLogger(__name__)


@singleton
class Compute():
    def __init__(self, openstack_compatible=True):
        LOG.info("VMThunder: start to create a VMThunder Compute_node")
        self.openstack_compatible = openstack_compatible
        self.sessions = {}
        self.instances = {}
        if not fcg.is_valid():
            fcg.create_group()
        if self.openstack_compatible:
            config_files = ['/etc/nova/nova.conf', '/etc/vmthunder/vmthunder.conf']
        else:
            config_files = ['/etc/vmthunder/vmthunder.conf']
        CONF(sys.argv[1:], project='vmthunder', default_config_files=config_files)

        self.heartbeat_event = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_clock)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        LOG.info("VMThunder: create a VMThunder Compute_node completed")

    def __del__(self):
        self.heartbeat_event.set()

    def heartbeat_clock(self):
        while not self.heartbeat_event.wait(CONF.heartbeat_interval):
            try:
                self.heartbeat()
            except Exception, e:
                LOG.error("VMThudner: heartbeat failed due to %s" % e)
                LOG.error("VMThunder: traceback is : %s" % traceback.print_exc())
        LOG.debug("VMThunder: stop heartbeat timer")

    def heartbeat(self):
        LOG.debug("VMThunder: heartbeat start @ %s" % time.asctime())
        to_delete_sessions = []
        for each_key in self.sessions:
            LOG.debug("VMThunder: session_name = %s, instances in session = %s" %
                      (self.sessions[each_key].volume_name, self.sessions[each_key].vm))
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
        LOG.debug("VMThunder: destroy vm started, vm_name = %s" % (vm_name))
        if self.instances.has_key(vm_name):
            instance = self.instances[vm_name]
            instance.deconfig_volume()
            del self.instances[vm_name]
        LOG.debug("VMThunder: destroy vm completed, vm_name = %s" % vm_name)

    def list(self):
        def build_list_object(instances):
            instance_list = []
            for instance in instances.keys():
                instance_list.append({
                    'vm_name': instances[instance].vm_name,
                })

        return build_list_object(self.instances)

    def create(self, volume_name, vm_name, image_connection, snapshot):
        #TODO: roll back if failed
        LOG.debug("VMThunder: -----PID = %s" % os.getpid())
        if vm_name not in self.instances.keys():
            LOG.debug("VMThunder: create vm started, volume_name = %s, vm_name = %s" % (volume_name, vm_name))
            if not self.sessions.has_key(volume_name):
                self.sessions[volume_name] = Session(volume_name)
            session = self.sessions[volume_name]
            if self.openstack_compatible:
                self.instances[vm_name] = StackBDImage(session, vm_name, snapshot)
            else:
                self.instances[vm_name] = BDImage(session, vm_name, snapshot)
            origin_path = session.deploy_image(image_connection)
            LOG.debug("origin is %s" % origin_path)
            self.instances[vm_name].config_volume(origin_path)
            LOG.debug("VMThunder: create vm completed, volume_name = %s, vm_name = %s, snapshot = %s" %
                      (volume_name, vm_name, self.instances[vm_name].snapshot_path))
            return self.instances[vm_name].snapshot_link