#!/usr/bin/env python

import os
import webob
from webob import Request
from webob import Response

class Hello():
    def __init__(self):
        pass
    def __call__(self, environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type','text/plain')]
        start_response(status, response_headers)
        return ['Hello World!\n']
    @classmethod
    def factory(cls, global_conf, **kwargs):
        print 'in Hello.factory', global_conf, kwargs
        return Hello()

class ShowVersion():
    def __init__(self):
        pass
    def __call__(self, environ, start_response):
        start_response("200 OK",[("Content-type", "text/plain")])  
        return ["Paste Deploy LAB: Version = 1.0.0",]  
    @classmethod  
    def factory(cls, global_conf, **kwargs):  
        print "in ShowVersion.factory", global_conf, kwargs  
        return ShowVersion()
 
class Calculator():  
    def __init__(self):  
        pass  
    def __call__(self, environ, start_response):  
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
        print "in Calculator.factory", global_conf, kwargs  
        return Calculator()  

if __name__ == '__main__':
    from paste.deploy import loadapp
    from wsgiref.simple_server import make_server
    config_file = 'api-paste.ini'
    app_name = 'all'
    wsgi_app = loadapp('config:%s' %os.path.abspath(config_file), app_name)
    server = make_server('localhost', 8080, wsgi_app)
    server.serve_forever()

'''
def hello_wsgi(environ, start_response):
    """Simple WSGI application"""
    status = '200 OK'
    response_headers = [('Content-type','text/plain')]
    start_response(status, response_headers)
    return ['Hello world!\n']

def app_factory(global_config, **local_config):
    """This function wraps our simple WSGI app so it
    can be used with paste.deploy"""
    return hello_wsgi
'''
