# -*- coding: utf-8 -*-
import mock
import os
import string
import logging
from tests import base
from virtman import image
from virtman.baseimage_new import FakeBaseImage
from virtman.instance import LocalInstance
from virtman.instance import BlockDeviceInstance
from virtman.utils import exception
from oslo.concurrency import lockutils


test_image_connections = [{
    'target_portal': '10.0.0.3:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-image',
    'target_lun': '1'}
]


class TestLocalImage(base.TestCase):
    def setUp(self):
        super(TestLocalImage, self).setUp()
        image.LOG.logger.setLevel(logging.DEBUG)
        self.test_image = image.LocalImage('test_local_image',
                                           test_image_connections,
                                           base_image=FakeBaseImage)

    def test_deploy_image(self):
        result = self.test_image.deploy_image()
        self.assertEqual('/dev/mapper/test_origin', result)

    def test_destroy_image(self):
        self.test_image.deploy_image()
        result = self.test_image.destroy_image()
        self.assertEqual(True, result)

    def test_create_instance(self):
        self.mock_object(LocalInstance, 'create',
                         mock.Mock(return_value='/test_path'))
        self.test_image.destroy_image()
        self.test_image.create_instance('test_instance1', '/blocks/snapshot1')

        self.assertEqual(True, self.test_image.has_instance())
        self.assertEqual(1, len(self.test_image.instances))

        self.test_image.create_instance('test_instance2', '/blocks/snapshot2')

        self.assertEqual(2, len(self.test_image.instances))

    def test_destroy_instance(self):
        self.mock_object(LocalInstance, 'create',
                         mock.Mock(return_value='/test_path'))
        self.mock_object(LocalInstance, 'destroy',
                         mock.Mock(return_value=True))

        self.test_image.destroy_image()
        self.test_image.create_instance('test_instance1', '/blocks/snapshot1')
        self.test_image.destroy_instance('test_instance1')

        self.assertEqual(False, self.test_image.has_instance())
        self.assertEqual(0, len(self.test_image.instances))



class BlockDeviceImage(base.TestCase):
    def setUp(self):
        super(BlockDeviceImage, self).setUp()
        self.test_image = image.BlockDeviceImage('test_block_device_image',
                                                 test_image_connections)