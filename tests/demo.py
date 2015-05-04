# -*- coding: utf-8 -*-
import os
import mock
from test_demo import FunDemo
from tests import base
from oslo_concurrency import processutils as putils

class FakeDemo():
    def show(self):
        print 'FakeDemo'

with mock.patch('test_demo.FunDemo', FakeDemo, spec=False):
    fun = FunDemo()
    assert isinstance(fun, FunDemo)
    fun.show()
    # print fun.add(1, 3)


@mock.patch('test_demo.FunDemo', FakeDemo)
def test(aa):
    print aa
    mm = FunDemo()
    mm.show()

test(aa=1111)

