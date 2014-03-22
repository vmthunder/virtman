
from webob.exc import HTTPBadRequest
from webob.exc import HTTPForbidden
from webob.exc import HTTPConflict
from webob.exc import HTTPNotFound
from webob import Response
from webob import Request
import eventlet

from vmthunder.common import policy
from vmthunder.common import exception
from vmthunder.common import wsgi
from vmthunder.openstack.common import log as logging
from vmthunder.openstack.common import jsonutils
from vmthunder import compute

LOG = logging.getLogger(__name__)

class ComputeAPI(object):
    """

    """
    compute_instance = compute.get_compute()
    def __init__(self):
        #self.policy = policy.Enforcer()
        self.pool = eventlet.GreenPool(size=1024)

    def _enforce(self, req, action):
        """Authorize an action against our policies"""
        try:
            policy.enforce(req.context, action, {})
        except exception.Forbidden:
            raise HTTPForbidden()

    def _get_body(selfself, req):
        body = jsonutils.loads(req.GET.get('body'))
        return body

    def create(self, req):
        #TODO：use policy.enforce
        print 'in compute create'
        print 'header=', req.headers
        print 'url=',req.url
        body = self._get_body(req)
        print type(body)
        print body

        try:
            print image_id, vm_name, connections, snapshot_dev
            #self.compute_instance.create(image_id, vm_name, connections, snapshot_dev)
        except:
            raise 'Failed to create %s' % vm_name
        else:
            return Response(body='', status=200)

    def destroy(self, req):
        return NotImplementedError()

    def list(self, req):
        #self._enforce(req, 'list')
        #TODO：use policy.enforce
        print 'in compute list'
        instances = self.compute_instance.list()
        print instances
        res_body = jsonutils.dumps(instances)
        return Response(body=res_body, status=200)

def create_resource():
    return wsgi.Resource(ComputeAPI())