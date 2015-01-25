from functools import partial
from virtman.openstack.common import log as logging

LOG = logging.getLogger(__name__)
CHAIN_TRIES = 3


class Chain(object):
    """
    build chain, roll over if failed
    """
    def __init__(self):
        self._chain = []

    def add_step(self, do, undo):
        assert callable(do) and callable(undo), "%s and %s must be callable" % \
                                                (do, undo)
        self._chain.append((do, undo))

    def do(self):
        stop_flag = False
        global LOG
        LOG.debug("Virtman: Chain is: %s" %
                  [(self._get_func(x), self._get_func(y)) for (x, y) in
                   self._chain])
        for i in range(len(self._chain)):
            tries = 0
            suc = False
            while tries < CHAIN_TRIES and suc is False:
                try:
                    self._chain[i][0]()
                    suc = True
                except Exception:
                    self._chain[i][1]()
                    tries += 1
                finally:
                    if tries < CHAIN_TRIES:
                        LOG.debug("Virtman: Chain try:%s for %s suc:%s" % (
                            tries, self._get_func(self._chain[i][0]), suc))

            if tries == CHAIN_TRIES and suc is False:
                while i >= 0:
                    self._chain[i][1]()
                    i -= 1
                stop_flag = True
            if stop_flag:
                raise

    @staticmethod
    def _get_func(callable_fun):
        if hasattr(callable_fun, 'func'):
            return callable_fun.func
        return callable_fun

if __name__ == "__main__":
    " Test and demostrate Chain itself "
    import sys
    from oslo.config import cfg

    CONF = cfg.CONF
    CONF(sys.argv[1:], project=__name__, default_config_files=[
        '/etc/virtman/virtman.conf'])

    logging.setup(__name__)
    c = Chain()

    def asdf(n):
        print '%s' % n

    def qwer(n):
        print 'except %s' % n
        raise OverflowError()

    print sys.argv
    c.add_step(partial(asdf, 1), partial(asdf, -1))
    c.add_step(partial(asdf, 2), partial(asdf, -2))
    c.add_step(partial(asdf, 3), partial(asdf, -3))
    c.do()

    # c.add_step(lambda: asdf(1), lambda: asdf(-1))
    # c.add_step(lambda: asdf(2), lambda: asdf(-2))
    # c.add_step(lambda: asdf(3), lambda: asdf(-3))
    # c.do()