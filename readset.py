class settings:
    def __init__(self, fn: str=None):
        if fn is not None:
            self.parse(fn)
    
    def parse(self, fn: str):
        d = {}
        with open(fn, 'r', encoding='utf8') as f:
            t = f.read()
            for i in t.splitlines(False):
                l = i.split('=', 2)
                if len(l) == 2:
                    d[l[0]] = l[1]
        self._token = d['token'] if 'token' in d else None
