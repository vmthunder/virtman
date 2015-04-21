# -*- coding: utf-8 -*-
import mock
import os
import string

from tests import base
from oslo_concurrency import processutils as putils
from virtman import baseimage
from virtman.path import connection_to_str

test_image_connections = [{
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-image',
    'target_lun': '1'}
]


def fake_connect(connection):
    test_path = '/dev/disk/by-path/ip-%s-iscsi-%s-lun-%s' % \
        (connection['target_portal'], connection['target_iqn'],
         connection['target_lun'])

    return {
        'path': test_path,
        'type': 'block'
    }


class FakePath():

    def __init__(self, connection):
        self.connection = connection
        self.connected = False
        self.device_info = None
        self.device_path = ''

    def __str__(self):
        return connection_to_str(self.connection)

    def connect(self):
        self.device_info = fake_connect(self.connection)
        self.device_path = self.device_info['path']
        self.connected = True
        return self.device_path

    def disconnect(self):
        self.connected = False


class TestParent():
    def __init__(self, host, port, iqn, lun):
        self.host = host
        self.port = port
        self.iqn = iqn
        self.lun = lun

new_parent = TestParent('10.0.0.2', '3260',
                         'iqn.2010-10.org.openstack:volume-image', '1')


class TestBlockDeviceBaseImage(base.TestCase):
    def setUp(self):
        super(TestBlockDeviceBaseImage, self).setUp()
        self.cmds = []
        self.baseimage = baseimage.BlockDeviceBaseImage('test_baseimage',
                                                        test_image_connections)

    def test_change_status(self):
        result = self.baseimage.change_status(baseimage.STATUS.building,
                                              baseimage.STATUS.ok)
        print result
        result = self.baseimage.change_status(baseimage.STATUS.empty,
                                              baseimage.STATUS.ok)
        print result
        print self.baseimage.status

    def test_adjust_for_heartbeat(self):
        self.mock_object(baseimage.BlockDeviceBaseImage, 'rebuild_multipath',
                         mock.Mock())
        self.assertRaises(Exception, self.baseimage.adjust_for_heartbeat,
                          new_parent)
        # self.assertRaises(baseimage.BlockDeviceBaseImage, 'rebuild_multipath')

