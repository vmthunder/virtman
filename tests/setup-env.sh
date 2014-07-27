#!/usr/bin/env bash

mkdir -p /root/blocks
dd if=/dev/zero of=/root/blocks/cache.blk bs=1M count=15k
losetup /dev/loop1 /root/blocks/cache.blk

echo "create snapshot devices"
dd if=/dev/zero of=/root/blocks/snap1.blk bs=1M count=512
losetup /dev/loop2 /root/blocks/snap1.blk

dd if=/dev/zero of=/root/blocks/snap2.blk bs=1M count=512
losetup /dev/loop3 /root/blocks/snap2.blk

dd if=/dev/zero of=/root/blocks/snap3.blk bs=1M count=512
losetup /dev/loop4 /root/blocks/snap3.blk
