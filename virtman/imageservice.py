#!/usr/bin/env python

import os

from virtman import blockservice
from virtman.drivers import iscsi
from virtman.openstack.common import log as logging

LOG = logging.getLogger(__name__)


targetlist = {}


def create_image_target(image_name, file_path, loop_dev, iqn_prefix):
    """
    :returns : string
        "0:info" specifies SUCCESS, info="target_id:loop_dev"
        "1:info" specifies WARNING, info indicates image_name exists
        "2:info" specifies WARNING, info indicates image file_path not exists
    """
    LOG.debug("Virtman: Image Service: create image target started! image_name = %s, "
              "file_path = %s" % (image_name, file_path))
    if not image_name.startswith("volume-"):
        image_name = "volume-" + image_name
    if targetlist.has_key(image_name):
        LOG.debug("Virtman: Image Service: Warning! image_name = %s exists! Please use another name"
                  % image_name)
        return "1:" + "Virtman: Image Service: Warning! image_name = %s exists! Please use another name" \
               % image_name
    if not os.path.exists(file_path):
        LOG.debug("Virtman: Image Service: Warning! image file_path = %s not exists! Please use another "
                  "image file" % file_path)
        return "2:" + "Virtman: Image Service: Warning! image file_path = %s not exists! Please use " \
                      "another image file" % file_path
    if loop_dev is None:
        loop_dev = blockservice.findloop()
    else:
        blockservice.unlinkloop(loop_dev)
    blockservice.linkloop(loop_dev, file_path)
    target_id = iscsi.create_iscsi_target(iqn_prefix + image_name, loop_dev)
    targetlist[image_name] = target_id + ':' +loop_dev
    LOG.debug("Virtman: Image Service: create image target completed! image_target_id = %s loop_dev = %s"
              % (target_id, loop_dev))
    return "0:" + target_id + ":" + loop_dev


def destroy_image_target(image_name):
    """
    :returns : string
        "0:info" specifies SUCCESS, info="nothing", nothing is None
        "1:info" specifies WARNING, info indicates image_name not exists
    """
    LOG.debug("Virtman: Image Service: remove image target started! image_name = %s" % image_name)
    if not image_name.startswith("volume-"):
        image_name = "volume-" + image_name
    if not targetlist.has_key(image_name):
        LOG.debug("Virtman: Image Service: Warning! image_name = %s not exists!" % image_name)
        return "1:" + "Virtman: Image Service: Warning! image_name = %s not exists!" % image_name
    nothing = iscsi.remove_iscsi_target(image_name, image_name)
    blockservice.unlinkloop(targetlist[image_name].split(':')[1])
    del targetlist[image_name]
    LOG.debug("Virtman: Image Service: remove image target completed!")
    return "0:" + str(nothing)


def list_image_target( ):
    return targetlist
