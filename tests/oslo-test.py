from oslo.config import cfg

CONF = cfg.CONF

CONF(default_config_files=["a.cfg"])

print CONF.name
print CONF.cinder.host

CONF.register_opt(cfg.StrOpt('name', default='222'))
CONF.register_opt(cfg.StrOpt('host', default = 'adsfas'), group='cinder')

print CONF.name
print CONF.cinder.host


#CONF(default_config_files=["a.cfg"])

print CONF.name
print CONF.cinder.host

#print CONF._get_config_dirs()

