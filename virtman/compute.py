#!/usr/bin/env python

import time
import os
import sys
import threading
import traceback
from oslo.config import cfg

from virtman.drivers import fcg
from virtman.drivers import volt
from virtman.image import LocalImage
from virtman.image import BlockDeviceImage
from virtman.utils import exception
from virtman.utils.singleton import singleton

from virtman.openstack.common import log as logging


host_opts = [
    cfg.StrOpt('host_ip',
               default='192.168.137.101',
               help='localhost ip provide Virtman service'),
    cfg.StrOpt('host_port',
               default='8001',
               help='localhost port to provide Virtman service'),
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
CONF.register_opts(host_opts)
CONF.register_opts(compute_opts)

LOG = logging.getLogger(__name__)


class Compute(object):
    def __init__(self):
        pass

    def create(self, instance_name, image_name, image_connections, snapshot):
        return NotImplementedError()

    def destroy(self, instance_name):
        return NotImplementedError()

    def list(self):
        return NotImplementedError()


@singleton
class Virtman(Compute):
    def __init__(self, openstack_compatible=True):
        LOG.info("Virtman: start to create a Virtman Compute_node")
        self.openstack_compatible = openstack_compatible
        self.images = {}
        self.instance_names = {}
        self.lock = threading.Lock()

        if self.openstack_compatible:
            config_files = ['/etc/nova/nova.conf', '/etc/virtman/virtman.conf']
        else:
            config_files = ['/etc/virtman/virtman.conf']
        CONF(sys.argv[1:], project='virtman', default_config_files=config_files)

        logging.setup('virtman')
        if not fcg.is_valid():
            fcg.create_group()

        self.heartbeat_event = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_clock)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        LOG.info("Virtman: create a Virtman Compute_node completed")

    def __del__(self):
        self.heartbeat_event.set()

    def heartbeat_clock(self):
        while not self.heartbeat_event.wait(CONF.heartbeat_interval):
            try:
                self.heartbeat()
            except Exception as ex:
                LOG.error("Virtman: heartbeat failed due to %s" % ex)
                LOG.error("Virtman: traceback is : %s" % traceback.print_exc())
        LOG.debug("Virtman: stop heartbeat timer")

    def heartbeat(self):
        with self.lock:
            self._heartbeat()

    def _heartbeat(self):
        LOG.debug("Virtman: heartbeat start @ %s" % time.asctime())
        for name in self.images.keys():
            if not self.images[name].has_instance:
                if self.images[name].destroy_image():
                    del self.images[name]
        info = volt.heartbeat()
        for name in self.images.keys():
            for image in info:
                if self.images[name].base_image.peer_id == image['peer_id']:
                    self.images[name].adjust_for_heartbeat(image['parents'])
                    break
        LOG.debug("Virtman: heartbeat end @ %s" % time.asctime())

    def create(self, instance_name, image_name, image_connections,
               snapshot=None):
        """
        :param instance_name: string
        :param image_name: string. It is 'iqn', likes
                           "iqn.2010-10.org.openstack:vol_id"
        :param image_connections: list or tuple or single dict, like ({},..) or
                                  [{},..] or {} and each dict make of {
                                  'target_portal':..,'target_iqn':..,
                                  'target_lun':.., ..}
        :param snapshot: snapshot_connection or snapshot_dev
        :returns : string
            "0:info" specifies SUCCESS, info=instance_path
            "1:info" specifies WARNING, info indicates instance_name exists
            "2:info" specifies FAILURE, info create instance failed
        """
        # multiple roots for creating
        LOG.debug("Virtman: create wait for unlock")
        with self.lock:
            return self._create(instance_name, image_name, image_connections,
                                snapshot)

    def _create(self, instance_name, image_name, image_connections, snapshot):
        LOG.info("Virtman: Begin! ----- PID = %s" % os.getpid())
        # Just support for openstack
        if not image_name.startswith("volume-"):
            image_name = "volume-" + image_name
        # for multi image server
        if isinstance(image_connections, tuple) or \
                isinstance(image_connections, list):
            image_connections = list(image_connections)
        else:
            image_connections = [image_connections]
        # with self.lock:
        if instance_name in self.instance_names:
            LOG.warn("Virtman: the instance_name '%s' already exists!" %
                      instance_name)
            return "1:" + "Virtman: the instance_name '%s' already exists!" % \
                          instance_name
        try:
            LOG.debug("Virtman: create VM started, instance_name = %s, "
                      "image_name = %s" % (instance_name, image_name))
            self.instance_names[instance_name] = image_name
            # deploy base image
            if image_name not in self.images:
                LOG.debug("Virtman: now need to create image first!")
                if not self.openstack_compatible:
                    self.images[image_name] = LocalImage(image_name,
                                                         image_connections)
                    self.images[image_name].deploy_image()
                else:
                    self.images[image_name] = BlockDeviceImage(image_name,
                                                               image_connections)
                    self.images[image_name].deploy_image()

            # create snapshot
            instance_path = None
            if self.images[image_name].origin_path:
                LOG.info("Virtman: middle!")
                instance_path = self.images[image_name].create_snapshot(
                    instance_name, snapshot)
                LOG.debug("Virtman: create VM completed, instance_name = %s, "
                          "image_name = %s, instance_path = %s" %
                          (instance_name, image_name, instance_path))
                # instance_path is like '/dev/mapper/snapshot_vm1'
        except Exception as ex:
            LOG.error("Virtman: create image failed, due to %s" % ex)
            LOG.error("Virtman: traceback is : %s" % traceback.print_exc())
            if ex is exception.CreateBaseImageFailed:
                del self.images[image_name]
            if instance_name in self.instance_names:
                del self.instance_names[instance_name]
            raise

        LOG.info("Virtman: end!  instance_path = %s" % instance_path)
        return "0:" + instance_path

    def destroy(self, instance_name):
        """
        :returns : string
            "0:info" specifies SUCCESS, info=""
            "1:info" specifies WARNING, info indicates instance_name not exists
            "2:info" specifies FAILURE, info destroy instance failed
        """
        LOG.debug("Virtman: destroy wait for unlock")
        with self.lock:
            return self._destroy(instance_name)

    def _destroy(self, instance_name):
        LOG.debug("Virtman: destroy VM started, instance_name = %s" %
                  instance_name)
        if instance_name not in self.instance_names:
            LOG.warn("Virtman: the instance_name '%s' does not exist!" %
                      instance_name)
            return "1:" + "Virtman: the instance_name '%s' does not exist!" \
                          % instance_name
        try:
            image_name = self.instance_names[instance_name]
            if self.images[image_name].destroy_snapshot(instance_name):
                # with self.lock:
                del self.instance_names[instance_name]
        except Exception as ex:
            LOG.error("Virtman: destroy instance failed, due to %s" % ex)
            LOG.error("Virtman: traceback is : %s" % traceback.print_exc())
            return "2:" + "Virtman: destroy VM instance failed"

        LOG.debug("Virtman: destroy VM completed, instance_name = %s" %
                  instance_name)
        return "0:"

    def list(self):
        instance_list = []
        for instance_name, image_name in self.instance_names.items():
            instance_list.append(instance_name + ':' + image_name)
        return instance_list

