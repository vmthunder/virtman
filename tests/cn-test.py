#!/usr/bin/env python
import sys
sys.path.append("..")
import os
from vmthunder import compute
from testsuit import try_exec
if __name__ == '__main__':
    prop1 = {}
    prop1['target_portal'] = '10.107.14.162:3260'
    prop1['target_iqn'] = 'iqn.2010-10.org.openstack:4'
    prop1['target_lun'] = 1
    prop2 = {}
    prop2['target_portal'] = '10.107.14.163:3260'
    prop2['target_iqn'] = 'iqn.2010-10.org.openstack:4'
    prop2['target_lun'] = 1
    
    cn = compute.get_compute()
    cn.create('4', 'vm1', [prop1], '/dev/loop1')
    cn.create('4', 'vm2', [prop2], '/dev/loop2')
    cn1 = compute.get_compute()
    cn1.adjust_structure('4', [prop1], '')
    cn1.destroy('vm1')
    cn1.destroy('vm2')    
    cn.adjust_structure('4', [prop2], '')
    
