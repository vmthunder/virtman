from vmthunder.common import wsgi
from vmthunder import computeapi

class ComputeRouter(wsgi.Router):

    """WSGI router for VMThunder Instance requests"""

    def __init__(self, mapper):
        compute_resource = computeapi.create_resource()

        mapper.connect("/list",
                       controller=compute_resource,
                       action='list',
                       conditions={'method':['GET']})
        mapper.connect("/create/{instance_name}",
                       controller=compute_resource,
                       action='create',
                       conditions={'method':['POST']})
        mapper.connect("/destroy/{instance_name}",
                       controller=compute_resource,
                       action='destroy',
                       conditions={'method':['POST']})

        super(ComputeRouter, self).__init__(mapper)
