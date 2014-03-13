#!/usr/bin/env python

#from vmthunder.api import hello_wsgi
from vmthunder import wsgi

class APIService(object):
    def __init__(self, name, host='0.0.0.0', port=8001, loader=None):
        self.name = name
        self.loader = loader or wsgi.Loader('/root/VMThunder/vmthunder/api-paste.ini')
        self.app = self.loader.load_app(name)
        self.host = host
        self.port = port
        self.server = wsgi.Server(name,
                                  self.app,
                                  host=self.host,
                                  port=self.port)
    def start(self):
        self.server.start()
        self.port = self.server.port
    def stop(self):
        self.server.stop()
    def wait(self):
        self.server.wait()
