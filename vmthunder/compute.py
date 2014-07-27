#!/usr/bin/env python

import time
import os
import sys
import threading
import traceback
from oslo.config import cfg

from vmthunder.image import LocalImage
from vmthunder.image import BlockDeviceImage
from vmthunder.singleton import singleton
from vmthunder.drivers import fcg
from vmthunder.drivers import volt

from vmthunder.openstack.common import log as logging

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

class Compute(object):

    def __init__(self):
        return NotImplementedError()

    def create(self, vm_name, image_name,image_connection, snapshot):
        return NotImplementedError()

    def destroy(self, vm_name):
        return NotImplementedError()


@singleton
class VMThunderCompute(Compute):
    def __init__(self, openstack_compatible=True):
        LOG.info("VMThunder: start to create a VMThunder Compute_node")
        self.openstack_compatible = openstack_compatible
        self.images = {}
        self.vm_names = {}
        self.lock = threading.Lock()
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
        with self.lock:
            self._heartbeat()

    def _heartbeat(self):
        LOG.debug("VMThunder: heartbeat start @ %s" % time.asctime())
        for name in self.images.keys():
            if not self.images[name].has_instance:
                if self.images[name].destroy_image():
                    del self.images[name]

        info = volt.heartbeat()

        for name in self.images.keys():
            for image in info:
                if self.images[name].peer_id == image['peer_id']:
                    self.images[name].adjust_for_heartbeat(image['parents'])
                    break
        LOG.debug("VMThunder: heartbeat end @ %s" % time.asctime())

    def create(self, vm_name, image_name, image_connections, snapshot):
        """
        :param vm_name: string
        :param image_name: string
        :param image_connections: list or tuple or single dict, like ({},..) or [{},..] or {}
                                  and each dict make of {'target_portal':..,'target_iqn':..,'target_lun':.., ..}
        :param snapshot: snapshot_connection or snapshot_dev
        """
        with self.lock:
            if self.vm_names.has_key(vm_name):
                LOG.debug("VMThunder: the vm_name \'%s\' already exists!" % (vm_name))
                return
            else:
                self.vm_names[vm_name] = image_name
            if not self.images.has_key(image_name):
                if self.openstack_compatible:
                    self.images[image_name] = BlockDeviceImage(image_name, image_connections)
                else:
                    self.images[image_name] = LocalImage(image_name, image_connections)
            self.images[image_name].has_instance = True
        LOG.debug("VMThunder: -----PID = %s" % os.getpid())
        LOG.debug("VMThunder: create vm started, vm_name = %s, image_name = %s" % (vm_name, image_name))
        instance_path = self.images[image_name].create_instance(vm_name, snapshot)
        LOG.debug("VMThunder: create vm completed, vm_name = %s, image_name = %s, instance_path = %s" % (vm_name, image_name, instance_path))
        return instance_path

    def destroy(self, vm_name):
        LOG.debug("VMThunder: destroy vm started, vm_name = %s" % (vm_name))
        if not self.vm_names.has_key(vm_name):
            LOG.debug("VMThunder: the vm_name \'%s\' does not exist!" % (vm_name))
            return
        else:
            image_name = self.vm_names[vm_name]
            if self.images[image_name].destroy_instance(vm_name):
                with self.lock:
                    del self.vm_names[vm_name]
        LOG.debug("VMThunder: destroy vm completed, vm_name = %s, ret = %s" % (vm_name, ret))

    def list(self):
        vm_list = []
        for vm_name, image_name in self.vm_names.items():
            vm_list.append(vm_name+':'+image_name)
        return vm_list