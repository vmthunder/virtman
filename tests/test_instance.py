# -*- coding: utf-8 -*-
import mock
import os
import string
import logging

from tests import base
from virtman import instance
from virtman import snapshot
from virtman.drivers import dmsetup
from oslo_concurrency import processutils as putils

test_snapshot_connection = {
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-shanpshot',
    'target_lun': 1}


class TestLocalInstance(base.TestCase):
    def setUp(self):
        super(TestLocalInstance, self).setUp()
        self.instance = instance.LocalInstance(origin_path='/dev/mapper/origin',
                                               instance_name='vm_test',
                                               snapshot_dev='/blocks/snapshot')
        instance.LOG.logger.setLevel(logging.DEBUG)

    def test_create(self):
        self.mock_object(snapshot.LocalSnapshot, 'create_snapshot',
                         mock.Mock(return_value='dev/loop1'))
        self.mock_object(dmsetup, 'snapshot',
                         mock.Mock(return_value='/dev/mapper/snapshot'))
        result = self.instance.create()
        print result

    def test_destroy(self):
        self.mock_object(dmsetup, 'remove_table', mock.Mock())
        self.mock_object(snapshot.LocalSnapshot, 'destroy_snapshot',
                         mock.Mock())
        result = self.instance.destroy()
        print result


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

    def test_create(self):
        self.mock_object(snapshot.BlockDeviceSnapshot, 'create_snapshot',
                         mock.Mock(return_value=(
                             '/dev/dm1',
                             '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.'
                             '2010-10.org.openstack:volume-snapshot1')
                             )
                         )
        self.mock_object(dmsetup, 'snapshot',
                         mock.Mock(return_value='/dev/mapper/snapshot'))
        self.mock_object(os.path, 'exists', mock.Mock(return_value=False))
        result = self.instance.create()
        print result
        print self.cmds

    def test_destroy(self):
        self.mock_object(os.path, 'exists', mock.Mock(return_value=True))
        self.mock_object(dmsetup, 'remove_table', mock.Mock())
        self.mock_object(snapshot.BlockDeviceSnapshot, 'destroy_snapshot',
                         mock.Mock())
        self.instance.snapshot_link = \
            '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.' \
            '2010-10.org.openstack:volume-snapshot1'
        result = self.instance.destroy()
        print result
        print self.cmds

