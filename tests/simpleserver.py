#!/usr/bin/env python

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

from vmthunder.compute import VMThunderCompute


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2')


class SimpleCompute(object):

    @staticmethod
    def create(instance_name, image_name, target_portal, target_iqn, target_lun, snapshot_dev):
        image_connection = {
            'target_portal': target_portal,
            'target_iqn': target_iqn,
            'target_lun': target_lun,
        }
        cn = VMThunderCompute(openstack_compatible=False)
        cn.create(instance_name, image_name, image_connection, snapshot_dev)

    @staticmethod
    def destroy(instance_name):
        cn = VMThunderCompute(openstack_compatible=False)
        cn.destroy(instance_name)

server = SimpleXMLRPCServer(("0.0.0.0", 7774), RequestHandler, allow_none=True)
server.register_introspection_functions()
server.register_instance(SimpleCompute)
server.serve_forever()
