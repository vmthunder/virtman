#!/usr/bin/env python

import types

from oslo.config import cfg

class GetConf(object):

    opts = [
    
    ]

    fcg_group = cfg.OptGroup(name = 'fcg')
    fcg_opts = [
        cfg.StrOpt('name', default = 'fcg'),
        cfg.ListOpt('ssds', default = ['/dev/bala']),
        cfg.StrOpt('blocksize', default = '4k'),
        cfg.StrOpt('pattern', default = 'back')
    ]   
    
    master_group = cfg.OptGroup(name = 'master')
    master_opts = [
        cfg.StrOpt('ip', default = 'None'),
        cfg.StrOpt('port', default = 'None')
    ]
    
    cinder_group = cfg.OptGroup(name = 'cinder')
    cinder_opts = [
        cfg.StrOpt('ip', default = 'None'),
        cfg.StrOpt('port', default = 'None')
    ]

    conf = cfg.CONF

    def __init__(self, config_names):
        if type(config_names) is types.StringType:
            config_names = [ config_names ]
        self.conf(default_config_files = config_names)
        self._add_common_opts(self.opts)
        self._add_fcg_opts(self.fcg_opts, self.fcg_group)
        self._add_master_opts(self.master_opts, self.master_group)
        self._add_cinder_opts(self.cinder_opts, self.cinder_group)

    def _add_common_opts(self, opts):
        self.conf.register_opts(opts)

    def _add_fcg_opts(self, fcg_opts, fcg_group):
        self.conf.register_group(fcg_group)
        self.conf.register_opts(fcg_opts, group = fcg_group)

    def _add_master_opts(self, master_opts, master_group):
        self.conf.register_group(master_group)
        self.conf.register_opts(master_opts, group = master_group)

    def _add_cinder_opts(self, cinder_opts, cinder_group):
        self.conf.register_group(cinder_group)
        self.conf.register_opts(cinder_opts, group = cinder_group)

    def get_fcg_name(self):
        return self.conf.fcg.name
    
    def get_fcg_ssds(self):
        return self.conf.fcg.ssds

    def get_fcg_blocksize(self):
        return self.conf.fcg.blocksize

    def get_fcg_pattern(self):
        return self.conf.fcg.pattern 

    def get_master_ip(self):
        return self.conf.master.ip

    def get_master_port(self):
        return self.conf.master.port

    def get_cinder_ip(self):
        return self.conf.cinder.ip

    def get_cinder_port(self):
        return self.conf.cinder.port

if __name__ == "__main__" :
    a = GetConf('../etc/vmthunder/vmthunder.conf')

    print a.get_fcg_name()
    print a.get_fcg_ssds()
    print a.get_fcg_blocksize()
    print a.get_fcg_pattern()

    print a.get_master_ip()
    print a.get_master_port()

    print a.get_cinder_ip()
    print a.get_cinder_port()

