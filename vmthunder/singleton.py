#!/usr/bin/env python

import threading


def singleton(cls):
    lock = threading.Lock()
    instances = {}

    def _singleton(*args, **kw):
        with lock:
            if cls not in instances:
                instances[cls] = cls(*args, **kw)
            return instances[cls]
    return _singleton