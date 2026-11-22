# Replays MatchLookups.tla: each case matches a logged mapping or class
# pattern against a subject with the program's entries, and compares
# whether it matched, and the log, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PRE = """log = []
class Keys:
    @property
    def a(self):
        log.append('key a')
        return 'a'
    @property
    def b(self):
        log.append('key b')
        return 'b'
K = Keys()
class Sub:
    def __init__(self, name):
        self.name = name
    def __eq__(self, o):
        for _ in (): pass
        log.append('sub ' + self.name)
        return o == 1
class S:
    a = Sub('a')
    b = Sub('b')
class M(dict):
    def get(self, key, default=None):
        log.append('get ' + key)
        return dict.get(self, key, default)
class P:
    __match_args__ = ('a', 'b')
    def __init__(self, values):
        self.values = values
    def read(self, name):
        log.append('attr ' + name)
        if name not in self.values:
            raise AttributeError(name)
        return self.values[name]
    a = property(lambda self: self.read('a'))
    b = property(lambda self: self.read('b'))
hit = False
"""


def outcome(p):
    values = {name: 1 if entry["matches"] else 2 for name, entry in zip("ab", p["entries"]) if entry["present"]}
    if p["kind"] == "mapping":
        values.update(c=0, d=0)
        source = "match M(%r):\n    case {K.a: S.a, K.b: S.b}:\n        hit = True\n" % values
    else:
        source = "match P(%r):\n    case P(S.a, S.b):\n        hit = True\n" % values
    namespace = {}
    exec(compile(PRE + source, "<match>", "exec"), namespace)
    return ("hit" if namespace["hit"] else "miss", tuple(namespace["log"]))


check_programs(outcome)
