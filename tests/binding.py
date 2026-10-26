"""Tests for the smallpython CPython binding (python/smallpython).

Run with a Python that has the extension built, e.g.
    python3 setup.py build_ext --inplace && PYTHONPATH=python python3 tests/binding.py
"""
import gc
import sys
import unittest

import smallpython
from smallpython import Error, Object, Runtime


class ValuesTest(unittest.TestCase):
    def setUp(self):
        self.rt = Runtime()

    def tearDown(self):
        self.rt.close()

    def test_round_trip(self):
        for value in [None, True, False, 0, -7, 2**100, -(2**70), 1.5, 2+3j, "", "héllo\U0001f600",
                      b"\x00b", bytearray(b"ab"), [1, [2]], (1, "a"), {"k": [1]}, {1, 2}, frozenset({3})]:
            with self.subTest(value=value):
                self.rt["x"] = value
                got = self.rt.eval("x")
                self.assertEqual(got, value)
                self.assertIs(type(got), type(value))

    def test_eval_and_exec(self):
        self.assertEqual(self.rt.eval("1 + 2"), 3)
        self.assertIsNone(self.rt.exec("y = [i * i for i in range(4)]"))
        self.assertEqual(self.rt["y"], [0, 1, 4, 9])
        with self.assertRaises(KeyError):
            self.rt["missing"]
        del self.rt["y"]
        with self.assertRaises(KeyError):
            del self.rt["y"]

    def test_objects(self):
        self.rt.exec("class P:\n    def __init__(self, n): self.n = n\n    def double(self): return self.n * 2\n"
                     "    def __repr__(self): return f'P({self.n})'")
        p = self.rt.call("P", 21)
        self.assertIsInstance(p, Object)
        self.assertEqual(p.n, 21)
        self.assertEqual(p.double(), 42)
        p.n = 5
        self.assertEqual(self.rt.call(self.rt["P"].double, p), 10)
        self.assertEqual(repr(p), "P(5)")
        self.assertIs(p.runtime, self.rt)
        with self.assertRaises(AttributeError):
            p.missing
        self.assertEqual(list(self.rt.eval("iter(range(3))")), [0, 1, 2])
        self.assertEqual(self.rt.call("sorted", [3, 1, 2], reverse=True), [3, 2, 1])

    def test_errors(self):
        with self.assertRaises(Error) as cm:
            self.rt.exec("x = 1\nraise ValueError('bad')", filename="prog.py")
        error = cm.exception
        self.assertEqual((error.type, error.message), ("ValueError", "bad"))
        self.assertEqual((error.filename, error.lineno), ("prog.py", 2))
        self.assertIsInstance(error.exception, Object)
        self.assertEqual(str(error), "ValueError: bad")
        with self.assertRaises(TypeError):
            self.rt["x"] = object()


class HostFunctionTest(unittest.TestCase):
    def test_define_and_keywords(self):
        with Runtime() as rt:
            @rt.function
            def add(a, b=10, *, scale=1):
                return (a + b) * scale
            self.assertEqual(rt.eval("add(1)"), 11)
            self.assertEqual(rt.eval("add(1, 2, scale=3)"), 9)
            rt.define("upper", str.upper)
            self.assertEqual(rt.eval("upper('x')"), "X")
            self.assertEqual(rt.eval("add.__name__"), "add")

    def test_exceptions_cross_the_boundary(self):
        with Runtime() as rt:
            @rt.function
            def fail(kind):
                raise {"key": KeyError, "zero": ZeroDivisionError, "custom": RuntimeWarning}[kind]("boom")
            rt.exec("def catch(kind):\n    try:\n        fail(kind)\n    except LookupError as e:\n        return 'lookup', str(e)\n"
                    "    except ArithmeticError as e:\n        return 'arith', str(e)\n    except Exception as e:\n        return type(e).__name__, str(e)")
            self.assertEqual(rt.call("catch", "key"), ("lookup", "'boom'"))
            self.assertEqual(rt.call("catch", "zero"), ("arith", "boom"))
            self.assertEqual(rt.call("catch", "custom"), ("RuntimeWarning", "boom"))

    def test_callbacks_reenter(self):
        with Runtime() as rt:
            rt.exec("def square(n): return n * n")
            rt.define("apply", lambda f, n: f(n))
            self.assertEqual(rt.eval("apply(square, 7)"), 49)
            rt.define("nested", lambda: rt.eval("1"))
            with self.assertRaises(Error) as cm:
                rt.eval("nested()")
            self.assertEqual(cm.exception.type, "RuntimeError")

    def test_engine_error_through_host(self):
        with Runtime() as rt:
            rt.exec("def bad(): raise IndexError('deep')")
            rt.define("relay", lambda f: f())
            rt.exec("try:\n    relay(bad)\nexcept IndexError as e:\n    caught = str(e)")
            self.assertEqual(rt["caught"], "deep")

    def test_callable_released(self):
        class Probe:
            def __call__(self):
                return 1
        probe = Probe()
        before = sys.getrefcount(probe)
        rt = Runtime()
        rt.define("probe", probe)
        rt["again"] = probe
        self.assertGreater(sys.getrefcount(probe), before)
        rt.close()
        self.assertEqual(sys.getrefcount(probe), before)


class RuntimeTest(unittest.TestCase):
    def test_output(self):
        out = []
        with Runtime(output=out.append) as rt:
            rt.exec("print('a', 1)\nprint('b', end='')")
        self.assertEqual("".join(out), "a 1\nb")

    def test_modules(self):
        with Runtime() as rt:
            rt.register_module("host", {"answer": 42, "twice": lambda n: n * 2},
                               source="def quad(n):\n    return twice(twice(n))")
            self.assertEqual(rt.eval("__import__('host').quad(answer := __import__('host').answer)"), 168)
            rt.exec("from host import twice")
            self.assertEqual(rt.eval("twice(4)"), 8)

    def test_loader(self):
        sources = {"greeting": "WORD = 'hi'"}
        with Runtime(loader=sources.get) as rt:
            rt.exec("import greeting")
            self.assertEqual(rt.eval("greeting.WORD"), "hi")
            with self.assertRaises(Error) as cm:
                rt.exec("import nowhere")
            self.assertEqual(cm.exception.type, "ModuleNotFoundError")

    def test_std(self):
        with Runtime() as rt:
            self.assertEqual(rt.eval("__import__('sys').maxsize > 0"), True)
        with Runtime(std=False) as rt:
            with self.assertRaises(Error):
                rt.exec("import sys")
            self.assertEqual(rt.eval("len(dir(__import__('builtins'))) > 100"), True)

    def test_step_limit(self):
        with Runtime(step_limit=1000) as rt:
            with self.assertRaises(Error):
                rt.exec("while True: pass")

    def test_close(self):
        rt = Runtime()
        obj = rt.eval("object()")
        rt.close()
        self.assertTrue(rt.closed)
        with self.assertRaises(RuntimeError):
            rt.eval("1")
        with self.assertRaises(RuntimeError):
            str(obj)
        self.assertIn("closed", repr(obj))
        rt.close()

    def test_cycles_collected(self):
        with Runtime() as rt:
            rt.exec("class N: pass\nfor _ in range(10):\n    a = N(); a.me = a\ndel a")
            self.assertGreaterEqual(rt.collect(), 10)

    def test_independent(self):
        a, b = Runtime(), Runtime()
        a["x"] = 1
        with self.assertRaises(KeyError):
            b["x"]
        with self.assertRaises(ValueError):
            b["y"] = a.eval("object()")
        a.close(); b.close()
        gc.collect()

    def test_version(self):
        self.assertEqual(smallpython.__version__, smallpython.SPY_VERSION)


if __name__ == "__main__":
    unittest.main()
