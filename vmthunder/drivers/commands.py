
from vmthunder.openstack.common import processutils as putils
from vmthunder.drivers import rootwrap


def execute(*cmd, **kwargs):
    return putils.execute(*cmd, **kwargs)


def unlink(path):
    return execute('rm', '-f', path, run_as_root=True, root_helper=rootwrap.root_helper())


def link(src, dst):
    return execute('ln', '-s', src, dst, run_as_root=True, root_helper=rootwrap.root_helper())