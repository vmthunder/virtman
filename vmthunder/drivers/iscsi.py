
import os

from brick.iscsi.iscsi import TgtAdm

from vmthunder.singleton import singleton


@singleton
class TgtExecutor(TgtAdm):
    def __index__(self, root_helper='', volumes_dir= '/etc/tgt/conf.d'):
        TgtAdm.__init__(self, root_helper, volumes_dir)

tgt = TgtExecutor('', '/etc/tgt/conf.d')


def create_iscsi_target(iqn, path):
    return tgt.create_iscsi_target(iqn, '', '', path)


def remove_iscsi_target(tid, lun, vol_id, vol_name, **kwargs):
    return tgt.remove_iscsi_target(tid, lun, vol_id, vol_name, **kwargs)


def exists(iqn):
    return tgt.exist(iqn)


def is_connected(target_id):
    """This method is to judge whether a target is hanging by other VMs"""
    #TODO: try to call brick.iscsi
    cmd = "tgtadm --lld iscsi --mode conn --op show --tid " + str(target_id)
    tmp = os.popen(cmd).readlines()
    if len(tmp) == 0:
        return False
    return True
