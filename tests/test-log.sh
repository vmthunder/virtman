#!/usr/bin/bash

dmsetup remove cache_fcg
dmsetup remove ssd_fcg
dmsetup remove fcg
pwd
cd /root/develop/VMThunder/
python setup.py install
cd /root/develop/VMThunder/bin/
python vmthunderd --debug
