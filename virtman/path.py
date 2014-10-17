
from virtman.drivers import connector

from virtman.openstack.common import log as logging


LOG = logging.getLogger(__name__)

iscsi_disk_format = "ip-%s-iscsi-%s-lun-%s"


def connection_to_str(connection):
    return iscsi_disk_format % (connection['target_portal'], connection['target_iqn'], connection['target_lun'])


class Path(object):

    def __init__(self, connection):
        self.connection = connection
        self.connected = False
        self.device_info = None
        self.device_path = ''

    def __str__(self):
        return connection_to_str(self.connection)

    def connect(self):
        self.device_info = connector.connect_volume(self.connection)
        self.device_path = self.device_info['path']
        print "Virtman: Path OK!  device_path = ", self.device_path
        self.connected = True
        LOG.debug("Virtman: connect to path: %s", str(self))
        return self.device_path

    def disconnect(self):
        connector.disconnect_volume(self.connection, self.device_info)
        self.connected = False
        LOG.debug("Virtman: disconnect to path: %s", str(self))

