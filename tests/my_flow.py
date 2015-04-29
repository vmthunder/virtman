# -*- coding: utf-8 -*-
from taskflow.types import failure as ft
from taskflow import engines
from taskflow.patterns import linear_flow
from taskflow import task
from oslo.config import cfg
from virtman.drivers import fcg
from virtman.drivers import dmsetup
from virtman.drivers import iscsi
from virtman.drivers import volt
from virtman.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Cache(object):
    def create_cache(multipath_path):
        LOG.debug("Virtman: create cache for baseimage according to "
                  "multipath %s" % multipath_path)
        try:
            cached_path = fcg.add_disk(multipath_path)
        except Exception:
            raise
        LOG.debug("Virtman: create cache completed, cache path = %s" %
                  cached_path)
        return cached_path

    def delete_cache(multipath_path):
        LOG.debug("Virtman: start to delete cache according to multipath %s " %
                  multipath_path)
        try:
            fcg.rm_disk(multipath_path)
        except Exception:
            raise
        LOG.debug("Virtman: delete cache according to multipath %s completed" %
                  multipath_path)


class Origin(object):
    @staticmethod
    def create_origin(origin_name, cached_path):
        LOG.debug("Virtman: start to create origin, cache path = %s" %
                  cached_path)
        try:
            origin_path = dmsetup.origin(origin_name,
                                         cached_path)
        except Exception:
            raise
        LOG.debug("Virtman: create origin complete, origin path = %s" %
                  origin_path)
        return origin_path

    @staticmethod
    def delete_origin(origin_name):
        LOG.debug("Virtman: start to remove origin %s " % origin_name)
        try:
            dmsetup.remove_table(origin_name)
        except Exception:
            raise
        LOG.debug("Virtman: remove origin %s completed" % origin_name)


class Target(object):
    @staticmethod
    def create_target(iqn, cached_path):
        LOG.debug("Virtman: start to create target, cache path = %s" %
                  cached_path)
        if iscsi.exists(iqn):
            return
        else:
            try:
                target_id = iscsi.create_iscsi_target(iqn, cached_path)
            except Exception:
                raise
        LOG.debug("Virtman: create target complete, target id = %s" %
                  target_id)
        return target_id

    @staticmethod
    def delete_target(target_id, image_name):
        LOG.debug("Virtman: start to remove target %s (%s)" %
                  (target_id, image_name))
        try:
            iscsi.remove_iscsi_target(image_name, image_name)
        except Exception:
            raise
        LOG.debug("Virtman: successful remove target %s (%s)" %
                  (target_id, image_name))


class Master(object):
    @staticmethod
    def login_master(image_name, peer_id, iqn):
        LOG.debug("Virtman: try to login to master server")
        try:
            info = volt.login(session_name=image_name,
                              peer_id=peer_id,
                              host=CONF.host_ip,
                              port='3260',
                              iqn=iqn,
                              lun='1')
        except Exception:
            raise
        LOG.debug("Virtman: login to master server %s" % info)

    @staticmethod
    def logout_master(image_name, peer_id):
        LOG.debug("Virtman: logout master session = %s, peer_id = %s" %
                  (image_name, peer_id))
        try:
            volt.logout(session_name=image_name, peer_id=peer_id)
        except Exception:
            raise


class CreateCacheTask(task.Task):
    default_provides = 'cached_path'

    def execute(self, multipath_path, **kwargs):
        print self.name
        print 'create cache for %s' % multipath_path
        return '/test/cached'

    def revert(self, multipath_path, result, **kwargs):
        if isinstance(result, ft.Failure):
            print result.exception_str

        print 'destroy cache for %s' % multipath_path


class CreateOriginTask(task.Task):
    def execute(self, origin_name, cached_path):
        print self.name
        print 'create origin for %s' % cached_path

    def revert(self, origin_name, cached_path, result, **kwargs):
        if isinstance(result, ft.Failure):
            print result.exception_str
        print 'destroy origin for %s' % cached_path


class CreateTargetTask(task.Task):
    def execute(self, iqn, cached_path,  **kwargs):
        print self.name
        print 'create target for %s, iqn: %s' % (cached_path, iqn)

    def revert(self, iqn, cached_path, result, **kwargs):
        if isinstance(result, ft.Failure):
            print result.exception_str
        print 'destroy target for %s, iqn: %s' % (cached_path, iqn)


class LoginMasterTask(task.Task):
    def execute(self, image_name, peer_id, iqn, **kwargs):
        print self.name
        print 'login master for %s, peer_id: %s, iqn: %s' % (image_name,
                                                             peer_id, iqn)
        raise IOError("ooooooooooo!!!!")

    def revert(self, image_name, peer_id, iqn,result,  **kwargs):
        if isinstance(result, ft.Failure):
            print result.exception_str
        print 'logout master for %s, peer_id: %s, iqn: %s' % (image_name,
                                                              peer_id, iqn)

if __name__ == '__main__':
    test_multipath_path = '/test/multipath'
    test_origin_name = 'test_origin'
    test_iqn = 'iqn.2010-10.org.test:test_target'
    test_image_name = 'test_image'
    test_peer_id = '11111'

    wf = linear_flow.Flow("my_flow")
    wf.add(CreateCacheTask(),
           CreateOriginTask(),
           CreateTargetTask(),
           LoginMasterTask()
           )
    dict_for_task = dict(multipath_path=test_multipath_path,
                         origin_name=test_origin_name,
                         iqn=test_iqn,
                         image_name=test_image_name,
                         peer_id=test_peer_id)
    print dict_for_task
    try:
        en = engines.run(wf, store=dict_for_task)
        en.run()
        print en.storage.fetch_all()
    except Exception as e:
        print e

