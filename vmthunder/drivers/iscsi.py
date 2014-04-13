
from brick.iscsi.iscsi import TgtAdm

from vmthunder.singleton import SingleTon


@SingleTon
class TgtExecutor(TgtAdm):
    def __index__(self, root_helper='', volumes_dir= '/etc/tgt/conf.d'):
        TgtAdm.__init__(self, root_helper, volumes_dir)

tgt = TgtExecutor()


def create_iscsi_target(iqn, path):
    return tgt.create_iscsi_target(iqn, '', '', path)


def remove_iscsi_target(tid, lun, vol_id, vol_name, **kwargs):
    return tgt.remove_iscsi_target(tid, lun, vol_id, vol_name, **kwargs)