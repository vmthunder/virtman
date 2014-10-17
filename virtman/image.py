#!/usr/bin/env python

import threading

from virtman.baseimage import BlockDeviceBaseImage
from virtman.instance import LocalInstance
from virtman.instance import BlockDeviceInstance
from virtman.utils.lockutils import synchronized

from virtman.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class Image(object):

    def __init__(self, image_name, image_connections):
        self.image_name = image_name
        self.image_connections = image_connections
        self.base_image = None
        self.instances = {}
        self.has_instance = None
        self.lock = threading.Lock()
        # deploy image only once
        self.origin_path = self._deploy_image()

    def create_instance(self, instance_name, snapshot):
        return NotImplementedError()

    def destroy_instance(self, instance_name):
        return NotImplementedError()


class LocalImage(Image):

    def __init__(self, image_name, image_connections):
        super(LocalImage, self).__init__(image_name, image_connections)

    def create_instance(self, instance_name, snapshot_dev):
        LOG.debug("Virtman: create VM instance started, instance_name = %s" % (instance_name))
        self.instances[instance_name] = LocalInstance(self.origin_path, instance_name, snapshot_dev)
        instance_path = self.instances[instance_name].create()
        LOG.debug("Virtman: create VM instance completed, instance_path = %s" % (instance_path))
        return instance_path

    def destroy_instance(self, instance_name):
        LOG.debug("Virtman: destroy VM instance started, instance_name = %s" % (instance_name))
        ret = self.instances[instance_name].destroy()
        if ret:
            del self.instances[instance_name]
            if len(self.instances) <= 0:
                self.has_instance = False
        LOG.debug("Virtman: destroy VM instance completed, result = %s" % (ret))
        return ret

    @synchronized
    def _deploy_image(self):
        self.base_image = BlockDeviceBaseImage(self.image_name, self.image_connections)
        return self.base_image.deploy_base_image()

    @synchronized
    def destroy_image(self):
        return self.base_image.destroy_base_image()

    def adjust_for_heartbeat(self, parents):
        self.base_image.adjust_for_heartbeat(parents)


class BlockDeviceImage(Image):

    def __init__(self, image_name, image_connections):
        super(BlockDeviceImage, self).__init__(image_name, image_connections)

    def create_instance(self, instance_name, snapshot_connection):
        LOG.debug("Virtman: create VM instance started, instance_name = %s" % (instance_name))
        self.instances[instance_name] = BlockDeviceInstance(self.origin_path, instance_name, snapshot_connection)
        instance_path = self.instances[instance_name].create()
        LOG.debug("Virtman: create VM instance completed, instance_path = %s" % (instance_path))
        return instance_path

    def destroy_instance(self, instance_name):
        LOG.debug("Virtman: destroy VM instance started, instance_name = %s" % (instance_name))
        ret = self.instances[instance_name].destroy()
        if ret:
            del self.instances[instance_name]
            if len(self.instances) <= 0:
                self.has_instance = False
        LOG.debug("Virtman: destroy VM instance completed, result = %s" % (ret))
        return ret

    @synchronized
    def _deploy_image(self):
        self.base_image = BlockDeviceBaseImage(self.image_name, self.image_connections)
        return self.base_image.deploy_base_image()

    @synchronized
    def destroy_image(self):
        return self.base_image.destroy_base_image()

    def adjust_for_heartbeat(self, parents):
        self.base_image.adjust_for_heartbeat(parents)


class QCOW2Image(Image):
    """
    QCOW2 image, with
    """
    pass


class RAWImage(Image):
    """
    RAW file image, with loop and dm-snapshoting
    """
    pass