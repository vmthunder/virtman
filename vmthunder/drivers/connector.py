import os

from brick.initiator.connector import ISCSIConnector

from vmthunder.singleton import SingleTon


@SingleTon
class ISCSIExecutor(ISCSIConnector):
    def __init__(self):
        super(ISCSIExecutor, self).__init__('')

iscsi_connector = ISCSIExecutor()


def connect_volume(connection):
    return iscsi_connector.connect_volume(connection)

def disconnect_volume(self, connection, device_info):
    #TODO: Fix this problem
    cmd = "iscsiadm -m node -T " + connection['target_iqn'] + " -p " + connection['target_portal'][:-5] + " --logout"
    os.popen(cmd)
