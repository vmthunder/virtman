class Tests(object):

    def __setattr__(self, name, value):
        setattr(self, name, value)
        #self.__dict__[name] = value

    def __getattr__(self, name):
        return getattr(self, name)
        return self.__dict__[name]

    def __str__(self):
        return "IamTest"


if __name__ == "__main__":
    t = Tests()
    t.name = "hehe"
    t.__setattr__("age", 100)

    print t
    print t.name
    print t.age
    print t.__dict__
    print object.__dict__