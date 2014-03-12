import os
import sys
import cgi
import cgitb


print os.environ

environ = {}
environ['REQUEST_METHOD'] = os.environ['REQUEST_METHOD'] 
environ['SCRIPT_NAME'] = os.environ['SCRIPT_NAME']  
environ['PATH_INFO'] = os.environ['PATH_INFO']  
environ['QUERY_STRING'] = os.environ['QUERY_STRING']  
environ['CONTENT_TYPE'] = os.environ['CONTENT_TYPE']  
environ['CONTENT_LENGTH'] = os.environ['CONTENT_LENGTH']  
environ['SERVER_NAME'] = os.environ['SERVER_NAME']  
environ['SERVER_PORT'] = os.environ['SERVER_PORT']  
environ['SERVER_PROTOCOL'] = os.environ['SERVER_PROTOCOL']  
environ['wsgi.version'] = (1, 0)  
environ['wsgi.url_scheme'] = 'http'  
environ['wsgi.input']        = sys.stdin  
environ['wsgi.errors']       = sys.stderr  
environ['wsgi.multithread']  = False  
environ['wsgi.multiprocess'] = True
environ['wsgi.run_once']     = True




class Router(object):
    def __init__(self):
        self.path_info = {}
    def route(self, environ, start_response):
        app = self.path_info[ environ['PATH_INFO'] ]
        return app(environ, start_response)
    def __call__(self, path):
        def wrapper(app):
            self.path_info[path] = app
        return wrapper

router = Router()

@router('/hello_app')
def hello_app(environ, start_response):
    body = ['%s: %s' %(key, value) for key, value in sorted(environ.items())]
    body = '\n'.join(body)
    status = '200 OK'
    headers = [('Content-Type', 'text/plain'),('Content-Length', str(len(body)))]
    start_response(status, headers)
    return ['Hello!!\n', body]

@router('/world_app')
def world_app(environ, start_response):
    output = 'hello'
    status = '200 OK'
    response_headers = [('Content-Type', 'text/plain'),
                        ('Content-Length', str(len(body)))]
    write = start_response(status, response_headers)
    return [ output ]

wsgi.server(eventlet.listen( ('0.0.0.0', 8040) ), hello_app)






result = router.route(environ, start_response)

for value in result:
    print(value)
