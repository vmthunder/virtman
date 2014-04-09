dmsetup remove origin_1
dmsetup remove cached_loop1
tgtadm --lld iscsi --mode target --op delete --tid 1
tgtadm --lld iscsi --mode target --op delete --tid 3
tgtadm --lld iscsi --mode target --op delete --tid 2
dmsetup remove cached_dm-6
dmsetup remove cached_dm-7
dmsetup remove cache_fcg
dmsetup remove ssd_fcg
dmsetup remove fcg
dmsetup remove multipath_1
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.164 --logout
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.169 --logout
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.162 --logout

dmsetup remove snapshot_vm1
dmsetup remove origin_1
dmsetup remove cached_loop1
tgtadm --lld iscsi --mode target --op delete --tid 1
tgtadm --lld iscsi --mode target --op delete --tid 3
dmsetup remove cached_dm-6
dmsetup remove cached_dm-7
dmsetup remove cache_fcg
dmsetup remove ssd_fcg
dmsetup remove fcg
dmsetup remove multipath_1
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.164 --logout
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.162 --logout
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.169 --logout

cd develop/VMThunder/tests
cd ../
python setup.py install
cd bin
python vmthunderd --debug
