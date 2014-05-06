from oslo.config import cfg

rootwrap_opts = [
    cfg.StrOpt('root_helper',
               default='sudo nova-rootwrap /etc/nova/rootwrap.conf',
               help='root helper for none-root users'),
]

CONF = cfg.CONF
CONF.register_opts(rootwrap_opts)


def root_helper():
    return CONF.root_helper