from eventlet import wsgi
import eventlet

def hello_world(environ, start_response):
    start_response('200 0K', [('Content-Type', 'text/plain')])
    return ['Hello World']

wsgi.server(eventlet.listen('', 8001), hello_world)
