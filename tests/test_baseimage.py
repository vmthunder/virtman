# -*- coding: utf-8 -*-
import mock
import os
import string
import logging

from oslo.config import cfg
from tests import base
from virtman.path import Paths
from virtman import baseimage_new
from virtman.path import Path
from virtman.drivers import connector
from virtman.drivers import fcg
from virtman.drivers import dmsetup
from virtman.drivers import iscsi
from virtman.drivers import volt

CONF = cfg.CONF

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
        return Path.connection_to_str(self.connection)

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
        self.peer_id = 'test_peer_id'

new_parent = TestParent('10.0.0.2', '3260',
                        'iqn.2010-10.org.openstack:volume-image', '1')

parent_connection = {
    'target_portal': '10.0.0.2:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-00000001',
    'target_lun': '1'
}


class TestBlockDeviceBaseImage(base.TestCase):
    def setUp(self):
        super(TestBlockDeviceBaseImage, self).setUp()
        self.cmds = []
        baseimage_new.LOG.logger.setLevel(logging.DEBUG)
        self.baseimage = \
            baseimage_new.BlockDeviceBaseImage('test_baseimage',
                                               test_image_connections)

    def test_check_local_image(self):
        CONF.host_ip = '10.0.0.1'
        self.baseimage.check_local_image()
        self.assertEqual(True, self.baseimage.is_local_has_image)
        CONF.host_ip = '10.0.0.2'
        self.baseimage.check_local_image()
        self.assertEqual(False, self.baseimage.is_local_has_image)

    def test_adjust_for_heartbeat(self):
        self.mock_object(Paths, 'rebuild_multipath',
                         mock.Mock(return_value='/dev/mapper/test_multipath'))
        self.baseimage.adjust_for_heartbeat([parent_connection])
        print self.baseimage.multipath_path

    def test_get_parent(self):
        CONF.host_ip = '10.0.0.2'
        self.mock_object(volt, 'get',
                         mock.Mock(return_value=('test_peer_id', [new_parent])))
        result = self.baseimage.get_parent()
        self.assertEqual([new_parent], result)

    def test_modify_parent_connection(self):
        CONF.host_ip = '10.0.0.2'
        self.mock_object(volt, 'get',
                         mock.Mock(return_value=('test_peer_id', [new_parent])))
        self.baseimage.is_local_has_image = True
        expected_result = [{'target_lun': '1',
                            'target_iqn': 'iqn.2010-10.org.openstack:'
                                          'volume-image',
                            'target_portal': '10.0.0.1:3260'}]
        result = self.baseimage.modify_parent_connection()
        self.assertEqual(expected_result, result)
        expected_result = [{'target_lun': '1',
                            'target_iqn': 'iqn.2010-10.org.openstack:'
                                          'volume-image',
                            'target_portal': '10.0.0.2:3260'}]
        self.baseimage.is_local_has_image = False
        result = self.baseimage.modify_parent_connection()
        self.assertEqual(expected_result, result)

    def test_deploy_base_image(self):
        CONF.master_ip = '10.0.0.1'
        CONF.host_ip = '10.0.0.2'
        self.mock_object(volt, 'get',
                         mock.Mock(return_value=('test_peer_id', [new_parent])))
        self.mock_object(connector, 'connect_volume',
                         mock.Mock(side_effect=fake_connect))
        self.mock_object(Paths, 'rebuild_multipath',
                         mock.Mock(return_value='/dev/mapper/test_multipath'))
        self.mock_object(fcg, 'add_disk',
                         mock.Mock(return_value='/dev/mapper/test_cached'))
        self.mock_object(dmsetup, 'origin',
                         mock.Mock(return_value='/dev/mapper/test_origin'))
        self.mock_object(iscsi, 'exists',
                         mock.Mock(return_value=False))
        self.mock_object(iscsi, 'create_iscsi_target',
                         mock.Mock(return_value='1'))
        self.mock_object(iscsi, 'create_iscsi_target',
                         mock.Mock(return_value='1'))
        self.mock_object(volt, 'login',
                         mock.Mock(return_value=CONF.master_ip))
        excepted_result = '/dev/mapper/test_origin'
        result = self.baseimage.deploy_base_image()
        self.assertEqual(excepted_result, result)
        self.assertEqual('1', self.baseimage.target_id)
        self.assertEqual('/dev/mapper/test_origin', self.baseimage.origin_path)
        self.assertEqual('origin_test_baseimage', self.baseimage.origin_name)
        self.assertEqual('/dev/mapper/test_cached', self.baseimage.cached_path)
        self.assertEqual('/dev/mapper/test_multipath',
                         self.baseimage.multipath_path)
        self.assertEqual('multipath_test_baseimage',
                         self.baseimage.multipath_name)



