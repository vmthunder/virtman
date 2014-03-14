
import os
import eventlet

import launcher
from eventlet import wsgi
from paste import deploy

class APIService(object):
    
    def __init__(self, host='0.0.0.0', port=8001,
                       name='vmthunder-api',
                       config_path='/root/VMThunder/bin/api-paste.ini'):
        self.host = host
        self.port = port
        self.name = name
        self.config_path = config_path
        self.app = deploy.loadapp('config:%s' %os.path.abspath(self.config_path), self.name)
        self.pool = eventlet.GreenPool()
        self._server = None

    def _start(self):
        eventlet.wsgi.server( eventlet.listen((self.host, self.port)), self.app,
                              protocol= eventlet.wsgi.HttpProtocol, custom_pool = self.pool)
        #eventlet.wsgi.server( eventlet.listen((self.host, self.port)), self.app )

    def start(self):
        self._server = eventlet.spawn( self._start() )
        #self._server = self.pool.spawn( self._start() )

    def stop(self):
        if self._server is not None:
            self._pool.resize(0)
            self._server.kill()

    def wait(self):
        if self._server is not None:
            self._server.wait()

def process_launcher():
    return launcher.ProcessLauncher()


if __name__ == '__main__' :
    a = APIService()
    a.start()

