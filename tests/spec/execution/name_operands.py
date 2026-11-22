# spec: PLS-315 9.3.1, 9.3.2, 9.7, 27.2, 28.2
# description: Repeated name loads observe rebinding, separate globals and
# closures, lookup callbacks, and source lifetime across suspension.
from harness import *

def zero():
    return 0

code = compile("def read(): return zero() + payload\n", "<name-operands>", "exec")
first = {"zero": zero, "payload": 2, "__builtins__": {"payload": 9}}
second = {"zero": zero, "payload": 5}
exec(code, first)
exec(code, second)
left, right = first.pop("read"), second.pop("read")
for _ in range(3):
    assert (left(), right(), left()) == (2, 5, 2)
del first["payload"]
first["unrelated"] = 71
host.collect()
assert left() == 9
first["payload"] = 17
second["payload"] = 23
del code
assert (right(), left()) == (23, 17)

def outer(value):
    def read():
        return zero() + value
    def write(new):
        nonlocal value
        value = new
    def remove():
        nonlocal value
        del value
    return read, write, remove

read_a, write_a, remove_a = outer(3)
read_b, write_b, remove_b = outer(7)
for _ in range(3):
    assert (read_a(), read_b()) == (3, 7)
write_a(11)
remove_b()
assert read_a() == 11
assert_raises(NameError, read_b)
write_b(13)
assert read_b() == 13

# A lookup callback can replace the entry being compared and collect the
# values it removed. The load must use the replacement after the callback.
namespace = {"zero": zero}
class Key:
    def __hash__(self):
        return hash("payload")
    def __eq__(self, other):
        if other != "payload":
            return False
        namespace.clear()
        namespace["payload"] = 29
        host.collect()
        return True

namespace[Key()] = 19
exec("def read(): return zero() + payload\n", namespace)
read = namespace["read"]
assert read() == 29

# The comparison can return an object whose truth callback does the
# replacement. Both callbacks complete before the name lookup continues.
namespace = {"zero": zero}
events = []
class Decision:
    def __bool__(self):
        events.append("bool")
        namespace.clear()
        namespace["payload"] = 41
        host.collect()
        return True
class DeferredKey:
    def __hash__(self):
        return hash("payload")
    def __eq__(self, other):
        assert other == "payload"
        events.append("eq")
        return Decision()

namespace[DeferredKey()] = 19
exec("def read(): return zero() + payload\n", namespace)
read = namespace["read"]
assert read() == 41
assert events == ["eq", "bool"]

# The suspended frame retains the name operand's source unit after the
# creating function and the explicit code reference have been released.
namespace = {"zero": zero, "payload": 31}
exec(compile("def g():\n    yield 0\n    yield zero() + payload\n", "<name-lifetime>", "exec"), namespace)
generator = namespace.pop("g")()
assert next(generator) == 0
namespace["payload"] = 37
host.collect()
assert next(generator) == 37
generator.close()
del namespace
host.collect()
