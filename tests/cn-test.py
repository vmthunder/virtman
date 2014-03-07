#!/usr/bin/env python
import sys
sys.path.append("..")
from vmthunder.computenode import ComputeNode
from testsuit import try_exec

if __name__ == '__main__':
    prop1 = {}
    prop1['target_portal'] = '192.168.122.202:3260'
    prop1['target_iqn'] = 'iqn.2010-10.org.openstack:3'
    prop1['target_lun'] = 1
    prop2 = {}
    prop2['target_portal'] = '192.168.122.203:3260'
    prop2['target_iqn'] = 'iqn.2010-10.org.openstack:3'
    prop2['target_lun'] = 1

    cn = ComputeNode()
    cn.fake_code('3', 'vm1', [prop1,prop2], '/dev/loop1')
    cn.destroy('3', 'vm1', [prop1,prop2], '/dev/loop1')
