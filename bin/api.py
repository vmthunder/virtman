#!/usr/bin/env python

import os
import sys

from webob import Request
from webob import Response
from vmthunder.singleton import get_instance

sys.path.append("..")
from vmthunder import compute

class ComputeApplication:
    compute_ins = compute.get_compute()
    def __call__(self, *args, **kwargs):
        return NotImplementedError()
    @classmethod
    def factory(cls, global_conf, **kwargs):
        return NotImplementedError()

class start_vm(ComputeApplication):
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
        return start_vm()

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
 
