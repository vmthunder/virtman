# -*- coding: utf-8 -*-
import mock
import os
import string

from tests import base
from oslo_concurrency import processutils as putils
from virtman import baseimage
from virtman.drivers import dmsetup

test_image_connections = [{
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-image',
    'target_lun': '1'}
]


class test_parent():
    def __init__(self, host, port, iqn, lun):
        self.host = host
        self.port = port
        self.iqn = iqn
        self.lun = lun

new_parent = test_parent('10.0.0.2', '3260',
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

