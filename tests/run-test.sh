#!/usr/bin/env bash

function dmsetup_remove
{
    for table in `dmsetup table | grep $1_ | awk -F ':' '{print $1}'`
    do
        dmsetup remove $table
    done
}

for i in `ps ax|grep vmt |grep python | awk '{print $1}'`;do kill -9 $i;done

dmsetup remove origin_1
dmsetup remove cached_loop1
tgtadm --lld iscsi --mode target --op delete --tid 1
tgtadm --lld iscsi --mode target --op delete --tid 3
tgtadm --lld iscsi --mode target --op delete --tid 2
dmsetup remove cached_dm-6
dmsetup remove cached_dm-7
dmsetup remove cached_dm-3
dmsetup remove cache_fcg
dmsetup remove ssd_fcg
dmsetup remove fcg
dmsetup remove multipath_1
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.164 --logout
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.169 --logout
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.162 --logout

dmsetup_remove snapshot

dmsetup_remove origin

dmsetup_remove cached


tgtadm --lld iscsi --mode target --op delete --tid 1
tgtadm --lld iscsi --mode target --op delete --tid 3

dmsetup remove cache_fcg
dmsetup remove ssd_fcg
dmsetup remove fcg

dmsetup_remove multipath

iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.164 --logout
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.162 --logout
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.169 --logout

rm -f /dev/disk/by-path/ip-10.100.9.8-iqn-hgiuhikhkj-snap1
ln -s /dev/loop1 /dev/disk/by-path/ip-10.100.9.8-iqn-hgiuhikhkj-snap1


rm -rf /usr/local/lib/python2.7/dist-packages/vmthunder*
rm -rf /root/develop/VMThunder/build/ /root/develop/VMThunder/vmthunder.egg*


cd /root/develop/VMThunder/tests
cd ../
python setup.py install
cd vmthunder/cmd
python vmthunderd.py --debug
