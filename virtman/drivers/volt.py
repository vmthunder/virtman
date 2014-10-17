#!/usr/bin/env python

import threading

from oslo.config import cfg
from voltclient.v1 import client


master_opts = [
    cfg.StrOpt('master_ip',
               default='192.168.137.101',
               help='Master\'s ip to provide Voltclient service'),
    cfg.StrOpt('master_port',
               default='7447',
               help='Master\'s port to provide Voltclient service'),
]
CONF = cfg.CONF
CONF.register_opts(master_opts)


def singleton(cls):
    lock = threading.Lock()
    instances = {}
    def _singleton(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return _singleton


@singleton
class VoltClient(client.Client):
    def __init__(self):
        client.Client.__init__(self, 'http://%s:%s' % (CONF.master_ip, CONF.master_port))


def login(session_name, peer_id, host, port, iqn, lun):
    volt_client = VoltClient()
    return volt_client.volumes.login(session_name=session_name,
                                     peer_id=peer_id,
                                     host=host,
                                     port=port,
                                     iqn=iqn,
                                     lun=lun)


def logout(session_name, peer_id):
    volt_client = VoltClient()
    return volt_client.volumes.logout(session_name, peer_id=peer_id)


def get(session_name, host):
    volt_client = VoltClient()
    return volt_client.volumes.get(session_name=session_name, host=host)


def heartbeat():
    volt_client = VoltClient()
    return volt_client.members.heartbeat()

