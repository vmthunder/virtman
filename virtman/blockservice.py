#!/usr/bin/env python

import os

from virtman.utils import rootwrap

from virtman.openstack.common import log as logging
from openstack.common import processutils as putils

LOG = logging.getLogger(__name__)


def findloop():
    # Licyh NOTE: openstack.common.processutils & subprocess.Popen only
    # supports 'ls' not 'cat a.py' but 'cat','a.py',
    (out, err) = putils.execute('losetup', '-f', run_as_root=True,
                                root_helper=rootwrap.root_helper())
    return out.strip()


def try_linkloop(loop_dev):
    path = '/root/blocks/'
    if not os.path.exists(path):
        putils.execute('mkdir', '-p', path, run_as_root=True,
                       root_helper=rootwrap.root_helper())
    path = path + 'snap' + loop_dev[9:] + '.blk'
    if not os.path.exists(path):
        putils.execute('dd', 'if=/dev/zero', 'of=' + path, 'bs=1M', 'count=512',
                       run_as_root=True, root_helper=rootwrap.root_helper())
    linkloop(loop_dev, path)


def is_looped(loop_dev):
    (out, err) = putils.execute("losetup", '-a', run_as_root=True,
                                root_helper=rootwrap.root_helper())
    looped_list = [line.split()[0].rstrip(":")
                   for line in out.strip().split('\n')]
    if loop_dev in looped_list:
        return True
    return False
    # try:
    #     putils.execute("losetup", loop_dev, run_as_root=True,
    #                    root_helper=rootwrap.root_helper())
    # except putils.ProcessExecutionError:
    #     return False
    # else:
    #     return True


def linkloop(loop_dev, path):
        putils.execute('losetup', loop_dev, path,
                       run_as_root=True, root_helper=rootwrap.root_helper())


def unlinkloop(loop_dev):
    if is_looped(loop_dev):
        putils.execute('losetup', '-d', loop_dev,
                       run_as_root=True, root_helper=rootwrap.root_helper())
