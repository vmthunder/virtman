# -*- coding: utf-8 -*-
import mock
import os
import string

from tests import base
from oslo_concurrency import processutils as putils
from virtman import blockservice


class TestBlockService(base.TestCase):
    def setUp(self):
        super(TestBlockService, self).setUp()
        self.cmds = []
        self.mock_object(putils, 'execute',
                         mock.Mock(side_effect=self.fake_execute))

    def fake_execute(self, *cmd, **kwargs):
        self.cmds.append(string.join(cmd))
        return "", None

    def exists_side_effect(self, false_times):
        count = [0]
        max_times = [false_times]

        def counter_and_return(*arg):
            count[0] += 1
            if count[0] > max_times[0]:
                return True
            return False

        return counter_and_return

    def fake_loop_list(self, *cmd, **kwargs):
        return """/dev/loop0: [8010]:264910 (/block/image0)
        /dev/loop1: [8010]:264910 (/block/image1)""", None

    def test_findloop(self):
        expected_commands = ['losetup -f']
        blockservice.findloop()
        self.assertEqual(expected_commands, self.cmds)

    def test_try_linkloop(self):
        expected_commands = ['mkdir -p /root/blocks/',
                             'dd if=/dev/zero of='
                             '/root/blocks/snap1.blk bs=1M count=512',
                             'losetup /dev/loop1 /root/blocks/snap1.blk']
        exists_side_effect = self.exists_side_effect(2)
        self.mock_object(os.path, 'exists',
                         mock.Mock(side_effect=exists_side_effect))
        blockservice.try_linkloop('/dev/loop1')
        self.assertEqual(expected_commands, self.cmds)

    def test_is_looped(self):
        self.mock_object(putils, 'execute',
                         mock.Mock(side_effect=self.fake_loop_list))
        result = blockservice.is_looped('/dev/loop1')
        self.assertEqual(True, result)

    def test_is_not_looped(self):
        self.mock_object(putils, 'execute',
                         mock.Mock(side_effect=self.fake_loop_list))
        result = blockservice.is_looped('/dev/loop3')
        self.assertEqual(False, result)

    def test_linkloop(self):
        expected_commands = ['losetup /dev/loop1 /block/img.blk']
        blockservice.linkloop('/dev/loop1', '/block/img.blk')
        self.assertEqual(expected_commands, self.cmds)

    def test_unlinkloop(self):
        expected_commands = ['losetup -d /dev/loop1']
        self.mock_object(blockservice, 'is_looped',
                         mock.Mock(side_effect=lambda x: True))
        blockservice.unlinkloop('/dev/loop1')
        self.assertEqual(expected_commands, self.cmds)

