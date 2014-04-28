from webob.exc import HTTPBadRequest
from webob.exc import HTTPForbidden
from webob.exc import HTTPConflict
from webob.exc import HTTPNotFound
from webob import Response
from webob import Request
import eventlet

#from vmthunder.common import policy
from vmthunder.common import exception
from vmthunder.common import wsgi
from vmthunder.openstack.common import log as logging
from vmthunder.openstack.common import jsonutils
from vmthunder import vmt

LOG = logging.getLogger(__name__)


class VMThunderAPI(object):
    """

    """
    compute_instance = vmt.VMThunder()

    def __init__(self):
        #self.policy = policy.Enforcer()
        self.pool = eventlet.GreenPool(size=1024)

    def _enforce(self, req, action):
        """Authorize an action against our policies"""
        try:
            policy.enforce(req.context, action, {})
        except exception.Forbidden:
            raise HTTPForbidden()

    def _get_body(self, req):
        body = jsonutils.loads(req.GET.get('body'))
        return body

    def create(self, req, **kwargs):
        #TODO：use policy.enforce
        #instance = self._get_body(req)
        LOG.debug("In computeapi create, req = ")
        LOG.debug(req)
        instance = kwargs['body']
        image_id = instance['image_id']
        vm_name = instance['vm_name']
        connections = instance['connections']
        #TODO: snapshot_dev should be a link to snapshot
        snapshot_connection = instance['snapshot_dev']
        #try:
        snapshot_path = self.compute_instance.create(image_id, vm_name, connections, snapshot_connection)
        #except:
        #    raise 'Failed to create %s' % vm_name
        #else:
        res_body = jsonutils.dumps(snapshot_path)
        LOG.debug(res_body)
        return snapshot_path

    def destroy(self, req, **kwargs):
        #instance = self._get_body(req)
        instance = kwargs['body']
        vm_name = instance['vm_name']
        #try:
        self.compute_instance.destroy(vm_name)
        #except:
        #     raise Exception('Failed to destroy %s' % vm_name)
        #else:
        return Response(body='', status=200)

    def list(self, req):
        #self._enforce(req, 'list')
        #TODO：use policy.enforce
        instances = self.compute_instance.list()
        res_body = jsonutils.dumps(instances)
        return Response(body=res_body, status=200)


def create_resource():
    return wsgi.Resource(VMThunderAPI())
