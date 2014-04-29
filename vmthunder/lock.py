import threading

#try:
#    from brick.openstack.common import log as logging
#except ImportError:
from vmthunder.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def synchronized(name):
    """Synchronization decorator.

    Decorating a method like so::

        @synchronized('mylock')
        def foo(self, *args):
           ...

    ensures that only one thread will execute the foo method at a time.

    Different methods can share the same lock::

        @synchronized('mylock')
        def foo(self, *args):
           ...

        @synchronized('mylock')
        def bar(self, *args):
           ...

    This way only one of either foo or bar can be executing at a time.
    """

    locks = {}

    def wrap(f):
        def inner(*args, **kwargs):
            if name not in locks:
                locks[name] = threading.RLock()
            try:
                with locks[name]:
                    LOG.debug('Got semaphore / lock "%(function)s"',
                              {'function': f.__name__})
                    return f(*args, **kwargs)
            finally:
                LOG.debug('Semaphore / lock released "%(function)s"',
                          {'function': f.__name__})
        return inner
    return wrap
