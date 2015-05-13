# -*- coding: utf-8 -*-
import mock
import logging
from tests import base

from virtman import compute
from virtman.drivers import fcg
from virtman.drivers import volt
from virtman.image import LocalImage
from virtman.image import BlockDeviceImage
from virtman.utils import exception


class TestComputer(base.TestCase):
    def setUp(self):
        super(TestComputer, self).setUp()
        compute.LOG.logger.setLevel(logging.DEBUG)
        # self.mock_object(compute.Virtman, 'heartbeat_clock', mock.Mock())
        self.test_computer = compute.Virtman()

    def test_create(self):
        pass

    def test_destroy(self):
        pass

    def test_list(self):
        pass