# -*- coding: utf-8 -*-
import mock
import os
import string
import logging

from tests import base
from virtman import instance
from virtman import blockservice
from virtman.drivers import connector
from virtman.drivers import dmsetup
from oslo_concurrency import processutils as putils

test_snapshot_connection = {
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-shanpshot',
    'target_lun': '1'}

device_info = {'path': '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.2010-10'
                       '.org.openstack:volume-snapshot1',
               'type': 'block'}


class TestLocalInstance(base.TestCase):
    def setUp(self):
        super(TestLocalInstance, self).setUp()
        self.instance = instance.LocalInstance(origin_path='/dev/mapper/origin',
                                               instance_name='vm_test',
                                               snapshot_dev='/blocks/snapshot')
        instance.LOG.logger.setLevel(logging.DEBUG)

    def test_create(self):
        self.mock_object(blockservice, 'findloop',
                         mock.Mock(return_value='/dev/loop1'))
        self.mock_object(blockservice, 'try_linkloop', mock.Mock())
        self.mock_object(dmsetup, 'snapshot',
                         mock.Mock(return_value='/dev/mapper/snapshot'))
        expected_result = '/dev/mapper/snapshot'

        result = self.instance.create()

        self.assertEqual(expected_result, result)

    def test_destroy(self):
        self.mock_object(dmsetup, 'remove_table', mock.Mock())
        self.mock_object(blockservice, 'unlinkloop', mock.Mock())

        result = self.instance.destroy()

        self.assertEqual(True, result)


class TestBlockDeviceInstance(base.TestCase):
    def setUp(self):
        super(TestBlockDeviceInstance, self).setUp()
        self.instance = instance.BlockDeviceInstance(
            origin_path='/dev/mapper/origin',
            instance_name='vm_test',
            snapshot_connection=test_snapshot_connection)
        self.cmds = []
        self.mock_object(putils, 'execute',
                         mock.Mock(side_effect=self.fake_execute))
        instance.LOG.logger.setLevel(logging.DEBUG)

    def fake_execute(self, *cmd, **kwargs):
        self.cmds.append(string.join(cmd))
        return "", None

    def exists_side_effect(self, times, first_return=True):
        count = [0]
        max_times = [times]

        def counter_and_return(*arg):
            count[0] += 1
            if count[0] > max_times[0]:
                return not first_return
            return first_return

        return counter_and_return

    def test_create(self):
        self.mock_object(connector, 'connect_volume',
                         mock.Mock(return_value=device_info))
        self.mock_object(os.path, 'exists',
                         mock.Mock(side_effect=self.exists_side_effect(2)))
        self.mock_object(os.path, 'realpath', mock.Mock(
                         return_value='/dev/dm1'))
        self.mock_object(dmsetup, 'snapshot',
                         mock.Mock(return_value='/dev/mapper/snapshot'))

        expected_result = '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.' \
                          '2010-10.org.openstack:volume-snapshot1'
        expected_cmds = ['rm -f /dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.'
                         '2010-10.org.openstack:volume-snapshot1',
                         'ln -s /dev/mapper/snapshot /dev/disk/by-path/'
                         'ip-10.0.0.1:3260-iscsi-iqn.2010-10.org.openstack:'
                         'volume-snapshot1']

        result = self.instance.create()

        self.assertEqual(expected_result, result)
        self.assertEqual(expected_cmds, self.cmds)

    def test_destroy(self):
        self.mock_object(os.path, 'exists', mock.Mock(return_value=True))
        self.mock_object(dmsetup, 'remove_table', mock.Mock())
        self.mock_object(connector, 'disconnect_volume', mock.Mock())

        self.instance.snapshot_link = \
            '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.' \
            '2010-10.org.openstack:volume-snapshot1'
        expected_cmds = ['rm -f '
                          '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.'
                          '2010-10.org.openstack:volume-snapshot1']

        result = self.instance.destroy()

        self.assertEqual(True, result)
        self.assertEqual(expected_cmds, self.cmds)

