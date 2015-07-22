# -*- coding: utf-8 -*-
import mock
import os
import string

from tests import base
from virtman import imageservice
from virtman import blockservice
from virtman.drivers import iscsi
from virtman.openstack.common import processutils as putils


test_iqn_prefix = 'iqn.2010-10.org.test:'


class TestImageService(base.TestCase):
    def setUp(self):
        super(TestImageService, self).setUp()
        self.cmds = []
        self.mock_object(putils, 'execute',
                         mock.Mock(side_effect=self.fake_execute))

    def fake_execute(self, *cmd, **kwargs):
        self.cmds.append(string.join(cmd))
        return "", None

    def test_create_image_target(self):

        self.mock_object(iscsi, 'create_iscsi_target',
                         mock.Mock(return_value='1'))

        self.mock_object(os.path, 'exists', mock.Mock(return_value=False))
        self.mock_object(blockservice, 'is_looped',
                         mock.Mock(return_value=False))
        expected_result = '2:Virtman: Image Service: Warning!image file_path' \
                          ' = /blocks/image1 not exists! Please use another ' \
                          'image file'
        result = imageservice.create_image_target('image1', '/blocks/image1',
                                                  '/dev/loop2', test_iqn_prefix)
        self.assertEqual(expected_result, result)

        expected_result = '0:1:/dev/loop2'
        self.mock_object(os.path, 'exists', mock.Mock(return_value=True))
        result = imageservice.create_image_target('image1', '/blocks/image1',
                                                  '/dev/loop2', test_iqn_prefix)
        self.assertEqual(expected_result, result)

        expected_result = '1:Virtman: Image Service: Warning! image_name = ' \
                          'volume-image1 exists! Please use another name'
        result = imageservice.create_image_target('image1', '/blocks/image1',
                                                  '/dev/loop2', test_iqn_prefix)
        self.assertEqual(expected_result, result)

    def test_destroy_image_target(self):
        self.mock_object(iscsi, 'remove_iscsi_target',
                         mock.Mock(return_value=None))
        self.mock_object(blockservice, 'is_looped',
                         mock.Mock(return_value=True))

        imageservice.targetlist = {'volume-image1': '1:/dev/loop1',
                                   'volume-image2': '1:/dev/loop2'}
        expected_result = '1:Virtman: Image Service: Warning! image_name = ' \
                          'volume-image3 not exists!'
        result = imageservice.destroy_image_target('image3')
        self.assertEqual(expected_result, result)

        expected_result = '0:'
        result = imageservice.destroy_image_target('image2')
        self.assertEqual(expected_result, result)

    def test_list_image_target(self):
        imageservice.targetlist = {'volume-image1': '1:/dev/loop1',
                                   'volume-image2': '1:/dev/loop2'}
        result = imageservice.list_image_target()
        self.assertEqual(imageservice.targetlist, result)