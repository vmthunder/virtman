class Chain:
    def __init__(self):
        self._chain = []

    def add_step(self, do, undo):
        assert callable(do) and callable(undo), "%s and %s must be callable" % (do, undo)
        self._chain.append((do, undo))

    def do(self):
        for i in range(len(self._chain)):
            try:
                self._chain[i][0]()
            except Exception:
                i -= 1
                while i >= 0:
                    self._chain[i][1]()
                    i -= 1
                raise