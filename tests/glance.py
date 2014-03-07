
from oslo.config import cfg
common_opts = [
    cfg.StrOpt('bind_host',  
                default='0.0.0.0',  
                help='IP address to listen on'),  
    cfg.IntOpt('bind_port',  
                default=9292,  
                help='Port number to listen on')  
]  


conf = cfg.CONF
conf.register_opts(common_opts)

print conf.bind_port

conf(default_config_files='glance.conf')  

def start(server, app):  
    server.start(app, CONF.bind_port, CONF.bind_host)


