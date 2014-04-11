from libfcg.fcg import FCG
from oslo.config import cfg
from vmthunder.singleton import SingleTon

CONF = cfg.CONF

@SingleTon
class FcgExecutor(FCG):
    def __init__(self):
        super(FcgExecutor, self).__init__(CONF.fcg_name)

fcg_executor = FcgExecutor()


def create_group(ssds, block_size, pattern):
    return fcg_executor.create_group(ssds, block_size, pattern)


def add_disk(disk):
    return fcg_executor.add_disk(disk)


def rm_disk(disk):
    return fcg_executor.rm_disk(disk)