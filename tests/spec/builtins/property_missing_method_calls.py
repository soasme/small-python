# spec: PLS-315 20.5.2
# description: property's __get__, __set__ and __delete__ called as
# methods without the accessor raise the AttributeError naming the
# property: its __set_name__ name's repr or its getter's __name__, each
# read through Python that may loop, whose errors pass out instead; from
# the property, its class, or a property subclass.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Name:
    def __repr__(self):
        for _ in (): pass
        log.append("repr"); return "N"
class Getter:
    def __call__(self, owner): return 1
    @property
    def __name__(self):
        for _ in (): pass
        log.append("name"); return "g"
class BadName:
    def __call__(self, owner): return 1
    @property
    def __name__(self):
        for _ in (): pass
        raise ValueError("bad name")
class BadRepr:
    def __repr__(self):
        for _ in (): pass
        raise KeyError("r")
class ReprName:
    def __call__(self, owner): return 1
    __name__ = BadRepr()
class Owner: pass
def attempt(f, *a):
    log.clear()
    try: f(*a); emit("no error")
    except Exception as e: emit(type(e).__name__, e, log)
p = property(Getter())
attempt(p.__set__, Owner(), 1)
attempt(p.__delete__, Owner())
attempt(property.__set__, p, Owner(), 1)
q = property(None, lambda o, v: None)
q.__set_name__(Owner, Name())
attempt(q.__get__, Owner())
attempt(q.__get__, Owner(), Owner)
attempt(q.__delete__, Owner())
attempt(property(BadName()).__set__, Owner(), 1)
attempt(property(ReprName()).__delete__, Owner())
emit(p.__get__(None, Owner) is p)
class Sub(property): pass
attempt(Sub(Getter()).__set__, Owner(), 2)
EXPECTED = [
    "AttributeError property 'g' of 'Owner' object has no setter ['name']",
    "AttributeError property 'g' of 'Owner' object has no deleter ['name']",
    "AttributeError property 'g' of 'Owner' object has no setter ['name']",
    "AttributeError property N of 'Owner' object has no getter ['repr']",
    "AttributeError property N of 'Owner' object has no getter ['repr']",
    "AttributeError property N of 'Owner' object has no deleter ['repr']",
    'ValueError bad name []',
    "KeyError 'r' []",
    'True',
    "AttributeError property 'g' of 'Owner' object has no setter ['name']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
