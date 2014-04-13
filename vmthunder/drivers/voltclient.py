
from oslo.config import cfg
from voltclient.v1 import client

from vmthunder.singleton import SingleTon

master_opts = [
    cfg.StrOpt('master_ip',
               default='10.107.14.170',
               help='Master\'s ip to provide Voltclient service'),
    cfg.StrOpt('master_port',
               default='7447',
               help='Master\'s port to provide Voltclient service'),
]
CONF = cfg.CONF
CONF.register_opts(master_opts)

@SingleTon
class VoltClient(client.Client):
    def __init__(self):
        client.Clien.__init__(self, 'http://%s:%s' % (CONF.master_ip, CONF.master_ip))


volt_client = VoltClient()


def login(session_name, peer_id, host, port, iqn, lun):
    return volt_client.volumes.login(session_name, peer_id, host, port, iqn, lun)


def get(session_name, host):
    return volt_client.volumes.get(session_name, host)


def logout(session_name, peer_id):
    return volt_client.volumes.logout(session_name, peer_id)