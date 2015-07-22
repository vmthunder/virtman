# -*- coding: utf-8 -*-
import mock
import testtools
import os
import string
import logging
from tests import base
from testtools import ExpectedException
from virtman import image
from virtman.baseimage_new import FakeBaseImage
from virtman.snapshot import LocalSnapshot
from virtman.snapshot import BlockDeviceSnapshot
from virtman.utils.exception import TestException
from virtman.utils.exception import CreateSnapshotFailed


test_image_connections = [{
    'target_portal': '10.0.0.3:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-image',
    'target_lun': '1'}
]

test_snapshot_connection1 = {
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-shanpshot1',
    'target_lun': '1'}

test_snapshot_connection2 = {
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-shanpshot2',
    'target_lun': '1'}

def exception_for_test(*args):
    raise TestException

class TestImage(base.TestCase):
    def setUp(self):
        super(TestImage, self).setUp()
        image.LOG.logger.setLevel(logging.DEBUG)
        self.test_image = image.Image('test_image',
                                      test_image_connections,
                                      base_image=FakeBaseImage)

    def test_deploy_image(self):
        self.assertRaises(NotImplementedError, self.test_image.deploy_image)

    def test_destroy_image(self):
        self.assertRaises(NotImplementedError, self.test_image.destroy_image)

    def test_create_snapshot(self):
        self.assertRaises(NotImplementedError, self.test_image.create_snapshot,
                          None, None)

    def test_destroy_snapshot(self):
        self.assertRaises(NotImplementedError, self.test_image.destroy_snapshot,
                          None)

    def test_adjust_for_heartbeat(self):
        self.assertRaises(NotImplementedError,
                          self.test_image.adjust_for_heartbeat, None)


class TestLocalImage(base.TestCase):
    def setUp(self):
        super(TestLocalImage, self).setUp()
        image.LOG.logger.setLevel(logging.DEBUG)
        self.test_image = image.LocalImage('test_local_image',
                                           test_image_connections,
                                           base_image=FakeBaseImage)

    def test_deploy_image(self):
        self.test_image.deploy_image()
        self.assertEqual('/dev/mapper/test_origin',
                         self.test_image.origin_path)
        self.assertEqual(True, self.test_image.has_instance)

    def test_destroy_image(self):
        self.test_image.deploy_image()
        result = self.test_image.destroy_image()
        self.assertEqual(True, result)

    def test_create_snapshot(self):
        self.mock_object(LocalSnapshot, 'create',
                         mock.Mock(return_value='/test_path'))
        self.test_image.deploy_image()
        self.test_image.create_snapshot('test_instance1', '/blocks/snapshot1')

        self.assertEqual('/dev/mapper/test_origin', self.test_image.origin_path)
        self.assertEqual(True, self.test_image.has_instance)
        self.assertEqual(1, len(self.test_image.snapshots))

        self.test_image.create_snapshot('test_instance2', '/blocks/snapshot2')

        self.assertEqual(2, len(self.test_image.snapshots))

    def test_create_snapshot_with_exception(self):
        self.mock_object(LocalSnapshot, 'create',
                         mock.Mock(side_effect=TestException))
        with ExpectedException(CreateSnapshotFailed):
            self.test_image.deploy_image()
            self.test_image.create_snapshot('test_instance1',
                                            '/blocks/snapshot1')
        self.assertEqual(0, len(self.test_image.snapshots))
        self.assertEqual(False, self.test_image.has_instance)

    def test_destroy_snapshot(self):
        self.mock_object(LocalSnapshot, 'create',
                         mock.Mock(return_value='/test_path'))
        self.mock_object(LocalSnapshot, 'destroy',
                         mock.Mock(return_value=True))

        self.test_image.deploy_image()
        self.test_image.create_snapshot('test_instance1', '/blocks/snapshot1')
        self.test_image.destroy_snapshot('test_instance1')

        self.assertEqual(False, self.test_image.has_instance)
        self.assertEqual(0, len(self.test_image.snapshots))


class TestBlockDeviceImage(base.TestCase):
    def setUp(self):
        super(TestBlockDeviceImage, self).setUp()
        image.LOG.logger.setLevel(logging.DEBUG)
        self.test_image = image.BlockDeviceImage('test_block_device_image',
                                                 test_image_connections,
                                                 base_image=FakeBaseImage)

    def test_deploy_image(self):
        self.test_image.deploy_image()
        self.assertEqual('/dev/mapper/test_origin',
                         self.test_image.origin_path)
        self.assertEqual(True, self.test_image.has_instance)

    def test_destroy_image(self):
        self.test_image.deploy_image()
        result = self.test_image.destroy_image()
        self.assertEqual(True, result)

    def test_create_snapshot(self):
        self.mock_object(BlockDeviceSnapshot, 'create',
                         mock.Mock(return_value='/dev/mappper/test_path'))
        self.test_image.deploy_image()
        self.test_image.create_snapshot('test_instance1',
                                        test_snapshot_connection1)

        self.assertEqual('/dev/mapper/test_origin', self.test_image.origin_path)
        self.assertEqual(True, self.test_image.has_instance)
        self.assertEqual(1, len(self.test_image.snapshots))

        self.test_image.create_snapshot('test_instance2',
                                        test_snapshot_connection2)

        self.assertEqual(2, len(self.test_image.snapshots))

    def test_create_snapshot_with_exception(self):
        self.mock_object(LocalSnapshot, 'create',
                         mock.Mock(side_effect=TestException))
        with ExpectedException(CreateSnapshotFailed):
            self.test_image.deploy_image()
            self.test_image.create_snapshot('test_instance1',
                                            '/blocks/snapshot1')
        self.assertEqual(0, len(self.test_image.snapshots))
        self.assertEqual(False, self.test_image.has_instance)

    def test_destroy_snapshot(self):
        self.mock_object(BlockDeviceSnapshot, 'create',
                         mock.Mock(return_value='/dev/mappper/test_path'))
        self.mock_object(BlockDeviceSnapshot, 'destroy',
                         mock.Mock(return_value=True))

        self.test_image.deploy_image()
        self.test_image.create_snapshot('test_instance1',
                                        test_snapshot_connection1)
        self.test_image.destroy_snapshot('test_instance1')

        self.assertEqual(False, self.test_image.has_instance)
        self.assertEqual(0, len(self.test_image.snapshots))
