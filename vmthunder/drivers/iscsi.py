
from brick.iscsi.iscsi import TgtAdm

from vmthunder.singleton import SingleTon


@SingleTon
class TgtExecutor(TgtAdm):
    def __index__(self):
        TgtAdm.__init__(self, '', '/etc/tgt/conf.d')

tgt = TgtExecutor()


def create_iscsi_target(iqn, path):
    return tgt.create_iscsi_target(iqn, path)


def remove_iscsi_target(tid, lun, vol_id, vol_name, **kwargs):
    return tgt.remove_iscsi_target(tid, lun, vol_id, vol_name, **kwargs)