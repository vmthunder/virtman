
from webob.exc import HTTPBadRequest
from webob.exc import HTTPForbidden
from webob.exc import HTTPConflict
from webob.exc import HTTPNotFound
from webob import Response
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

    def create(self, req):
        return NotImplementedError()

    def destroy(self, req):
        return NotImplementedError()

    def list(self, req):
        #self._enforce(req, 'list')
        #TODO：use policy.enforce
        print 'in compute list'
        instances = self.compute_instance.list()
        print instances
        res_body = jsonutils.dumps(instances)
        print res_body
        return Response(body=res_body, status=200)

def create_resource():
    return wsgi.Resource(ComputeAPI())