#!/usr/bin/env python

import requests
#import json
from virtman.openstack.common import jsonutils


class Client(object):

    USER_AGENT = 'python-virtmanclient'

    def __init__(self, name='virtman'):
        self.name = name

    def requests(self, url, method, **kwargs):
        resp = requests.request(method, url, **kwargs)
        #body = json.loads(resp.text) 
        body = 'Is Body'
        return resp, body
             
    def get(self, url, **kwargs):
        return self.requests(url, 'GET', **kwargs) 
    
    def post(self, url, **kwargs):
        return self.requests(url, 'POST', **kwargs)
    
    def put(self, url, **kwargs):
        return self.requests(url, 'PUT', **kwargs)
    
    def delete(self, url, **kwargs):
        return self.requests(url, 'DELETE', **kwargs)

def test4():
    url4 = 'http://127.0.0.1:8001/list'
    r4 = requests.get(url4)
    print r4.headers, '\n', r4.content

    url5 = 'http://127.0.0.1:8001/create'

    body = {
        'image_id':'123456',
        'vm_name':'vm6',
        'connections':[],
        'snapshot_dev':'/dev/loop8'
    }
    kwargs = {}
    kwargs.setdefault('headers', kwargs.get('headers', {}))
    kwargs['headers']['Accept'] = 'application/json'
    kwargs['headers']['Content-Type'] = 'application/json'
    kwargs['body'] = jsonutils.dumps(body)

    r5 = requests.request('POST', url5, kwargs)
    print r5.headers, '\n', r5.content

    url6 = 'http://127.0.0.1:8001/destroy'

    body = {
        'vm_name': 'vm6'
    }
    kwargs = {}
    kwargs.setdefault('headers', kwargs.get('headers', {}))
    kwargs['headers']['Accept'] = 'application/json'
    kwargs['headers']['Content-Type'] = 'application/json'
    kwargs['body'] = jsonutils.dumps(body)
    r6 = requests.request('POST', url6, kwargs)
    print r6.headers, '\n', r6.content


def test1():
    c = Client()
    url = 'http://10.107.14.50:8041'
    print c.get(url)
    print c.post(url)
    print c.put(url)
    print c.delete(url)

def test2():

    url1 = 'http://127.0.0.1:8001'
    url2 = 'http://127.0.0.1:8001/show'
    url3 = 'http://127.0.0.1:8001/calc?operator=plus&operand1=12&operand2=23'

    r1 = requests.get(url1)
    r2 = requests.get(url2)
    r3 = requests.get(url3)

    print '\r'

    print r1.headers, '\n', r1.text
    print r2.headers, '\n', r2.text
    print r3.headers, '\n', r3.text, '\n'

    print requests.post(url1).content
    print requests.post(url2).text
    print requests.post(url3).text
    
    #import webob
    #from webob import Response
    #r = Response()
    #r = requests.get(url3)
    #print r

def test3():
    url2 = 'http://127.0.0.1:8001/show'
    r2 = requests.get(url2)
    print r2.headers, '\n', r2.content

    url3 = 'http://127.0.0.1:8001/calc?operator=plus&operand1=12&operand2=23'
    r3 = requests.get(url3)
    print r3.headers, '\n', 
    print jsonutils.loads(r3.content)
'''
    url = 'http://127.0.0.1:8001/start?image_id=image-100&vm_name=vm-200&connections=ss'
    r = requests.get(url)
    print r.headers
    print r.text
'''


if __name__ == '__main__' :
    #test1()
    #test2()
    #test3()
    test4()





