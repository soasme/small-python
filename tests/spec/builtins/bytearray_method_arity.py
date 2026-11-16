# spec: PLS-315 24.2
# description: A bytearray's append, extend, pop, insert, remove, clear,
# copy and reverse take positional arguments only, their count checked
# as the methods' of the type, and name the type when they refuse one.
from harness import *

def results():
    ba = bytearray(b"abc")
    out = []
    for n in ("append", "extend", "pop", "insert", "remove", "clear", "copy", "reverse"):
        for k in range(4):
            try: getattr(ba, n)(*[0] * k)
            except TypeError as e: out.append((n, k, str(e)))
            except Exception as e: out.append((n, k, type(e).__name__))
            ba[:] = b"abc"
        try: getattr(ba, n)(x=1)
        except TypeError as e: out.append((n, "kw", str(e)))
    return out

expected = [('append', 0, 'bytearray.append() takes exactly one argument (0 given)'),
            ('append', 2, 'bytearray.append() takes exactly one argument (2 given)'),
            ('append', 3, 'bytearray.append() takes exactly one argument (3 given)'),
            ('append', 'kw', 'bytearray.append() takes no keyword arguments'),
            ('extend', 0, 'bytearray.extend() takes exactly one argument (0 given)'),
            ('extend', 1, "can't extend bytearray with int"),
            ('extend', 2, 'bytearray.extend() takes exactly one argument (2 given)'),
            ('extend', 3, 'bytearray.extend() takes exactly one argument (3 given)'),
            ('extend', 'kw', 'bytearray.extend() takes no keyword arguments'),
            ('pop', 2, 'pop expected at most 1 argument, got 2'), ('pop', 3, 'pop expected at most 1 argument, got 3'),
            ('pop', 'kw', 'bytearray.pop() takes no keyword arguments'),
            ('insert', 0, 'insert expected 2 arguments, got 0'), ('insert', 1, 'insert expected 2 arguments, got 1'),
            ('insert', 3, 'insert expected 2 arguments, got 3'),
            ('insert', 'kw', 'bytearray.insert() takes no keyword arguments'),
            ('remove', 0, 'bytearray.remove() takes exactly one argument (0 given)'), ('remove', 1, 'ValueError'),
            ('remove', 2, 'bytearray.remove() takes exactly one argument (2 given)'),
            ('remove', 3, 'bytearray.remove() takes exactly one argument (3 given)'),
            ('remove', 'kw', 'bytearray.remove() takes no keyword arguments'),
            ('clear', 1, 'bytearray.clear() takes no arguments (1 given)'),
            ('clear', 2, 'bytearray.clear() takes no arguments (2 given)'),
            ('clear', 3, 'bytearray.clear() takes no arguments (3 given)'),
            ('clear', 'kw', 'bytearray.clear() takes no keyword arguments'),
            ('copy', 1, 'bytearray.copy() takes no arguments (1 given)'),
            ('copy', 2, 'bytearray.copy() takes no arguments (2 given)'),
            ('copy', 3, 'bytearray.copy() takes no arguments (3 given)'),
            ('copy', 'kw', 'bytearray.copy() takes no keyword arguments'),
            ('reverse', 1, 'bytearray.reverse() takes no arguments (1 given)'),
            ('reverse', 2, 'bytearray.reverse() takes no arguments (2 given)'),
            ('reverse', 3, 'bytearray.reverse() takes no arguments (3 given)'),
            ('reverse', 'kw', 'bytearray.reverse() takes no keyword arguments')]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
