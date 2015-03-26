# -*- coding: utf-8 -*-
import stubout
import mock
import os
import string

from tests import base
from oslo_concurrency import processutils as putils
from virtman import blockservice



class BlockServiceTestCase(base.TestCase):
    def setUp(self):
        super(BlockServiceTestCase, self).setUp()
        self.stubs = stubout.StubOutForTesting()
        self.cmds = []
        self.stubs.Set(putils, 'execute', self.fake_execute)

    def fake_execute(self, *cmd, **kwargs):
        self.cmds.append(string.join(cmd))
        return "", None

    def fake_loop_list(self, *cmd, **kwargs):
        return """/dev/loop0: [8010]:264910 (/block/image0)
        /dev/loop1: [8010]:264910 (/block/image1)""", None

    def test_findloop(self):
        blockservice.findloop()
        print self.cmds

    def test_try_linkloop(self):
        self.stubs.Set(os.path, 'exists', lambda x:
                       False if x.startswith('/root/blocks/') else True)
        blockservice.try_linkloop('/dev/loop1')
        print self.cmds

    def test_is_looped(self):
        self.stubs.Set(putils, 'execute', self.fake_loop_list)
        result = blockservice.is_looped('/dev/loop1')
        print result

    def test_is_not_looped(self):
        self.stubs.Set(putils, 'execute', self.fake_loop_list)
        result = blockservice.is_looped('/dev/loop3')
        print result


    def test_linkloop(self):
        self.stubs.Set(os.path, 'exists', lambda x: True)
        blockservice.linkloop('/dev/loop1', '/block/img.blk')
        print self.cmds

    def test_unlinkloop(self):
        self.stubs.Set(blockservice, 'is_looped', lambda x: True)
        blockservice.unlinkloop('/dev/loop1')
        print self.cmds

