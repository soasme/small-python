# spec: PLS-315 13.3.4, 10.2.1, 7.4.3
# description: A call with *args or **kwargs of a bound method, a callable
# instance or a class with a Python __init__ binds self or the new instance
# first, then the unpacked arguments; the class call's value is the
# instance, __init__ returning other than None raises TypeError, and binding
# and __init__ errors propagate. Methods that loop run in function
# statements as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Point:
    def __init__(self, x, y=0, *rest, **extra):
        spin()
        self.args = (x, y, rest, extra)
        log.append(("init", type(self).__name__))
        if x == "bad":
            raise ValueError("init")
    def move(self, dx, dy=0, **flags):
        spin()
        log.append(("move", dx, dy, flags))
        return (self.args[0] + dx, self.args[1] + dy)

class Point3(Point): pass

class Returns:
    def __init__(self, *args): return 1

class Callable:
    def __call__(self, *args, **kwargs):
        spin()
        return ("called", args, kwargs)

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    del log[:]
    args, kwargs = [1, 2, 3], {"z": 4}
    p = Point(*args, **kwargs)
    q = Point3(*[5], y=6)
    r = Point(**{"x": 7})
    out = [type(p).__name__, p.args, type(q).__name__, q.args, r.args,
           p.move(*[10]), p.move(*(1, 2), **{"fast": True}), Point.move(p, *[3]),
           Callable()(*args, k=1), Callable()(**kwargs)]
    out += [error(lambda: Point(*["bad"])), error(lambda: Point(*[], **{})),
            error(lambda: Point(*[1], **{"x": 2})), error(lambda: Returns(*[1])),
            p.move(*[], **{"dx": 1, "spam": 2, "dy": 3}),
            error(lambda: p.move(**{1: 2}))]
    out.append(list(log))
    return out

expected = ["Point", (1, 2, (3,), {"z": 4}), "Point3", (5, 6, (), {}), (7, 0, (), {}),
            (11, 2), (2, 4), (4, 2),
            ("called", (1, 2, 3), {"k": 1}), ("called", (), {"z": 4}),
            ("ValueError", "init"),
            ("TypeError", "Point.__init__() missing 1 required positional argument: 'x'"),
            ("TypeError", "Point.__init__() got multiple values for argument 'x'"),
            ("TypeError", "__init__() should return None, not 'int'"),
            (2, 5),
            ("TypeError", "keywords must be strings"),
            [("init", "Point"), ("init", "Point3"), ("init", "Point"),
             ("move", 10, 0, {}), ("move", 1, 2, {"fast": True}), ("move", 3, 0, {}),
             ("init", "Point"), ("move", 1, 3, {"spam": 2})]]

def main():
    return calls()

assert_eq(main(), expected)
assert_eq(calls(), expected)
