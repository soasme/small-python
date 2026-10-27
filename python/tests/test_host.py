"""Host functions: Python callables called from engine code."""
import sys
import threading
import unittest

from small_python import Error, Object, Runtime


class DefineTest(unittest.TestCase):
    def test_define_and_decorator(self):
        with Runtime() as rt:
            @rt.function
            def add(a, b=10, *, scale=1):
                return (a + b) * scale

            @rt.function(name="shout")
            def upper(text):
                return text.upper()

            self.assertEqual(rt.define("neg", lambda n: -n).__name__, "<lambda>")
            self.assertEqual(rt.eval("add(1)"), 11)
            self.assertEqual(rt.eval("add(1, 2, scale=3)"), 9)
            self.assertEqual(rt.eval("add(*[1, 2], **{'scale': 2})"), 6)
            self.assertEqual(rt.eval("shout('x'), neg(3)"), ("X", -3))
            self.assertEqual(rt.eval("add.__name__, shout.__name__"), ("add", "shout"))
            self.assertEqual(upper("y"), "Y")

    def test_define_validation(self):
        with Runtime() as rt:
            with self.assertRaises(TypeError):
                rt.define("x", 1)
            with self.assertRaises(TypeError):
                rt.define(1, print)

    def test_arguments_and_results_convert(self):
        seen = []
        with Runtime() as rt:
            rt.define("record", lambda *args, **kwargs: seen.append((args, kwargs)) or [args, kwargs])
            rt.exec("class P: pass")
            self.assertEqual(rt.eval("record(1, 'a', [2], k=b'v')"), [(1, "a", [2]), {"k": b"v"}])
            rt.eval("record(P())")
            self.assertIsInstance(seen[-1][0][0], Object)

    def test_callables_passed_as_values(self):
        with Runtime() as rt:
            rt["double"] = lambda n: n * 2
            self.assertEqual(rt.eval("double(4)"), 8)
            self.assertEqual(rt.eval("list(map(double, [1, 2]))"), [2, 4])
            self.assertEqual(rt.call("sorted", ["bb", "a"], key=len), ["a", "bb"])
            self.assertIsInstance(rt["double"], Object)
            self.assertEqual(rt["double"](5), 10)

    def test_unconvertible_result(self):
        with Runtime() as rt:
            rt.define("bad", lambda: object())
            rt.exec("try:\n    bad()\nexcept TypeError as e:\n    msg = str(e)")
            self.assertIn("cannot convert", rt["msg"])

    def test_callable_released_on_close(self):
        class Probe:
            def __call__(self):
                return 1

        probe = Probe()
        before = sys.getrefcount(probe)
        rt = Runtime()
        rt.define("probe", probe)
        rt["again"] = probe
        rt.register_module("m", {"p": probe})
        rt.exec("import m")
        self.assertGreater(sys.getrefcount(probe), before)
        rt.close()
        self.assertEqual(sys.getrefcount(probe), before)


class HostExceptionTest(unittest.TestCase):
    def test_mapped_to_builtin_classes(self):
        class NotFound(KeyError):
            pass

        class Custom(Exception):
            pass

        errors = {"key": KeyError("k"), "zero": ZeroDivisionError("z"), "sub": NotFound("n"),
                  "custom": Custom("c", 2), "warning": RuntimeWarning("w"), "base": GeneratorExit()}
        with Runtime() as rt:
            def fail(kind):
                raise errors[kind]

            rt.define("fail", fail)
            rt.exec("def catch(kind):\n    try:\n        fail(kind)\n    except BaseException as e:\n"
                    "        return type(e).__name__, e.args")
            self.assertEqual(rt.call("catch", "key"), ("KeyError", ("k",)))
            self.assertEqual(rt.call("catch", "zero"), ("ZeroDivisionError", ("z",)))
            self.assertEqual(rt.call("catch", "sub"), ("KeyError", ("n",)))
            self.assertEqual(rt.call("catch", "custom"), ("Exception", ("c", 2)))
            self.assertEqual(rt.call("catch", "warning"), ("RuntimeWarning", ("w",)))
            self.assertEqual(rt.call("catch", "base"), ("GeneratorExit", ()))

    def test_engine_globals_do_not_capture_exceptions(self):
        class Config(Exception):
            pass

        def load():
            raise Config("bad config")

        with Runtime() as rt:
            rt.exec("class Config: pass\nclass ValueError: pass")
            rt.define("load", load)
            rt.define("value", lambda: int("x"))
            rt.exec("try:\n    load()\nexcept Exception as e:\n    a = type(e).__name__")
            rt.exec("try:\n    value()\nexcept __import__('builtins').ValueError as e:\n    b = type(e).__name__")
            self.assertEqual((rt["a"], rt["b"]), ("Exception", "ValueError"))

    def test_unconvertible_args_fall_back_to_message(self):
        with Runtime() as rt:
            def fail():
                raise ValueError(object(), "x")

            rt.define("fail", fail)
            rt.exec("try:\n    fail()\nexcept ValueError as e:\n    n = len(e.args)\n    m = e.args[0]")
            self.assertEqual(rt["n"], 1)
            self.assertIn("object", rt["m"])

    def test_uncaught_exception_is_the_cause(self):
        original = LookupError("gone")

        def fail():
            raise original

        with Runtime() as rt:
            rt.define("fail", fail)
            with self.assertRaises(Error) as cm:
                rt.eval("fail()")
            self.assertEqual(cm.exception.type, "LookupError")
            self.assertIs(cm.exception.__cause__, original)
            with self.assertRaises(Error) as cm:
                rt.eval("1/0")
            self.assertIsNone(cm.exception.__cause__)

    def test_handled_then_new_error_has_no_cause(self):
        with Runtime() as rt:
            rt.define("fail", lambda: 1 / 0)
            with self.assertRaises(Error) as cm:
                rt.exec("try:\n    fail()\nexcept ZeroDivisionError:\n    raise ValueError('other')")
            self.assertEqual(cm.exception.type, "ValueError")
            self.assertIsNone(cm.exception.__cause__)

    def test_keyboard_interrupt_and_system_exit_pass_through(self):
        for exc in [KeyboardInterrupt(), SystemExit(3)]:
            with self.subTest(exc=type(exc).__name__), Runtime() as rt:
                def stop():
                    raise exc

                rt.define("stop", stop)
                with self.assertRaises(type(exc)) as cm:
                    rt.exec("try:\n    stop()\nexcept Exception:\n    pass")
                self.assertIs(cm.exception, exc)
                self.assertEqual(rt.eval("1"), 1)

    def test_engine_error_through_host_keeps_identity(self):
        with Runtime() as rt:
            rt.exec("class Oops(Exception): pass\ndef bad(): raise Oops('deep')")
            rt.define("relay", lambda f: f())
            rt.exec("try:\n    relay(bad)\nexcept Oops as e:\n    caught = (type(e).__name__, str(e))")
            self.assertEqual(rt["caught"], ("Oops", "deep"))


class ReentryTest(unittest.TestCase):
    def test_callbacks_into_engine(self):
        with Runtime() as rt:
            rt.exec("def square(n): return n * n")
            rt.define("apply", lambda f, n: f(n))
            rt.define("lookup", lambda: rt["square"](3) + rt.call("square", 2))
            self.assertEqual(rt.eval("apply(square, 7)"), 49)
            self.assertEqual(rt.eval("lookup()"), 13)

    def test_eval_exec_close_refused(self):
        with Runtime() as rt:
            for name, op in [("eval", lambda: rt.eval("1")), ("exec", lambda: rt.exec("1")), ("close", rt.close)]:
                with self.subTest(op=name):
                    rt.define("reenter", op)
                    with self.assertRaises(Error) as cm:
                        rt.eval("reenter()")
                    self.assertEqual(cm.exception.type, "RuntimeError")
            self.assertFalse(rt.closed)

    def test_other_runtimes_are_usable(self):
        with Runtime() as rt, Runtime() as other:
            rt.define("ask", lambda: other.eval("6 * 7"))
            self.assertEqual(rt.eval("ask()"), 42)

    def test_other_thread_refused_during_callback(self):
        results = []
        with Runtime() as rt:
            def use_from_thread():
                for op in [lambda: rt["x"], lambda: rt.eval("1"), lambda: rt.close(), lambda: obj.n]:
                    try:
                        op()
                        results.append("ran")
                    except RuntimeError as e:
                        results.append(str(e))

            def host():
                thread = threading.Thread(target=use_from_thread)
                thread.start()
                thread.join()
                return rt["x"]

            rt["x"] = 1
            rt.exec("class O: n = 1")
            obj = rt.call("O")
            rt.define("host", host)
            self.assertEqual(rt.eval("host()"), 1)
        self.assertEqual(results, ["the runtime is in use by another thread"] * 4)

    def test_threads_with_separate_runtimes(self):
        totals = {}

        def work(i):
            with Runtime() as rt:
                rt.define("slow", lambda n: n)
                totals[i] = rt.eval("sum(slow(n) for n in range(2000))")

        threads = [threading.Thread(target=work, args=(i,)) for i in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(totals, {i: sum(range(2000)) for i in range(4)})


if __name__ == "__main__":
    unittest.main()
