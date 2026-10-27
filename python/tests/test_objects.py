"""Object: Python protocols forwarded to engine values."""
import unittest

from small_python import Error, Object, Runtime

CLASSES = """
class Point:
    '''A point.'''
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.runtime = 'engine attribute'
    def norm(self, *, scale=1):
        return (self.x * self.x + self.y * self.y) * scale
    def __repr__(self):
        return f'Point({self.x}, {self.y})'
    def __str__(self):
        return f'({self.x}, {self.y})'
    def __eq__(self, other):
        return isinstance(other, Point) and (self.x, self.y) == (other.x, other.y)
    def __hash__(self):
        return hash((self.x, self.y))
    def __lt__(self, other):
        return (self.x, self.y) < (other.x, other.y)

class Bag:
    def __init__(self):
        self.items = {}
    def __getitem__(self, key):
        return self.items[key]
    def __setitem__(self, key, value):
        self.items[key] = value
    def __len__(self):
        return len(self.items)
    def __contains__(self, key):
        return key in self.items
    def __bool__(self):
        return bool(self.items)

class Strict:
    __slots__ = ('a',)
"""


class ObjectTest(unittest.TestCase):
    def setUp(self):
        self.rt = Runtime()
        self.rt.exec(CLASSES)

    def tearDown(self):
        self.rt.close()

    def test_not_constructible(self):
        with self.assertRaises(TypeError):
            Object()

    def test_call(self):
        p = self.rt.call("Point", 3, 4)
        self.assertIsInstance(p, Object)
        self.assertEqual(p.norm(), 25)
        self.assertEqual(p.norm(scale=2), 50)
        self.assertEqual(self.rt["Point"](1, y=2).y, 2)
        with self.assertRaises(Error) as cm:
            p.norm(1)
        self.assertEqual(cm.exception.type, "TypeError")

    def test_attributes(self):
        p = self.rt.call("Point", 3, 4)
        self.assertEqual((p.x, p.y), (3, 4))
        p.x = 10
        self.assertEqual(self.rt.call("getattr", p, "x"), 10)
        self.assertEqual(p.runtime, "engine attribute")
        self.assertEqual(p.__doc__, "A point.")
        self.assertIsInstance(p.__class__, Object)
        self.assertEqual(p.__class__.__name__, "Point")
        self.assertTrue(hasattr(p, "norm"))
        self.assertFalse(hasattr(p, "missing"))
        with self.assertRaisesRegex(AttributeError, "missing"):
            p.missing
        with self.assertRaises(TypeError):
            del p.x
        with self.assertRaises(AttributeError):
            self.rt.call("Strict").b = 1
        with self.assertRaises(AttributeError):
            self.rt.eval("1 .bit_length").__self__.y = 1

    def test_items(self):
        bag = self.rt.call("Bag")
        bag["a"] = [1]
        self.assertEqual(bag["a"], [1])
        with self.assertRaises(KeyError) as cm:
            bag["missing"]
        self.assertEqual(cm.exception.args, ("missing",))
        with self.assertRaises(IndexError):
            self.rt.eval("range(3)")[10]
        with self.assertRaises(TypeError):
            self.rt.eval("range(3)")["a"]
        with self.assertRaises(TypeError):
            self.rt.eval("range(3)")[0] = 1
        with self.assertRaises(TypeError):
            del bag["a"]

    def test_len_contains_bool(self):
        bag = self.rt.call("Bag")
        self.assertFalse(bag)
        self.assertEqual(len(bag), 0)
        bag["k"] = 1
        self.assertTrue(bag)
        self.assertEqual(len(bag), 1)
        self.assertIn("k", bag)
        self.assertNotIn("z", bag)
        self.assertEqual(len(self.rt.eval("range(7)")), 7)
        self.assertIn(3, self.rt.eval("range(5)"))
        with self.assertRaises(TypeError):
            len(self.rt.call("Point", 1, 2))
        with self.assertRaises(TypeError):
            object() in bag

    def test_iteration(self):
        self.assertEqual(list(self.rt.eval("range(3)")), [0, 1, 2])
        it = iter(self.rt.eval("iter('ab')"))
        self.assertEqual((next(it), next(it)), ("a", "b"))
        with self.assertRaises(StopIteration):
            next(it)
        gen = self.rt.eval("(lambda: (yield 1))()")
        self.assertEqual(list(gen), [1])
        self.assertEqual(dict(self.rt.eval("zip('ab', range(2))")), {"a": 0, "b": 1})

    def test_iteration_errors(self):
        with self.assertRaises(TypeError):
            iter(self.rt.eval("len"))
        with self.assertRaises(TypeError):
            next(self.rt.eval("len"))
        with self.assertRaises(TypeError):
            next(self.rt.call("Point", 1, 2))
        self.rt.exec("def broken():\n    yield 1\n    raise ValueError('mid')")
        gen = self.rt.call("broken")
        self.assertEqual(next(gen), 1)
        with self.assertRaises(Error) as cm:
            next(gen)
        self.assertEqual(cm.exception.type, "ValueError")

    def test_equality_and_hash(self):
        a, b, c = self.rt.call("Point", 1, 2), self.rt.call("Point", 1, 2), self.rt.call("Point", 2, 0)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(len({a, b, c}), 2)
        self.assertLess(a, c)
        self.assertEqual(sorted([c, a]), [a, c])
        self.assertEqual(self.rt["Point"], self.rt["Point"])
        self.assertEqual(self.rt.eval("range(3)"), self.rt.eval("range(3)"))
        self.assertNotEqual(a, object())
        self.assertFalse(a == object())
        with self.assertRaises(TypeError):
            a < object()
        with self.assertRaises(TypeError):
            self.rt.call("Strict") < 1
        with self.assertRaises(TypeError):
            hash(self.rt.eval("type('L', (list,), {})()"))

    def test_equality_across_runtimes(self):
        with Runtime() as other:
            self.assertNotEqual(self.rt.eval("range(1)"), other.eval("range(1)"))

    def test_text(self):
        p = self.rt.call("Point", 1, 2)
        self.assertEqual(repr(p), "Point(1, 2)")
        self.assertEqual(str(p), "(1, 2)")
        self.assertEqual(f"{p}", "(1, 2)")

    def test_dir(self):
        names = dir(self.rt.call("Point", 1, 2))
        self.assertIn("norm", names)
        self.assertIn("x", names)

    def test_closed(self):
        p = self.rt.call("Point", 1, 2)
        it = self.rt.eval("iter(range(3))")
        self.rt.close()
        for op in [lambda: p.x, lambda: setattr(p, "x", 1), lambda: p(), lambda: p["a"], lambda: len(p),
                   lambda: hash(p), lambda: p == p, lambda: bool(p), lambda: str(p), lambda: next(it),
                   lambda: dir(p), lambda: 1 in p]:
            with self.assertRaises(RuntimeError):
                op()
        self.assertEqual(repr(p), "<small_python.Object (closed)>")


if __name__ == "__main__":
    unittest.main()
