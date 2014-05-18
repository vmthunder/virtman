#!/usr/bin/env python

import xmlrpclib


[image_server, image_path, image_id, image_iqn] = open('image.txt').read().split()
print image_server, image_path, image_id, image_iqn

with open("nodelist.txt") as f:
    nodes = {}
    for line in f.readlines():
        [node, vm, snapshot_dev] = line.split()
        if node not in nodes:
            nodes[node] = xmlrpclib.ServerProxy('http://%s:7774' % node)
        print node, vm, snapshot_dev
        print nodes[node]
        nodes[node].create(image_id, vm, image_server+":3260", image_iqn, 1, snapshot_dev)