#!/usr/bin/env python
#!/usr/bin/env python

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

from vmthunder.compute import Compute


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2')


class SimpleCompute(object):
    @staticmethod
    def create(volume_name, vm_name, target_portal, target_iqn, target_lun, snapshot_dev):
        image_connection = {
            'target_portal' : target_portal,
            'target_iqn' : target_iqn,
            'target_lun' : target_lun,
        }
        cn = Compute()
        cn.create(volume_name, vm_name, image_connection, snapshot_dev)

    @staticmethod
    def destroy(vm_name):
        cn = Compute()
        cn.destroy(vm_name)

server = SimpleXMLRPCServer(("0.0.0.0", 7774), RequestHandler, allow_none=True)
server.register_introspection_functions()
server.register_instance(SimpleCompute)
server.serve_forever()
