import functools
import threading
import weakref
import time

from virtman.openstack.common import log as logging

LOG = logging.getLogger(__name__)

_semaphores = weakref.WeakValueDictionary()
_semaphores_lock = threading.Lock()


class GeneratorContextManager(object):
    """Helper for @contextmanager decorator."""

    def __init__(self, gen):
        self.gen = gen

    def __enter__(self):
        try:
            return self.gen.next()
        except StopIteration:
            raise RuntimeError("generator didn't yield")

    def __exit__(self, type, value, traceback):
        if type is None:
            try:
                self.gen.next()
            except StopIteration:
                return
            else:
                raise RuntimeError("generator didn't stop")
        else:
            if value is None:
                # Need to force instantiation so we can reliably
                # tell if we get the same exception back
                value = type()
            try:
                self.gen.throw(type, value, traceback)
                raise RuntimeError("generator didn't stop after throw()")
            except StopIteration, exc:
                # Suppress the exception *unless* it's the same exception that
                # was passed to throw().  This prevents a StopIteration
                # raised inside the "with" statement from being suppressed
                return exc is not value
            except:
                # only re-raise if it's *not* the exception that was
                # passed to throw(), because __exit__() must not raise
                # an exception unless __exit__() itself failed.  But throw()
                # has to raise the exception to signal propagation, so this
                # fixes the impedance mismatch between the throw() protocol
                # and the __exit__() protocol.
                #
                if sys.exc_info()[1] is not value:
                    raise


def contextmanager(func):
    @functools.wraps(func)
    def helper(*args, **kwds):
        return GeneratorContextManager(func(*args, **kwds))
    return helper


def synchronized(name):
    """Synchronization decorator.

    Decorating a method like so::

        @synchronized('mylock')
        def foo(self, *args):
           ...

    ensures that only one thread will execute the foo method at a time.
    """

    def wrap(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            try:
                with lock(name):
                    LOG.debug('Got semaphore / lock "%(function)s"',
                              {'function': f.__name__})
                    return f(*args, **kwargs)

            finally:
                LOG.debug('Semaphore / lock released "%(function)s"',
                          {'function': f.__name__})
        return inner
    return wrap


def internal_lock(name):
    with _semaphores_lock:
        try:
            sem = _semaphores[name]
        except KeyError:
            sem = threading.Semaphore()
            _semaphores[name] = sem

    LOG.debug('Got semaphore "%(lock)s"', {'lock': name})
    return sem


@contextmanager
def lock(name):
    int_lock = internal_lock(name)
    with int_lock:
        yield int_lock
    LOG.debug('Released semaphore "%(lock)s"', {'lock': name})


def batch_exec(fun, thread_number):
    thread_lists = []
    for thread_id in range(thread_number):
        thread = threading.Thread(target=fun)
        thread.start()
        thread_lists.append(thread)
    for thread in thread_lists:
        thread.join()

if __name__ == '__main__':
    import sys
    from oslo.config import cfg

    @synchronized('test')
    def test_time():
        print time.ctime()
        time.sleep(2)

    def batch_exec(fun, thread_number):
        thread_lists = []
        for thread_id in range(thread_number):
            thread = threading.Thread(target=fun)
            thread.start()
            thread_lists.append(thread)
        for thread in thread_lists:
            thread.join()

    CONF = cfg.CONF
    CONF(sys.argv[1:], project=__name__, default_config_files=['./my.conf'])

    logging.setup(__name__)

    batch_exec(test_time, 10)