import os
import mock
import testtools
from tests import base
from virtman.openstack.common import processutils as putils
from virtman.utils import exception


class FunDemo():
    def show(self):
        print 'funDemo'

    def add(self, a, b):
        return a + b

    @staticmethod
    def cmd():
        return putils.execute()


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
                         mock.Mock(return_value=1))
        result = self.fun.cmd()
        self.assertEqual(1, result)

    def test_exception(self):
        with testtools.ExpectedException(exception.CreateBaseImageFailed):
            raise exception.CreateBaseImageFailed(baseimage='test_image')

