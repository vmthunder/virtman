from pydm import dmsetup

from vmthunder.singleton import SingleTon


@SingleTon
class DmExecutor(dmsetup.Dmsetup):
    def __init__(self):
        super(DmExecutor, self).__init__()

dm = DmExecutor()
prefix = dm.mapdev_prefix


def remove_table(name):
    return dm.remove_table(name)


def reload_table(name, table):
    return dm.reload_table(name, table)


def multipath(name, disks):
    return dm.multipath(name, disks)


def origin(origin_name, origin_dev):
    return dm.origin(origin_name, origin_dev)


def snapshot(origin_path, snapshot_name, snapshot_dev):
    return dm.snapshot(origin_path, snapshot_name, snapshot_dev)
