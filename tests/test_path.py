# -*- coding: utf-8 -*-
import mock

from tests import base
from virtman import path
from virtman.drivers import connector

connection = {'target_portal': '10.0.0.1:3260',
              'target_iqn': 'iqn.2010-10.org.openstack:volume-00000001',
              'target_lun': 1}
device_info = {'path': '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.2010-10'
                       '.org.openstack:volume-00000001-lun-1',
               'type': 'block'}


class TestPath(base.TestCase):
    def setUp(self):
        super(TestPath, self).setUp()
        self.path = path.Path(connection)

    def test_connect(self):
        expected = '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.2010-10.' \
                   'org.openstack:volume-00000001-lun-1'
        self.mock_object(connector, 'connect_volume',
                         mock.Mock(return_value=device_info))
        result = self.path.connect()
        self.assertEqual(expected, result)
        self.assertEqual(True, self.path.connected)

    def test_disconnect(self):
        self.mock_object(connector, 'disconnect_volume', mock.Mock())
        self.path.disconnect()
        self.assertEqual(False, self.path.connected)