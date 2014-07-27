#!/usr/bin/env python


import threading

from vmthunder.baseimage import BaseImage
from vmthunder.snapshot import Snapshot
from vmthunder.lockutils import synchronized
from vmthunder.singleton import singleton


class Image(object):

    def __init_(self):
        return NotImplementedError()

    def __str__(self):
        return str(self.base_image)

    def deploy_image(self, vm_name, image_connection):
        return NotImplementedError()

    def destroy_image(self, vm_name):
        return NotImplementedError()

    def adjust(self):
        return NotImplementedError()

    def create_vm(self):
        return NotImplementedError()

class LocalImage(Image):

    def __init__(self, image_name, image_connection):
        self.image_name = image_name
        self.image_connection = image_connection
        self.base_image = None
        self.instances = {}
        self.has_instance = None
        self.origin_path = None
        self.peer_id = None
        self.lock = threading.Lock()

    @synchronized
    def deploy_image(self, vm_name, image_connection):
        pass

    @synchronized
    def destroy_image(self, vm_name):
        pass

    @synchronized
    def adjust(self):
        pass

    def create_vm(self, vm_name, snapshot_dev):
        if origin_path is None:
            self._deploy_image()
        snapshot = LocalSnapshot(snapshot_dev)


class BlockDeviceImage(Image):

    def __init__(self, image_name, image_connections):
        self.image_name = image_name
        if isinstance(image_connections, tuple) or isinstance(image_connections, list):
            self.image_connections = list(image_connections)
        else:
            self.image_connections = [image_connections]
        self.base_image = BlockDeviceBaseImage(self.image_name, self.image_connections)
        self.instances = {}
        self.has_instance = None
        self.origin_path = None
        self.peer_id = None
        self.lock = threading.Lock()

    @synchronized
    def adjust_for_heartbeat(self, parents):
        self.base_image.adjust_for_heartbeat(parents)

    def create_instance(self, vm_name, snapshot_connection):
        if self.origin_path is None:
            self.origin_path = self._deploy_image()
        self.instances[vm_name] = Instance(self.origin_path, vm_name, snapshot_connection)
        instance_path = self.instances[vm_name].create()
        return instance_path

    def destroy_instance(self, vm_name):
        ret = self.instances[vm_name].destroy()
        if ret:
            del self.instances[vm_name]
            if len(self.instances) <= 0:
                self.has_instance = False
        return ret

    @synchronized
    def _deploy_image(self):
        return self.base_image.deploy_base_image()

    @synchronized
    def destroy_image(self):
        return self.base_image.destroy_base_image()


class Qcow2Image(Image):
    """
    QCOW2 image, with
    """
    pass


class RAWImage(Image):
    """
    RAW file image, with loop and dm-snapshoting
    """
    pass