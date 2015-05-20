#!/usr/bin/env python

import threading

from virtman.baseimage_new import BlockDeviceBaseImage
from virtman.snapshot import LocalSnapshot
from virtman.snapshot import BlockDeviceSnapshot
from virtman.utils import exception
from oslo.concurrency import lockutils

from virtman.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class Image(object):

    def __init__(self, image_name, image_connections, base_image):
        self.image_name = image_name
        self.image_connections = image_connections
        self.base_image = base_image(self.image_name, self.image_connections)
        self.snapshots = {}
        self.lock = threading.Lock()
        # deploy image only once
        self.origin_path = None

    def has_instance(self):
        if len(self.snapshots) > 0:
            return True
        else:
            return False

    def create_snapshot(self, instance_name, snapshot):
        raise NotImplementedError()

    def destroy_snapshot(self, instance_name):
        raise NotImplementedError()

    def deploy_image(self):
        raise NotImplementedError()

    def destroy_image(self):
        raise NotImplementedError()

    def adjust_for_heartbeat(self, parents):
        raise NotImplementedError()


class LocalImage(Image):

    def __init__(self, image_name, image_connections,
                 base_image=BlockDeviceBaseImage):
        super(LocalImage, self).__init__(image_name, image_connections,
                                         base_image)

    def create_snapshot(self, instance_name, snapshot_dev):
        LOG.debug("Virtman: create VM instance started, instance_name = %s" %
                  instance_name)
        self.snapshots[instance_name] = LocalSnapshot(self.origin_path,
                                                      instance_name,
                                                      snapshot_dev)
        instance_path = self.snapshots[instance_name].create()
        LOG.debug("Virtman: create VM instance completed, instance_path = %s" %
                  instance_path)
        return instance_path

    def destroy_snapshot(self, instance_name):
        LOG.debug("Virtman: destroy VM instance started, instance_name = %s" %
                  instance_name)
        ret = self.snapshots[instance_name].destroy()
        if ret:
            del self.snapshots[instance_name]
        LOG.debug("Virtman: destroy VM instance completed, result = %s" %
                  ret)
        return ret

    @lockutils.synchronized('deploy_image')
    def deploy_image(self):
        if self.origin_path is None:
            try:
                self.origin_path = self.base_image.deploy_base_image()
            except Exception as ex:
                LOG.error("Virtman: create baseimage failed, due to %s" % ex)
                raise exception.CreateBaseImageFailed(baseimage=self.image_name)

    @lockutils.synchronized('deploy_image')
    def destroy_image(self):
        return self.base_image.destroy_base_image()
        # return BlockDeviceBaseImage.destroy_base_image(self.base_image)

    def adjust_for_heartbeat(self, parents):
        self.base_image.adjust_for_heartbeat(parents)
        # BlockDeviceBaseImage.adjust_for_heartbeat(self.base_image, parents)


class BlockDeviceImage(Image):

    def __init__(self, image_name, image_connections,
                 base_image=BlockDeviceBaseImage):
        super(BlockDeviceImage, self).__init__(image_name, image_connections,
                                               base_image)

    def create_snapshot(self, instance_name, snapshot_connection):
        LOG.debug("Virtman: create VM instance started, instance_name = %s" %
                  instance_name)
        self.snapshots[instance_name] = BlockDeviceSnapshot(self.origin_path,
                                                            instance_name,
                                                            snapshot_connection)
        instance_path = self.snapshots[instance_name].create()
        LOG.debug("Virtman: create VM instance completed, instance_path = %s" %
                  instance_path)
        return instance_path

    def destroy_snapshot(self, instance_name):
        LOG.debug("Virtman: destroy VM instance started, instance_name = %s" %
                  instance_name)
        ret = self.snapshots[instance_name].destroy()
        if ret:
            del self.snapshots[instance_name]
        LOG.debug("Virtman: destroy VM instance completed, result = %s" %
                  ret)
        return ret

    @lockutils.synchronized('deploy_image')
    def deploy_image(self):
        if self.origin_path is None:
            try:
                self.origin_path = self.base_image.deploy_base_image()
            except Exception as ex:
                LOG.error("Virtman: create baseimage failed, due to %s" % ex)
                raise exception.CreateBaseImageFailed(baseimage=self.image_name)

    @lockutils.synchronized('deploy_image')
    def destroy_image(self):
        return self.base_image.destroy_base_image()
        # return BlockDeviceBaseImage.destroy_base_image(self.base_image)

    def adjust_for_heartbeat(self, parents):
        self.base_image.adjust_for_heartbeat(parents)
        # BlockDeviceBaseImage.adjust_for_heartbeat(self.base_image, parents)


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