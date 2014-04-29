#!/usr/bin/env bash

function dmsetup_remove
{
    for table in `dmsetup table | grep $1_ | awk -F ':' '{print $1}'`
    do
        dmsetup remove $table
    done
}

for i in `ps ax|grep vmt |grep python | awk '{print $1}'`;do kill -9 $i;done


dmsetup_remove snapshot

dmsetup_remove origin

dmsetup_remove cached

dmsetup remove cache_fcg
dmsetup remove ssd_fcg
dmsetup remove fcg

dmsetup_remove multipath

cd /root/packages/VMThunder/tests
cd ../
python setup.py install
cd vmthunder/cmd
echo "" > vmthunder.log
echo "" > vmthunder.log
python vmthunderd.py --debug --log-file vmthunder.log
