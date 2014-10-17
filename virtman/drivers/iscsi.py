
from brick.iscsi.iscsi import TgtAdm

from virtman.utils import rootwrap
from virtman.utils import singleton

from virtman.openstack.common import processutils as putils

class TgtExecutor(TgtAdm):
    def __init__(self, root_helper='', volumes_dir='/etc/tgt/stack.d'):
        TgtAdm.__init__(self, root_helper, volumes_dir)


tgt = TgtExecutor(rootwrap.root_helper(), '/etc/tgt/stack.d')


def create_iscsi_target(iqn, path):
    # params included (iqn  tid  lun  path) but (tid lun) not need for tgt to create target
    return tgt.create_iscsi_target(iqn, '', '', path)


def remove_iscsi_target(vol_id, vol_name):
    return tgt.remove_iscsi_target('', '', vol_id, vol_name)


def exists(iqn):
    return tgt.exist(iqn)


def is_connected(target_id):
    """This method is to judge whether a target is hanging by other VMs"""
    #TODO: try to call brick.iscsi
    #cmd = "tgtadm --lld iscsi --mode conn --op show --tid " + str(target_id)
    (output, error) = putils.execute("tgtadm", '--lld', 'iscsi', '--mode', 'conn', '--op', 'show', '--tid',
                                     str(target_id), run_as_root=True, root_helper=rootwrap.root_helper())
    if len(output) == 0:
        return False
    return True
