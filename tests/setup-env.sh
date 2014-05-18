#!/usr/bin/env bash

mkdir /root/packages/blocks
dd if=/dev/zero of=/root/packages/blocks/cache.blk bs=1M count=1k
losetup /dev/loop1 /root/packages/blocks/cache.blk

echo "create snapshot devices"
dd if=/dev/zero of=/root/packages/blocks/snap1.blk bs=1M count=512
losetup /dev/loop2 /root/packages/blocks/snap1.blk

dd if=/dev/zero of=/root/packages/blocks/snap2.blk bs=1M count=512
losetup /dev/loop3 /root/packages/blocks/snap2.blk

dd if=/dev/zero of=/root/packages/blocks/snap3.blk bs=1M count=512
losetup /dev/loop4 /root/packages/blocks/snap3.blk
