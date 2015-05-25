# -*- coding: utf-8 -*-
import mock
import logging
from tests import base

from virtman import compute_new
from virtman.drivers import fcg
from virtman.drivers import volt
from virtman.image import FakeImage
from virtman.utils import exception

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

def baseimage_exception_for_test(*args):
    raise exception.CreateBaseImageFailed(baseimage='test_baseimage')
def exception_for_test(*args):
    raise exception.TestException

class TestComputer(base.TestCase):
    def setUp(self):
        super(TestComputer, self).setUp()
        compute_new.LOG.logger.setLevel(logging.DEBUG)
        self.mock_object(fcg, 'create_group',
                         mock.Mock())
        self.test_computer = compute_new.Virtman()
        self.test_computer.image_type = 'FakeImage'

    def test_get_image_type(self):
        expected_result1 = 'BlockDeviceImage'
        result1 = self.test_computer.get_image_type(openstack_compatible=True)
        self.assertEqual(expected_result1, result1)

        expected_result2 = 'LocalImage'
        result2 = self.test_computer.get_image_type(openstack_compatible=False)
        self.assertEqual(expected_result2, result2)

    def test_create(self):
        expected_result1 = '0:/dev/mapper/snapshot_test_vm1'
        result1 = self.test_computer.create('test_vm1',
                                            'test_image',
                                            test_image_connections,
                                            test_snapshot_connection1)
        self.assertEqual(expected_result1, result1)

        expected_result2 = '0:/dev/mapper/snapshot_test_vm2'
        result2 = self.test_computer.create('test_vm2',
                                            'test_image',
                                            test_image_connections,
                                            test_snapshot_connection2)
        self.assertEqual(expected_result2, result2)

    def test_create_with_already_exist(self):
        self.test_computer.create('test_vm1',
                                  'test_image',
                                  test_image_connections,
                                  test_snapshot_connection1)
        expected_result = "1:Virtman: the instance_name 'test_vm1' " \
                          "already exists!"
        result = self.test_computer.create('test_vm1',
                                  'test_image',
                                  test_image_connections,
                                  test_snapshot_connection1)
        self.assertEqual(expected_result, result)

    def test_create_with_exception(self):
        self.mock_object(FakeImage, 'deploy_image',
                         mock.Mock(side_effect=baseimage_exception_for_test))
        expected_result = "2:Virtman: create image failed"

        result = self.test_computer.create('test_vm1',
                                           'test_image',
                                           test_image_connections,
                                           test_snapshot_connection1)

        self.assertEqual(expected_result, result)
        self.assertEqual(0, len(self.test_computer.images))
        self.assertEqual(0, len(self.test_computer.instance_names))

    def test_destroy(self):
        self.test_computer.create('test_vm1',
                                  'test_image',
                                  test_image_connections,
                                  test_snapshot_connection1)
        expected_result = '0:'
        result = self.test_computer.destroy('test_vm1')
        self.assertEqual(expected_result, result)

    def test_destroy_with_not_exist(self):
        expected_result = "1:Virtman: the instance_name 'test_vm1' " \
                          "does not exist!"
        result = self.test_computer.destroy('test_vm1')
        self.assertEqual(expected_result, result)

    def test_destroy_with_exception(self):
        self.mock_object(FakeImage, 'destroy_snapshot',
                         mock.Mock(side_effect=exception_for_test))
        self.test_computer.create('test_vm1',
                                  'test_image',
                                  test_image_connections,
                                  test_snapshot_connection1)
        expected_result = "2:Virtman: destroy VM instance failed"

        result = self.test_computer.destroy('test_vm1')

        self.assertEqual(expected_result,result)

    def test_list(self):
        self.test_computer.create('test_vm1',
                                  'test_image',
                                  test_image_connections,
                                  test_snapshot_connection1)
        self.test_computer.create('test_vm2',
                                  'test_image',
                                  test_image_connections,
                                  test_snapshot_connection2)

        expected_result = ['test_vm1:volume-test_image',
                           'test_vm2:volume-test_image']
        result = self.test_computer.list()
        self.assertEqual(expected_result, result)
