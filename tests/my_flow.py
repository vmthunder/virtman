# -*- coding: utf-8 -*-
import logging
from taskflow.types import failure as ft
from taskflow import engines
from taskflow.patterns import linear_flow
from taskflow import task


class CreateCacheTask(task.Task):
    def execute(self, base_image, **kwargs):
        print self.name
        print 'create cache for %s' % base_image.multipath_path
        base_image.cached_path = '/test/cached'

    def revert(self, base_image, result, **kwargs):
        if isinstance(result, ft.Failure):
            print result.exception_str

        print 'destroy cache for %s' % base_image.multipath_path


class CreateOriginTask(task.Task):
    def execute(self, base_image, **kwargs):
        print self.name
        print 'create origin for %s' % base_image.cached_path

    def revert(self, base_image, result, **kwargs):
        if isinstance(result, ft.Failure):
            print result.exception_str
        print 'destroy origin for %s' % base_image.cached_path


class CreateTargetTask(task.Task):
    def execute(self, base_image,  **kwargs):
        print self.name
        print 'create target for %s, iqn: %s' % (base_image.cached_path,
                                                 base_image.iqn)

    def revert(self, base_image, result, **kwargs):
        if isinstance(result, ft.Failure):
            print result.exception_str
        print 'destroy target for %s, iqn: %s' % (base_image.cached_path,
                                                  base_image.iqn)


class LoginMasterTask(task.Task):
    def execute(self, base_image, **kwargs):
        print self.name
        print 'login master for %s, peer_id: %s, iqn: %s' % \
              (base_image.image_name, base_image.peer_id, base_image.iqn)
        raise IOError("ooooooooooo!!!!")

    def revert(self, base_image, result, **kwargs):
        if isinstance(result, ft.Failure):
            print result.exception_str
        print 'logout master for %s, peer_id: %s, iqn: %s' % \
              (base_image.image_name, base_image.peer_id, base_image.iqn)


class BaseImage():
    def __init__(self, multipath_path, origin_name, iqn, image_name, peer_id):
        self.multipath_path = multipath_path
        self.cached_path = None
        self.origin_name = origin_name
        self.iqn = iqn
        self.image_name = image_name
        self.peer_id = peer_id


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    test_multipath_path = '/test/multipath'
    test_origin_name = 'test_origin'
    test_iqn = 'iqn.2010-10.org.test:test_target'
    test_image_name = 'test_image'
    test_peer_id = '11111'

    base_image = BaseImage('/test/multipath',
                                'test_origin',
                                'iqn.2010-10.org.test:test_target',
                                'test_image',
                                '11111')

    wf = linear_flow.Flow("my_flow")
    wf.add(CreateCacheTask(),
           CreateOriginTask(),
           CreateTargetTask(),
           LoginMasterTask()
           )
    dict_for_task = dict(base_image=base_image)
    print dict_for_task
    try:
        logging.debug('hello.........')
        en = engines.run(wf, store=dict_for_task)
        # en.run()
        # print en.storage.fetch_all()
    except Exception as e:
        print e

