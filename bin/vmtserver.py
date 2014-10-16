#!/usr/bin/env python

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

from vmthunder.compute import VMThunderCompute


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class SimpleCompute(object):

    @staticmethod
    def create(instance_name, image_name, image_connection, snapshot_dev):
        cn = VMThunderCompute(openstack_compatible=False)
        return cn.create(instance_name, image_name, image_connection, snapshot_dev)

    @staticmethod
    def destroy(instance_name):
        cn = VMThunderCompute(openstack_compatible=False)
        return cn.destroy(instance_name)

    @staticmethod
    def list():
        cn = VMThunderCompute(openstack_compatible=False)
        return cn.list()

    @staticmethod
    def create_image_target(image_name, file_path, loop_dev, iqn_prefix):
        cn = VMThunderCompute(openstack_compatible=False)
        return cn.create_image_target(image_name, file_path, loop_dev, iqn_prefix)

    @staticmethod
    def destroy_image_target(image_name):
        cn = VMThunderCompute(openstack_compatible=False)
        return cn.destroy_image_target(image_name)


server = SimpleXMLRPCServer(("0.0.0.0", 7774), RequestHandler, allow_none=True)
server.register_introspection_functions()
server.register_instance(SimpleCompute)
server.serve_forever()
