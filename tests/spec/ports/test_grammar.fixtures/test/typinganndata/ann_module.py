

"""
The module for testing variable annotations.
Empty lines above are for good reason (testing for correct line numbers)
"""

# (Ported) typing and functools are not imported.
Optional = lambda t: t

class C:

    x = 5; y: Optional['C'] = None  # (Ported) Optional[...] written as a call

# (Ported) typing.Tuple is the builtin tuple.
x: int = 5; y: str = x; f: tuple[int, int]

class M(type):
    o: type = object

(pars): bool = True

class D(C):
    j: str = 'hi'; k: str= 'bye'

# (Ported) types.new_class is three-argument type().
h_class = type('H', (C,), {})
j_class = type('J', (), {})

class F():
    z: int = 5
    def __init__(self, x):
        pass

class Y(F):
    def __init__(self):
        super(F, self).__init__(123)

class Meta(type):
    def __new__(meta, name, bases, namespace):
        return super().__new__(meta, name, bases, namespace)

class S(metaclass = Meta):
    x: str = 'something'
    y: str = 'something else'

def foo(x: int = 10):
    def bar(y: List[str]):
        x: str = 'yes'
    bar()

def dec(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    # (Ported) functools.wraps copies the wrapped function's metadata.
    for name in ('__module__', '__name__', '__qualname__', '__doc__'):
        setattr(wrapper, name, getattr(func, name))
    wrapper.__wrapped__ = func
    return wrapper

u: int | float
