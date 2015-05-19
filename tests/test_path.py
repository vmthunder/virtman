# -*- coding: utf-8 -*-
import mock

from tests import base
from virtman import path
from virtman.drivers import dmsetup
from virtman.drivers import connector
# from pydm.common import processutils as putils

iscsi_disk_format = "ip-%s-iscsi-%s-lun-%s"

test_connection1 = {
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-00000001',
    'target_lun': '1'
}

test_connection2 = {
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-00000002',
    'target_lun': '1'
}

test_connection3 = {
    'target_portal': '10.0.0.1:3260',
    'target_iqn': 'iqn.2010-10.org.openstack:volume-00000003',
    'target_lun': '1'
}


def fake_connect(connection):
    test_path = '/dev/disk/by-path/'+iscsi_disk_format % \
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
        return self.connection_to_str(self.connection)

    @staticmethod
    def connection_to_str(connection):
        return iscsi_disk_format % (connection['target_portal'],
                                    connection['target_iqn'],
                                    connection['target_lun'])

    @staticmethod
    def connect(path):
        path.device_info = fake_connect(path.connection)
        path.device_path = path.device_info['path']
        path.connected = True
        return '/dev/disk/by-path/'+str(path)

    @staticmethod
    def disconnect(path):
        path.connected = False

FakePath1 = FakePath(test_connection1)
FakePath.connect(FakePath1)
FakePath2 = FakePath(test_connection2)
FakePath.connect(FakePath2)
test_paths = {str(FakePath1): FakePath1,
              str(FakePath2): FakePath2}


class TestPath(base.TestCase):
    def setUp(self):
        super(TestPath, self).setUp()
        self.path = path.Path(test_connection1)

    def test_str(self):
        expected = 'ip-10.0.0.1:3260-iscsi-iqn.2010-10.org.' \
                   'openstack:volume-00000001-lun-1'
        result = str(self.path)
        self.assertEqual(expected, result)

    def test_connect(self):
        expected = '/dev/disk/by-path/ip-10.0.0.1:3260-iscsi-iqn.2010-10.' \
                   'org.openstack:volume-00000001-lun-1'
        self.mock_object(connector, 'connect_volume',
                         mock.Mock(side_effect=fake_connect))
        result = path.Path.connect(self.path)
        self.assertEqual(expected, result)
        self.assertEqual(True, self.path.connected)

    def test_disconnect(self):
        self.mock_object(connector, 'disconnect_volume', mock.Mock())
        path.Path.disconnect(self.path)
        self.assertEqual(False, self.path.connected)


class TestPaths(base.TestCase):
    def setUp(self):
        super(TestPaths, self).setUp()
        self.paths = test_paths

    # @mock.patch('virtman.path.Path', FakePath)
    def test_rebuild_multipath(self):
        self.mock_object(dmsetup, 'multipath',
                         mock.Mock(side_effect=lambda x, y: '/dev/mapper/'+x))
        self.mock_object(dmsetup, 'reload_multipath', mock.Mock())
        self.mock_object(dmsetup, 'remove_table', mock.Mock())
        self.mock_object(path.Path, 'connect',
                         mock.Mock(side_effect=FakePath.connect))
        self.mock_object(path.Path, 'disconnect',
                         mock.Mock(side_effect=FakePath.disconnect))
        test_connection2_str = path.Path.connection_to_str(test_connection2)
        test_connection3_str = path.Path.connection_to_str(test_connection3)
        expected_result1 = '/dev/mapper/multipath_test'
        result1 = path.Paths.rebuild_multipath(
            self.paths, [test_connection3], 'multipath_test',
            multipath_path=False)
        self.assertEqual(expected_result1, result1)
        self.assertIn(test_connection3_str, self.paths.keys())

        # for reload multipath
        multipath_path = '/dev/mapper/multipath_test_for_reload'
        result2 = path.Paths.rebuild_multipath(
            self.paths, [test_connection2, test_connection3], 'multipath_test',
            multipath_path=multipath_path)
        self.assertEqual(multipath_path, result2)
        self.assertEqual(2, len(self.paths))
        self.assertIn(test_connection2_str, self.paths.keys())
        self.assertIn(test_connection3_str, self.paths.keys())




