# -*- coding: utf-8 -*-
import os
import mock
import tests
from tests import test_demo
from tests.test_demo import FunDemo
from tests import base
from oslo_concurrency import processutils as putils


class MyDemo():
    def show(self):
        print 'funDemo'


class FakeDemo():
    def show(self):
        print 'FakeDemo'

fun = FunDemo()
print fun

with mock.patch('tests.test_demo.FunDemo', FakeDemo):
    fun = FunDemo()
    print fun
    fun.show()

with mock.patch('__main__.MyDemo', FakeDemo):
    fun = MyDemo()
    print fun
    fun.show()


@mock.patch('tests.test_demo.FunDemo', FakeDemo)
def test():
    tests.test_demo.FunDemo().show()

print "hello"