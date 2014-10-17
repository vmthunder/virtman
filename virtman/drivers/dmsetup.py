from pydm import dmsetup
from pydm.blockdev import Blockdev

from virtman.utils import singleton
from virtman.utils import rootwrap


class DmExecutor(dmsetup.Dmsetup):
    def __init__(self):
        dmsetup.Dmsetup.__init__(self, root_helper=rootwrap.root_helper())


dm = DmExecutor()
prefix = dm.mapdev_prefix


def remove_table(name):
    return dm.remove_table(name)


def reload_table(name, table):
    return dm.reload_table(name, table)


def multipath(name, disks):
    return dm.multipath(name, disks)


def reload_multipath(name, disks):
    blk = Blockdev(root_helper=rootwrap.root_helper())
    size = blk.get_sector_count(disks[0])
    multipath_table = '0 %d multipath 0 0 1 1 queue-length 0 %d 1 ' % (size, len(disks))
    for disk in disks:
        multipath_table += disk + ' 128 '
    multipath_table += '\n'
    reload_table(name, multipath_table)


def origin(origin_name, origin_dev):
    return dm.origin(origin_name, origin_dev)


def snapshot(origin_path, snapshot_name, snapshot_dev):
    return dm.snapshot(origin_path, snapshot_name, snapshot_dev)
