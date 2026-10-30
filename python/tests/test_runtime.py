"""Runtime: options, running code, globals, calls, and lifetime."""
import gc
import unittest
import weakref

from small_python import Error, Object, Runtime


class OptionsTest(unittest.TestCase):
    def test_keyword_only(self):
        with self.assertRaises(TypeError):
            Runtime(True)

    def test_validation(self):
        with self.assertRaises(ValueError):
            Runtime(step_limit=-1)
        with self.assertRaises(TypeError):
            Runtime(output="stdout")
        with self.assertRaises(TypeError):
            Runtime(loader=42)
        with self.assertRaises(TypeError):
            Runtime(unknown=1)

    def test_init_twice(self):
        with Runtime() as rt:
            with self.assertRaises(RuntimeError):
                rt.__init__()
            self.assertEqual(rt.eval("1"), 1)

    def test_std(self):
        with Runtime() as rt:
            for name in ["sys", "gc"]:
                with self.subTest(module=name):
                    rt.exec(f"import {name}")
        with Runtime(std=False) as rt:
            with self.assertRaises(Error) as cm:
                rt.exec("import sys")
            self.assertEqual(cm.exception.type, "ModuleNotFoundError")
            self.assertEqual(rt.eval("len(dir(__import__('builtins'))) > 100"), True)

    def test_no_library_modules(self):
        with Runtime() as rt:
            for name in ["os", "json", "math"]:
                with self.subTest(module=name), self.assertRaises(Error):
                    rt.exec(f"import {name}")


class RunTest(unittest.TestCase):
    def setUp(self):
        self.rt = Runtime()

    def tearDown(self):
        self.rt.close()

    def test_eval_returns_last_expression(self):
        self.assertEqual(self.rt.eval("1 + 2"), 3)
        self.assertEqual(self.rt.eval("x = 5\nx * 2"), 10)
        self.assertEqual(self.rt.eval("1; 2"), 2)
        self.assertIsNone(self.rt.eval("y = 1"))
        self.assertIsNone(self.rt.eval(""))

    def test_exec_returns_none(self):
        self.assertIsNone(self.rt.exec("z = [i * i for i in range(4)]"))
        self.assertIsNone(self.rt.exec("z"))
        self.assertEqual(self.rt["z"], [0, 1, 4, 9])

    def test_keywords_and_filename(self):
        self.assertEqual(self.rt.eval(source="2"), 2)
        with self.assertRaises(Error) as cm:
            self.rt.exec(source="\n\n1/0", filename="calc.py")
        self.assertEqual((cm.exception.filename, cm.exception.lineno), ("calc.py", 3))
        with self.assertRaises(Error) as cm:
            self.rt.exec("1/0")
        self.assertEqual(cm.exception.filename, "<string>")

    def test_bad_source_arguments(self):
        with self.assertRaises(TypeError):
            self.rt.eval(b"1")
        with self.assertRaises(ValueError):
            self.rt.eval("1\x00")

    def test_globals_persist(self):
        self.rt.exec("def f(): return counter + 1\ncounter = 1")
        self.assertEqual(self.rt.eval("f()"), 2)
        self.rt["counter"] = 41
        self.assertEqual(self.rt.call("f"), 42)


class GlobalsTest(unittest.TestCase):
    def test_item_access(self):
        with Runtime() as rt:
            rt["a"] = 1
            self.assertEqual(rt["a"], 1)
            self.assertEqual(rt.eval("a"), 1)
            del rt["a"]
            with self.assertRaises(KeyError):
                rt["a"]
            with self.assertRaises(KeyError):
                del rt["a"]
            self.assertFalse(rt.eval("'a' in globals()"))

    def test_builtins_are_readable(self):
        with Runtime() as rt:
            self.assertIsInstance(rt["len"], Object)
            self.assertEqual(rt["len"]([1, 2]), 2)
            with self.assertRaises(KeyError):
                del rt["len"]

    def test_names_must_be_str(self):
        with Runtime() as rt:
            for op in [lambda: rt[1], lambda: rt.__setitem__(b"x", 1), lambda: rt.__delitem__(None)]:
                with self.assertRaisesRegex(TypeError, "global names must be str"):
                    op()

    def test_shadowed_builtins_do_not_affect_conversion(self):
        with Runtime() as rt:
            rt.exec("def set(*a): raise ValueError('user set')\nint = hex = bytearray = frozenset = complex = None")
            rt["v"] = [{1, 2}, frozenset({3}), bytearray(b"x"), 2**100, 1j]
            self.assertEqual(rt["v"], [{1, 2}, frozenset({3}), bytearray(b"x"), 2**100, 1j])
            rt.exec("len = next = hash = dir = None")
            self.assertEqual(len(rt.eval("range(3)")), 3)


class CallTest(unittest.TestCase):
    def test_call_by_name_and_object(self):
        with Runtime() as rt:
            rt.exec("def greet(name, *, end='!'):\n    return 'hi ' + name + end")
            self.assertEqual(rt.call("greet", "a"), "hi a!")
            self.assertEqual(rt.call("greet", "a", end="?"), "hi a?")
            self.assertEqual(rt.call(rt["greet"], name="b"), "hi b!")
            self.assertEqual(rt.call("sorted", [3, 1, 2], reverse=True), [3, 2, 1])
            self.assertEqual(rt.call(len, "abc"), 3)

    def test_call_errors(self):
        with Runtime() as rt:
            with self.assertRaises(TypeError):
                rt.call()
            with self.assertRaises(Error) as cm:
                rt.call("missing")
            self.assertEqual(cm.exception.type, "NameError")
            with self.assertRaises(Error) as cm:
                rt.call("len", 1, 2)
            self.assertEqual(cm.exception.type, "TypeError")
            with self.assertRaises(TypeError):
                rt.call("len", object())


class StepLimitTest(unittest.TestCase):
    def test_stops_loops(self):
        with Runtime(step_limit=1000) as rt:
            with self.assertRaises(Error) as cm:
                rt.exec("while True: pass")
            self.assertEqual(cm.exception.type, "RuntimeError")
            self.assertEqual(rt.eval("1 + 1"), 2)

    def test_count_restarts_per_eval(self):
        with Runtime(step_limit=5000) as rt:
            for _ in range(5):
                rt.exec("for i in range(100): pass")

    def test_host_functions_cannot_reset_the_count(self):
        with Runtime(step_limit=2000) as rt:
            rt.define("touch", lambda: (rt.__setitem__("t", 1), rt.__delitem__("t"), rt["len"])[0])
            with self.assertRaises(Error):
                rt.exec("for i in range(5000):\n    touch()")


class LifetimeTest(unittest.TestCase):
    def test_context_manager(self):
        with Runtime() as rt:
            self.assertFalse(rt.closed)
        self.assertTrue(rt.closed)

    def test_closed_runtime(self):
        rt = Runtime()
        obj = rt.eval("object()")
        rt.close()
        rt.close()
        for op in [lambda: rt.eval("1"), lambda: rt.exec("1"), lambda: rt["x"], lambda: rt.call("len", []),
                   lambda: rt.define("f", print), lambda: rt.register_module("m"), lambda: rt.mount("."),
                   lambda: rt.collect(), lambda: rt.__setitem__("x", 1)]:
            with self.assertRaises(RuntimeError):
                op()
        self.assertIn("closed", repr(obj))
        with self.assertRaises(RuntimeError):
            str(obj)

    def test_objects_keep_runtime_alive(self):
        obj = Runtime().eval("[1, object()]")[1]
        self.assertIn("object", repr(obj))

    def test_runtime_is_freed(self):
        rt = Runtime()
        rt.eval("object()")
        ref = weakref.ref(rt)
        del rt
        gc.collect()
        self.assertIsNone(ref())

    def test_collect(self):
        with Runtime() as rt:
            rt.exec("class N: pass\nfor _ in range(10):\n    a = N(); a.me = a\ndel a")
            self.assertGreaterEqual(rt.collect(), 10)
            self.assertEqual(rt.collect(), 0)

    def test_independent_runtimes(self):
        with Runtime() as a, Runtime() as b:
            a["x"] = 1
            with self.assertRaises(KeyError):
                b["x"]
            with self.assertRaises(ValueError):
                b["y"] = a.eval("object()")
            with self.assertRaises(ValueError):
                b.call(a["len"], [])

    def test_many_runtimes(self):
        for _ in range(200):
            with Runtime() as rt:
                rt["x"] = list(range(10))
                self.assertEqual(rt.eval("sum(x)"), 45)

    def test_subclass(self):
        class Mine(Runtime):
            def __init__(self, **kwargs):
                super().__init__(std=False, **kwargs)
                self.extra = 1

        with Mine(step_limit=10) as rt:
            self.assertEqual((rt.eval("2"), rt.extra), (2, 1))


if __name__ == "__main__":
    unittest.main()
