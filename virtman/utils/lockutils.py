
def synchronized(func):
    """
    synchronized decorator for class object, the class must contain a member called lock.
    """
    def _synchronized(*args, **kwargs):
        self = args[0]
        with self.lock:
            return func(*args, **kwargs)

    return _synchronized