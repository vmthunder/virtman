#!/usr/bin/env python

import sys
import threading
import time

from oslo.config import cfg

from vmthunder import compute
from vmthunder.openstack.common import log as logging

#TODO: Auto determine host ip if not filled in conf file
host_opts = [
    cfg.StrOpt('host_ip',
               default='10.107.14.170',
               help='localhost ip provide VMThunder service'),
    cfg.StrOpt('host_port',
               default='8001',
               help='localhost port to provide VMThunder service'),
    cfg.IntOpt('heartbeat_interval',
               default=20,
               help='localhost heartbeat interval'),
]
CONF = cfg.CONF
CONF.register_opts(host_opts)


def start():
    cn = compute.Compute()

    class HeartBeater(threading.Thread):
        def __init__(self, thread_name):
            super(HeartBeater, self).__init__(name=thread_name)

        def run(self):
            def clock():
                LOG = logging.getLogger(__name__)
                LOG.debug("At %s heartbeat once" % time.asctime())
                cn.heartbeat()
                time.sleep(CONF.heartbeat_interval)
                #TODO: the max depth of recursion
                clock()
            clock()
    heartbeat = HeartBeater('heartbeat')
    heartbeat.start()

    #TODO:!!!
    server = wsgi.Server('vmthunder-api', path='/root/packages/VMThunder/etc/vmthunder/api-paste.ini') #or path = ${a specified path} like '/root/VMThunder/etc/api-paste.ini'
    server.start()
    server.wait()

if __name__ == '__main__':
    CONF(sys.argv[1:], project='vmthunder',
         default_config_files = ['/root/packages/VMThunder/etc/vmthunder/vmthunder.conf'])
    logging.setup('vmthunder')
    start()
