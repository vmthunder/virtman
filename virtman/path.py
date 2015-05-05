import time
from virtman.drivers import connector
from virtman.drivers import dmsetup
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
        """
        :type connection: dict
        """
        return iscsi_disk_format % (connection['target_portal'],
                                    connection['target_iqn'],
                                    connection['target_lun'])

    @staticmethod
    def connect(path):
        """
        :type path: Path
        """
        path.device_info = connector.connect_volume(path.connection)
        path.device_path = path.device_info['path']
        path.connected = True
        LOG.debug("Virtman: connect to path: %s", str(path))
        return path.device_path

    @staticmethod
    def disconnect(path):
        """
        :type path: Path
        """
        connector.disconnect_volume(path.connection, path.device_info)
        path.connected = False
        LOG.debug("Virtman: disconnect to path: %s", str(path))


class Paths(object):

    @staticmethod
    def _find_paths_to_remove(paths, parent_connections):
        """
        :type paths: dict
        :type parent_connections: list
        """
        paths_to_remove = []
        for key in paths.keys():
            found = False
            for connection in parent_connections:
                if key == Path.connection_to_str(connection):
                    found = True
                    break
            if not found:
                paths_to_remove.append(key)
        return paths_to_remove

    @staticmethod
    def _add_new_connection(paths, parent_connections):
        for connection in parent_connections:
            if not isinstance(connection, dict):
                raise (Exception("Unknown %s type of %s " %
                                 (type(connection), connection)))
            key = Path.connection_to_str(connection)
            if key not in paths:
                paths[key] = Path(connection)

    @staticmethod
    def rebuild_multipath(paths, parent_connections, multipath_name,
                          has_multipath):
        """
        :type paths: dict
        :type parent_connections: list
        :type multipath_name: str
        :type has_multipath: bool
        """
        LOG.debug("Virtman: begin to rebuild multipath...")

        # Get keys of paths to remove, and add new paths
        paths_to_remove = Paths._find_paths_to_remove(paths, parent_connections)
        Paths._add_new_connection(paths, parent_connections)

        # Connect new paths
        for key in paths.keys():
            if key not in paths_to_remove and not paths[key].connected:
                Path.connect(paths[key])

        # Rebuild multipath device
        disks = [paths[key].device_path for key in paths.keys()
                 if key not in paths_to_remove and paths[key].connected]

        multipath_path = None
        if len(disks) > 0:
            if not has_multipath:
                multipath_path = Paths.create_multipath(multipath_name, disks)
            else:
                multipath_path = has_multipath
                Paths.reload_multipath(multipath_name, disks)
            # TODO:fix here, wait for multipath device ready
            time.sleep(2)

        # Disconnect paths to remove
        for key in paths_to_remove:
            if paths[key].connected:
                Path.disconnect(paths[key])
            del paths[key]
        LOG.debug("Virtman: now multipath is %s" % multipath_path)
        return multipath_path

    @staticmethod
    def create_multipath(multipath_name, disks):
        """
        :type multipath_name: str
        :type disks: list
        :rtype : str
        """
        LOG.debug("Virtman: create multipath according connection %s:" %
                  disks)
        multipath_path = dmsetup.multipath(multipath_name, disks)
        return multipath_path

    @staticmethod
    def reload_multipath(multipath_name, disks):
        """
        :type multipath_name: str
        :type disks: list
        """
        LOG.debug("Virtman: reload multipath according connection %s:" %
                  disks)
        dmsetup.reload_multipath(multipath_name, disks)

    @staticmethod
    def delete_multipath(multipath_name):
        LOG.debug("Virtman: delete multipath %s start!" %
                  multipath_name)
        dmsetup.remove_table(multipath_name)
        LOG.debug("Virtman: delete multipath %s completed  !" %
                  multipath_name)
        return True
