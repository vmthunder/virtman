
from virtman.openstack.common import processutils as putils
from virtman.utils import rootwrap


def execute(*cmd, **kwargs):
    return putils.execute(*cmd, **kwargs)

#Licyh NOTE: openstack.common.processutils & subprocess.Popen only supports 'ls' not 'cat a.py' but 'cat','a.py',
def unlink(path):
    return execute('rm', '-f', path, run_as_root=True, root_helper=rootwrap.root_helper())


def link(src, dst):
    return execute('ln', '-s', src, dst, run_as_root=True, root_helper=rootwrap.root_helper())