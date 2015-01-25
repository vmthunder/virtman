from virtman.openstack.common.gettextutils import _
from virtman.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class VirtmanException(Exception):
    """Base Virtman Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.message % kwargs

            except Exception:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                msg = (_("Exception in string format operation.  msg='%s'")
                       % self.message)
                LOG.exception(msg)
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))

                # at least get the core message out if something happened
                message = self.message

        # Put the message in 'msg' so that we can access it.  If we have it in
        # message it will be overshadowed by the class' message attribute
        self.msg = message
        super(VirtmanException, self).__init__(message)

    def __unicode__(self):
        return unicode(self.msg)