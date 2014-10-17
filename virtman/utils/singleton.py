#!/usr/bin/env python

import threading


def singleton(cls):
    """
    singleton decorator, thread safe singleton mode.
    Maybe GIL makes sure thread safe?
    P.S., No singleton in cls()
    """
    lock = threading.Lock()
    instances = {}

    def _singleton(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return _singleton