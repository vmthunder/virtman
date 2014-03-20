#!/usr/bin/env python

import os
import webob
from webob import Request
from webob import Response

import sys
sys.path.append("..")
from vmthunder.computenode import ComputeNode


cn = ComputeNode()

class Start():
    def __init__(self):
        pass
    def __call__(self, environ, start_response):
        req = Request(environ)
        res = Response()
        res.status = "200 OK"
        res.content_type = "text/plain"
        res.body = "%s had already started." % ('VM')
        
        image_id = req.GET.get("image_id", None)
        vm_name = req.GET.get("vm_name", None)
        connections = req.GET.get("connections", None)
        cn.start_vm(image_id, vm_name, connections)

        return res(environ, start_response)
    @classmethod
    def factory(cls, global_conf, **kwargs):
        return Start()

class Hello():
    def __init__(self):
        pass
    def __call__(self, environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type','text/plain')]
        start_response(status, response_headers)
        return ['Hello World!\r\n']
    @classmethod
    def factory(cls, global_conf, **kwargs):
        print 'in Hello.factory\r\n', global_conf, '\r\n', kwargs
        return Hello()

class ShowVersion():
    def __init__(self):
        pass
    def __call__(self, environ, start_response):
        print 'environ=', environ
        print 'start_response=', start_response 
        start_response("200 OK",[("Content-type", "text/plain")])  
        return ["Paste Deploy LAB: Version = 1.0.0\r\n",]  
    @classmethod  
    def factory(cls, global_conf, **kwargs):  
        print "in ShowVersion.factory\r\n", global_conf, '\r\n', kwargs  
        return ShowVersion()
 
class Calculator():  
    def __init__(self):  
        pass  
    def __call__(self, environ, start_response):  
        print 'environ=', environ
        print 'start_response=', start_response
        req = Request(environ)
        res = Response()
        # get operands  
        operator = req.GET.get("operator", None)  
        operand1 = req.GET.get("operand1", None)  
        operand2 = req.GET.get("operand2", None)  
        print req.GET
        opnd1 = int(operand1)  
        opnd2 = int(operand2)  
        if operator == u'plus':  
            opnd1 = opnd1 + opnd2  
        elif operator == u'minus':  
            opnd1 = opnd1 - opnd2  
        elif operator == u'star':  
            opnd1 = opnd1 * opnd2  
        elif operator == u'slash':  
            opnd1 = opnd1 / opnd2  
        res.status = "200 OK"  
        res.content_type = "text/plain"  
        res.body = "%s /nRESULT= %d" % (str(req.GET) , opnd1)  
        return res(environ, start_response)  
    @classmethod
    def factory(cls, global_conf, **kwargs):  
        print "in Calculator.factory\r\n", global_conf, '\r\n', kwargs  
        return Calculator()  


def th(server):
    server.serve_forever()

def _thread_done(gt, *args, **kwargs):
    """Callback function to be passed to GreenThread.link() when we spawn()
    Calls the :class:`ThreadGroup` to notify if.

    """
    kwargs['group'].thread_done(kwargs['thread'])

if __name__ == '__main__':
    from paste.deploy import loadapp
    from wsgiref.simple_server import make_server
    from eventlet import wsgi
    import eventlet
    import threading
    from multiprocessing import Process

    config_file = 'api-paste.ini'
    app_name = 'vmthunder-api'
    wsgi_app = loadapp('config:%s' %os.path.abspath(config_file), app_name)
    #wsgi.server(eventlet.listen(('0.0.0.0', 8001)), wsgi_app)
    #pool = eventlet.GreenPool()
    #thread = pool.spawn(wsgi.server(eventlet.listen(('0.0.0.0', 8001)), wsgi_app))
    #thread.link(_thread_done, thread)
    server = make_server('0.0.0.0', 8001, wsgi_app)

    p = threading.Thread(target=th, args=(server,))
    p.run()
    #p.daemon = True
    #p.start()
    #import time
    #time.sleep(5)   
 
