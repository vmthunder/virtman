import os
import stubout
import mock
from tests import base
from oslo_concurrency import processutils as putils


class FunDemo():
    def add(self, a, b):
        return a + b

    def cmd(self, *cmd, **kwargs):
        (out , err) = putils.execute(*cmd, **kwargs)
        print out, err
        return out


class TestDemo(base.TestCase):
    def setUp(self):
        super(TestDemo, self).setUp()
        self.fun = FunDemo()
        self.stubs = stubout.StubOutForTesting()

    def test_fun_add(self):
        result = self.fun.add(1, 2)
        self.assertEqual(3, result)

    def test_fun_cmd(self):
        self.stubs.Set(putils, 'execute', lambda: (1, None))
        result = self.fun.cmd()
        self.assertEqual(1, result)

    def test_mock(self):
        self.stubs.Set(os.path, 'exists',
                       lambda x: False if x.startswith('/block')
                       else True)
        print os.path.exists('/block')
        print os.path.exists('/home')
