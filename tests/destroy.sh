
tgtadm --lld iscsi --mode target --op delete --tid 3
dmsetup remove cached_dm-6
dmsetup remove cache_fcg
dmsetup remove ssd_fcg
dmsetup remove fcg
dmsetup remove multipath_3
multipath -F
iscsiadm -m node -T iqn.2010-10.org.openstack:3 -p 192.168.122.202 --logout
iscsiadm -m node -T iqn.2010-10.org.openstack:3 -p 192.168.122.203 --logout
