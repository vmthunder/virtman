#!/usr/bin/env python

import sys

from oslo.config import cfg

from vmthunder import compute
from vmthunder.common import wsgi
from vmthunder.openstack.common import log as logging

#TODO: Auto determine host ip if not filled in conf file
host_opts = [
    cfg.StrOpt('host_ip',
               default='10.107.14.170',
               help='localhost ip provide VMThunder service'),
    cfg.StrOpt('host_port',
               default='8001',
               help='localhost port to provide VMThunder service'),
]
CONF = cfg.CONF
CONF.register_opts(host_opts)

def start():
    cn = compute.Compute()
    server = wsgi.Server('vmthunder-api', path='/root/develop/VMThunder/etc/vmthunder/api-paste.ini') #or path = ${a specified path} like '/root/VMThunder/etc/api-paste.ini'
    server.start()
    server.wait()

if __name__ == '__main__':
    CONF(sys.argv[1:], project='vmthunder',
         default_config_files = ['../etc/vmthunder.conf'])
    #print CONF.fcg_name, CONF.fcg_ssds, CONF.fcg_blocksize, CONF.fcg_pattern
    logging.setup('vmthunder')
    start()
