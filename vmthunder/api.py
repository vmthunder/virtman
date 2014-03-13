#!/usr/bin/env python


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
