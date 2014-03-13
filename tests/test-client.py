#!/usr/bin/env python

import requests
#import json


class Client(object):

    USER_AGENT = 'python-vmthunderclient'

    def __init__(self, name='vmthunder'):
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

def test1():
    c = Client()
    url = 'http://10.107.14.50:8041'
    print c.get(url)
    print c.post(url)
    print c.put(url)
    print c.delete(url)

def test2():
    import webob
    from webob import Response
    url1 = 'http://127.0.0.1:8080'
    url2 = 'http://127.0.0.1:8080/show'
    url3 = 'http://127.0.0.1:8080/calc?operator=plus&operand1=12&operand2=23'
    print requests.get(url1)
    print requests.get(url2)
    print requests.get(url3).text
    print requests.post(url1)
    print requests.post(url2)
    print requests.post(url3).text

    r = requests.get(url3)
    print r.headers
    #print r.text
    print r.content

    r = Response()
    r = requests.get(url3)
    print r




if __name__ == '__main__' :
    #test1()
    test2()
