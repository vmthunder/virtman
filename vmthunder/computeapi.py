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
from vmthunder import compute

LOG = logging.getLogger(__name__)


class ComputeAPI(object):
    """

    """
    compute_instance = compute.Compute()

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

    def create(self, req):
        #TODO：use policy.enforce
        instance = self._get_body(req)
        image_id = instance['image_id']
        vm_name = instance['vm_name']
        connections = instance['connections']
        #TODO: snapshot_dev should be a link to snapshot
        snapshot_link = instance['snapshot_dev']
        #try:
        snapshot_path = self.compute_instance.create(image_id, vm_name, connections, snapshot_link)
        #except:
        #    raise 'Failed to create %s' % vm_name
        #else:
        res_body = jsonutils.dumps(snapshot_path)
        LOG.debug(res_body)
        return snapshot_path

    def destroy(self, req):
        instance = self._get_body(req)
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

    '''
    def list(self):
        def build_list_object(instances):
            instance_list = []
            for instance in instances.keys():
                instance_list.append({
                    'vm_name':instances[instance].vm_name,
                    })
            return { 'instances': instance_list}
        return build_list_object(self.instance_dict)
    '''


def create_resource():
    return wsgi.Resource(ComputeAPI())
