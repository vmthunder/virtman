#!/usr/bin/env python
import sys
sys.path.append("..")
from brick.iscsi.iscsi import TgtAdm
from brick.initiator.connector import get_connector_properties
from brick.initiator.connector import ISCSIConnector
from brick.openstack.common import log as logging
from testsuit import try_exec as try_exec

LOG = logging.getLogger(__name__)

def _test_create_iscsi_target():
	target = TgtAdm('', '/etc/tgt/conf.d')
	try_exec(target.create_iscsi_target, 'iqn.2010-10.org.openstack:1', '/dev/loop1')
def _test_show_target():
	target = TgtAdm('', '/etc/tgt/conf.d')
	try_exec(target.show_target, 1, 'iqn.2010-10.org.openstack:1')
def _test_remove_iscsi_target():
	target = TgtAdm('', '/etc/tgt/conf.d')
	try_exec(target.remove_iscsi_target, 1, 1, '1', '1')
def test_tgtadm():
	_test_create_iscsi_target()
	_test_show_target()
	_test_remove_iscsi_target()

def _test_iscsi_connect_volume(connect_props):
	iscsi = ISCSIConnector('')
	device_info = try_exec(iscsi.connect_volume, connect_props)
	print device_info
def _test_disconnect_volume(connect_props):
	iscsi = ISCSIConnector('')
	try_exec(iscsi.disconnect_volume, connect_props, '')
def test_iscsiadm():
	props = {}
	props['target_portal'] = '10.107.14.50:3260'
	props['target_iqn'] = 'iqn.2010-10.org.openstack:1'
	props['target_lun'] = 1
	_test_create_iscsi_target()
	_test_iscsi_connect_volume(props)
	_test_disconnect_volume(props)
	_test_remove_iscsi_target()

if __name__ == '__main__':
    _test_create_iscsi_target()
    #test_tgtadm()
	#test_iscsiadm()
