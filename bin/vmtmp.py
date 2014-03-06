#!/usr/bin/env python

import sys
sys.path.append("..")

#from oslo.config import cfg
from libfcg.fcg import FCG
from vmthunder.computenode import ComputeNode
from vmthunder.getconf import GetConf




from eventlet import wsgi
import eventlet

def hello_world(environ, start_response):
    start_response('200 0k', ['Content-Type', 'text/plain'])
    return ['Hello World!']

wsgi.server(eventlet.listen('', 8090), hello_world)



def main():
    gc = GetConf('../etc/vmthunder/vmthunder.conf')
    name = gc.get_fcg_name()
    ssds = gc.get_fcg_ssds()
    blocksize = gc.get_fcg_blocksize()
    pattern = gc.get_fcg_pattern()
    #print name, ssds, blocksize, pattern
    
    fcg = FCG(name)
    fcg.create_group(ssds, blocksize, pattern)

if __name__ == '__main__':
    #main()   
