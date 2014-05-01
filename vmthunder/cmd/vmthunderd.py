#!/usr/bin/env python

import sys
import threading
import time

from oslo.config import cfg

from vmthunder import compute
from vmthunder.openstack.common import log as logging

#TODO: Auto determine host ip if not filled in conf file

CONF = cfg.CONF

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

if __name__ == '__main__':
    CONF(sys.argv[1:], project='vmthunder',
         default_config_files = ['/root/packages/VMThunder/etc/vmthunder/vmthunder.conf'])
    logging.setup('vmthunder')
    start()
