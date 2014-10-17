from libfcg.fcg import FCG
from oslo.config import cfg

from virtman.utils import singleton
from virtman.utils import rootwrap

fcg_opts = [
    cfg.StrOpt('fcg_name',
               default='fcg',
               help='The name of the Flashcache Group'),
    cfg.ListOpt('fcg_ssds',
                default=['/dev/loop0'],
                help='The devices of SSDs to use to create the FCG, '
                     'the parameter of \'ssds\' can fill in one '
                     'or more, splited by \',\''),
    cfg.StrOpt('fcg_blocksize',
               default='4k',
               help='The block size of the FCG'),
    cfg.StrOpt('fcg_pattern',
               default='back',
               help='The cache mode for the FCG'),
]
CONF = cfg.CONF
CONF.register_opts(fcg_opts)


class FcgExecutor(FCG):
    def __init__(self):
        FCG.__init__(self, CONF.fcg_name, root_helper=rootwrap.root_helper())


fcg_executor = FcgExecutor()


def is_valid():
    return fcg_executor.is_valid()


def create_group():
    return fcg_executor.create_group(CONF.fcg_ssds, CONF.fcg_blocksize, CONF.fcg_pattern)


def add_disk(disk):
    return fcg_executor.add_disk(disk)


def rm_disk(disk):
    return fcg_executor.rm_disk(disk)

