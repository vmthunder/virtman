#!/usr/bin/env python

import sys
sys.path.append("..")

#from oslo.config import cfg
from libfcg.fcg import FCG
from vmthunder.computenode import ComputeNode
from vmthunder.getconf import GetConf
import eventlet
from eventlet import wsgi
#from wsgi import Server


def hello_app(environ, start_response):
    body = ['%s: %s' %(key, value) for key, value in sorted(environ.items())]
    body = '\n'.join(body)
    status = '200 OK'
    headers = [('Content-Type', 'text/plain'),('Content-Length', str(len(body)))]
    start_response(status, headers)
    return ['Hello!!\n', body]

def service():
    wsgi.server(eventlet.listen( ('0.0.0.0', 8040) ), hello_app)

def main():
    gc = GetConf('../etc/vmthunder/vmthunder.conf')
    name = gc.get_fcg_name()
    ssds = gc.get_fcg_ssds()
    blocksize = gc.get_fcg_blocksize()
    pattern = gc.get_fcg_pattern()
    #print name, ssds, blocksize, pattern
    
    fcg = FCG(name)
    fcg.create_group(ssds, blocksize, pattern)


class Manager(object):

    def run_command(self, cmd, **kwargs):
        f = self.get_command(cmd)
        return f(**kwargs)

    def get_command(self, cmd):
        cmd = cmd.lower.replace('-', '_')
        func = getattr(self, cmd)
        return func

    def start(self, **kwargs):
        

    def stop(self, **kwargs):

    def restart(self, **kwargs):       
















if __name__ == '__main__':
    #main()
    service()   
