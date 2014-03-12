#!/usr/bin/env python

from vmthunder import api
from vmthunder.openstack.cinder import wsgi

class WSGIService(object):
    def __init__(self, name, host='0.0.0.0', port=0, loader=None):
        self.name = name
        #self.loader = loader or wsgi.Loader()
        #self.app = self.loader.load_app(name)
        self.host = host
        self.port = port
        self.server = wsgi.Server(name,
                                  api,
                                  host=self.host,
                                  port=self.port)
    def start(self):
        self.server.start()
        self.port = self.server.port
    def stop(self):
        self.server.stop()
    def wait(self):
        self.server.wait()
