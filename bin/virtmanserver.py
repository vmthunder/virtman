#!/usr/bin/env python
import sys

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from oslo.config import cfg

from virtman.utils.singleton import singleton
from virtman.compute_new import Virtman
from virtman import imageservice
from virtman.openstack.common import log as logging

CONF = cfg.CONF

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


@singleton
class SimpleCompute(object):
    def __init__(self):
        self.cn = Virtman(openstack_compatible=False)

    def create(self, instance_name, image_name, image_connection, snapshot_dev):
        return self.cn.create(instance_name, image_name, image_connection,
                              snapshot_dev)

    def destroy(self, instance_name):
        return self.cn.destroy(instance_name)

    def list(self):
        return self.cn.list()

    @staticmethod
    def create_image_target(image_name, file_path, loop_dev, iqn_prefix):
        return imageservice.create_image_target(image_name, file_path, loop_dev,
                                                iqn_prefix)

    @staticmethod
    def destroy_image_target(image_name):
        return imageservice.destroy_image_target(image_name)

    @staticmethod
    def list_image_target():
        return imageservice.list_image_target()

if __name__ == '__main__':
    CONF(sys.argv[1:], project='virtman',
         default_config_files=['/etc/virtman/virtman.conf'])
    logging.setup('virtman')
    server = SimpleXMLRPCServer(("0.0.0.0", 7774), RequestHandler,
                                allow_none=True)
    server.register_introspection_functions()
    sc = SimpleCompute()
    server.register_instance(sc)
    print "Virtman Server Run ..."
    server.serve_forever()
