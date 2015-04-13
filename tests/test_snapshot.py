# -*- coding: utf-8 -*-
import mock
import os
import logging

from tests import base
from virtman import snapshot
from virtman import blockservice
from virtman.drivers import connector


connection = {'target_portal': '10.0.0.1:3260',
              'target_iqn': 'iqn.2010-10.org.openstack:volume-snapshot1',
              'target_lun': 1}
device_info = {'path': '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.2010-10'
                       '.org.openstack:volume-snapshot1',
               'type': 'block'}

class TestLocalSnapshot(base.TestCase):
    def setUp(self):
        super(TestLocalSnapshot, self).setUp()
        self.snapshot = snapshot.LocalSnapshot()
        snapshot.LOG.logger.setLevel(logging.DEBUG)

    def test_create_snapshot(self):
        self.mock_object(blockservice, 'findloop',
                         mock.Mock(return_value='/dev/loop1'))
        self.mock_object(blockservice, 'try_linkloop', mock.Mock())
        result = self.snapshot.create_snapshot()
        print result

    def test_destroy_snapshot(self):
         self.mock_object(blockservice, 'unlinkloop', mock.Mock())
         result = self.snapshot.destroy_snapshot()
         print result

class TestBlockDeviceSnapshot(base.TestCase):
    def setUp(self):
        super(TestBlockDeviceSnapshot, self).setUp()
        self.snapshot = snapshot.BlockDeviceSnapshot(connection)
        snapshot.LOG.logger.setLevel(logging.DEBUG)

    def test_create_snapshot(self):
        self.mock_object(connector, 'connect_volume',
                         mock.Mock(return_value=device_info))
        self.mock_object(os.path, 'exists', mock.Mock(return_value=True))
        self.mock_object(os.path, 'realpath', mock.Mock(
            return_value='/dev/dm1'))
        result = self.snapshot.create_snapshot()
        print result

    def test_destroy_snapshot(self):
        self.mock_object(connector, 'disconnect_volume', mock.Mock())
        result = self.snapshot.destroy_snapshot()
        print result