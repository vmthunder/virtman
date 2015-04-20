# -*- coding: utf-8 -*-
import mock

from tests import base
from virtman import path
from virtman.drivers import connector

test_connection = {
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-00000001',
    'target_lun': 1
}


def fake_connect(connection):
    test_path = '/dev/disk/by-path/ip-%s-iscsi-%s-lun-%s' % \
        (connection['target_portal'], connection['target_iqn'],
         connection['target_lun'])

    return {
        'path': test_path,
        'type': 'block'
    }


class TestPath(base.TestCase):
    def setUp(self):
        super(TestPath, self).setUp()
        self.path = path.Path(test_connection)

    def test_connect(self):
        expected = '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.2010-10.' \
                   'org.openstack:volume-00000001-lun-1'
        self.mock_object(connector, 'connect_volume',
                         mock.Mock(side_effect=fake_connect))
        result = self.path.connect()
        self.assertEqual(expected, result)
        self.assertEqual(True, self.path.connected)

    def test_disconnect(self):
        self.mock_object(connector, 'disconnect_volume', mock.Mock())
        self.path.disconnect()
        self.assertEqual(False, self.path.connected)