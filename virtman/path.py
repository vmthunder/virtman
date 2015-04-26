
from virtman.drivers import connector

from virtman.openstack.common import log as logging


LOG = logging.getLogger(__name__)

iscsi_disk_format = "ip-%s-iscsi-%s-lun-%s"


class Path(object):

    def __init__(self, connection):
        self.connection = connection
        self.connected = False
        self.device_info = None
        self.device_path = ''

    def __str__(self):
        return self.connection_to_str(self.connection)

    @staticmethod
    def connection_to_str(connection):
        return iscsi_disk_format % (connection['target_portal'],
                                    connection['target_iqn'],
                                    connection['target_lun'])

    @staticmethod
    def connect(path):
        path.device_info = connector.connect_volume(path.connection)
        path.device_path = path.device_info['path']
        path.connected = True
        LOG.debug("Virtman: connect to path: %s", str(path))
        return path.device_path

    @staticmethod
    def disconnect(path):
        connector.disconnect_volume(path.connection, path.device_info)
        path.connected = False
        LOG.debug("Virtman: disconnect to path: %s", str(path))

