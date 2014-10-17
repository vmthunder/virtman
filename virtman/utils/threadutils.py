
import threading
import eventlet

from virtman.utils.enum import Enum

THREAD_MODULES = Enum(['eventlet', 'threading'])

thread_module = None


def set_thread_module(module):
    global thread_module
    if module == THREAD_MODULES.eventlet or module == eventlet:
        thread_module = eventlet
    elif module == THREAD_MODULES.threading or module == threading:
        thread_module = threading
    else:
        raise Exception("thread module %s can not support currently" % module)


def sleep(seconds):
    return thread_module.sleep(seconds)