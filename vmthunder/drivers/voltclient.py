
from oslo.config import cfg
from voltclient.v1 import client

from vmthunder.singleton import SingleTon

CONF = cfg.CONF

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