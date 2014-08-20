#!/usr/bin/env python

import xmlrpclib


[image_server, image_path, image_id, image_iqn] = open('image.txt').read().split()
print image_server, image_path, image_id, image_iqn

with open("nodelist.txt") as f:
    nodes = {}
    for line in f.readlines():
        [node, instance_name, snapshot_dev] = line.split()
        if node not in nodes:
            nodes[node] = xmlrpclib.ServerProxy('http://%s:7774' % node)
        print "Instance starts in", node, ", name =", instance_name, ", snap_dev is", snapshot_dev \
                , ", serve node is", nodes[node]
        nodes[node].create(instance_name, image_id, image_server+":3260", image_iqn, 1, snapshot_dev)
        print "The instance is OK!"