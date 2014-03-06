#!/usr/bin/env/ python

from wsgiref.simple_server import make_server

def hello_world_app(environ, start_response):
    status = '200 0K'
    headers = [('Content-Type', 'text/plain')]
    print environ
    start_response(status, headers)
    return ['hello world']

httpd = make_server('', 8000, hello_world_app)

print "Serving on port 8000..."

httpd.serve_forever()
