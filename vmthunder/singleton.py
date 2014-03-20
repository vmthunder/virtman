
def get_instance(cls, *args, **kv):
    if cls in cls.objs:
        return cls.objs[cls]
    else:
        return cls(*args, **kv)

class SingleTon(object):
    objs  = {}
    def __new__(cls, *args, **kv):
        if cls not in cls.objs:
            cls.objs[cls] = object.__new__(cls)
        return cls.objs[cls]

