#!/usr/bin/env python

import sys
from oslo.config import cfg

from vmthunder import compute
from vmthunder.common import wsgi
from vmthunder.openstack.common import log as logging

fcg_opts = [
    cfg.StrOpt('fcg_name',
               default='fcg',
               help='The name of the Flashcache Group'),
    cfg.ListOpt('fcg_ssds',
                default=['/dev/loop1'],
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

master_opts = [
    cfg.StrOpt('master_ip',
               default='10.107.14.170',
               help='Master\'s ip to provide Voltclient service'),
    cfg.StrOpt('master_port',
               default='7447',
               help='Master\'s port to provide Voltclient service'),
]

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
CONF.register_opts(fcg_opts)
CONF.register_opts(master_opts)
CONF.register_opts(host_opts)

def start():
    cn = compute.Compute(CONF.fcg.name, CONF.fcg.ssds, CONF.fcg.blocksize, CONF.fcg.pattern)
    server = wsgi.Server('vmthunder-api', path='/root/develop/VMThunder/etc/vmthunder/api-paste.ini') #or path = ${a specified path} like '/root/VMThunder/etc/api-paste.ini'
    server.start()
    server.wait()

if __name__ == '__main__':
    CONF(sys.argv[1:], project='vmthunder',
         default_config_files = ['../etc/vmthunder.conf'])
    #print CONF.fcg_name, CONF.fcg_ssds, CONF.fcg_blocksize, CONF.fcg_pattern
    logging.setup('vmthunder')
    start()
