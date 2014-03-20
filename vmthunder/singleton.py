class SingleTon(object):
    objs  = {}
    def __new__(cls, *args, **kv):
        if cls not in cls.objs:
            cls.objs[cls] = object.__new__(cls)
        return cls.objs[cls]

