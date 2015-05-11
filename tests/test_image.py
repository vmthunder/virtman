# -*- coding: utf-8 -*-
import mock
import os
import string
import logging
from tests import base
from virtman import image
from virtman.baseimage_new import BlockDeviceBaseImage
from virtman.instance import LocalInstance
from virtman.instance import BlockDeviceInstance
from virtman.utils import exception
from oslo.concurrency import lockutils


test_image_connections = [{
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-image',
    'target_lun': '1'}
]

class TestLocalImage(base.TestCase):
    def setUp(self):
        super(TestLocalImage, self).setUp()
        self.test_image = image.LocalImage('test_local_image',
                                           test_image_connections)

    def test_deploy_image(self):
        self.test_image.deploy_image()

class BlockDeviceImage(base.TestCase):
    def setUp(self):
        super(BlockDeviceImage, self).setUp()
        self.test_image = image.BlockDeviceImage('test_block_device_image',
                                                 test_image_connections)