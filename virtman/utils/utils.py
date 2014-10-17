
from virtman.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def reform_connections(connections):
    """
    :param connections: a tuple or list
    """
    if not (isinstance(connections, list) or isinstance(connections, tuple)):
        raise Exception('Virtman: Unknown connections type: connection: {0:s}, type: {1:s}'.format(
            connections, type(connections)))
    new_connections = []
    for connection in connections:
        new_connections.append(reform_connection(connection))
    return new_connections


def reform_connection(connection):
    """
    :return new_connection: a list includes 'target_portal', 'target_iqn' and 'target_lun'.
    """
    LOG.debug("old connection is :")
    LOG.debug(connection)
    if isinstance(connection, dict):
        new_connection = {'target_portal': connection['target_portal'],
                          'target_iqn': connection['target_iqn'],
                          'target_lun': connection['target_lun'],
        }
    else:
        new_connection = {
            'target_portal': "%s:%s" % (connection.host, connection.port),
            'target_iqn': connection.iqn,
            'target_lun': connection.lun,
        }
    LOG.debug("new connection is :")
    LOG.debug(new_connection)
    return new_connection
