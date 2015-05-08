import os
import mock
from tests import base
from oslo_concurrency import processutils as putils
from virtman.utils import exception


class FunDemo():
    def show(self):
        print 'funDemo'


class FakeDemo():
    def show(self):
        print 'FakeDemo'


class TestDemo(base.TestCase):
    def setUp(self):
        super(TestDemo, self).setUp()
        self.fun = FunDemo()

    def test_fun_add(self):
        result = self.fun.add(1, 2)
        self.assertEqual(3, result)

    def test_fun_cmd(self):
        self.mock_object(putils, 'execute',
                         mock.Mock(side_effect=lambda: (1, None)))
        result = self.fun.cmd()
        self.assertEqual(1, result)

    def test_exception(self):
        raise exception.CreateBaseImageFailed(baseimage='test_image')

