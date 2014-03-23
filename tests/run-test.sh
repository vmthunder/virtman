dmsetup remove snapshot_vm1
dmsetup remove origin_1
dmsetup remove cached_loop1
tgtadm --lld iscsi --mode target --op delete --tid 1
dmsetup remove cached_dm-6
dmsetup remove cache_fcg
dmsetup remove ssd_fcg
dmsetup remove fcg
dmsetup remove multipath_1
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.50 --logout

dmsetup remove snapshot_vm1
dmsetup remove origin_1
dmsetup remove cached_loop1
tgtadm --lld iscsi --mode target --op delete --tid 1
dmsetup remove cached_dm-6
dmsetup remove cache_fcg
dmsetup remove ssd_fcg
dmsetup remove fcg
dmsetup remove multipath_1
iscsiadm -m node -T iqn.2010-10.org.openstack:1 -p 10.107.14.50 --logout

cd ../
python setup.py install
cd bin
python vmthunderd
