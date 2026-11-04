"""Host services: registered and native modules, the loader, output, and mounts."""
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

from small_python import Error, Runtime, WorkerError


class ModuleTest(unittest.TestCase):
    def test_members_and_source(self):
        with Runtime() as rt:
            rt.register_module("host", {"answer": 42, "twice": lambda n: n * 2},
                               source="def quad(n):\n    return twice(twice(n))")
            rt.exec("import host\nfrom host import twice")
            self.assertEqual(rt.eval("host.quad(host.answer)"), 168)
            self.assertEqual(rt.eval("twice(4)"), 8)
            self.assertEqual(rt.eval("host.__name__"), "host")

    def test_built_on_first_import(self):
        with Runtime() as rt:
            rt.register_module("lazy", source="import counter\ncounter.n += 1")
            rt.register_module("counter", source="n = 0")
            rt.exec("import lazy, lazy, counter")
            self.assertEqual(rt.eval("counter.n"), 1)

    def test_members_or_source_alone(self):
        with Runtime() as rt:
            rt.register_module("a", {"x": 1})
            rt.register_module("b", source="y = 2")
            rt.register_module("c")
            self.assertEqual(rt.eval("__import__('a').x, __import__('b').y"), (1, 2))
            rt.exec("import c")

    def test_registered_before_loader(self):
        with Runtime(loader=lambda name: "where = 'loader'") as rt:
            rt.register_module("m", source="where = 'registered'")
            self.assertEqual(rt.eval("__import__('m').where"), "registered")

    def test_validation(self):
        with Runtime() as rt:
            with self.assertRaises(TypeError):
                rt.register_module("m", ["x"])
            with self.assertRaises(TypeError):
                rt.register_module("m", {1: "x"})
            with self.assertRaises(TypeError):
                rt.register_module("m", source=b"x = 1")
            with self.assertRaises(TypeError):
                rt.register_module(b"m")

    def test_import_errors(self):
        with Runtime() as rt:
            rt.register_module("syntax", source="1 +")
            rt.register_module("raises", source="raise KeyError('in module')")
            with self.assertRaises(TypeError):
                rt.register_module("member", {"x": object()})
            for name, kind in [("syntax", "SyntaxError"), ("raises", "KeyError")]:
                with self.subTest(module=name):
                    with self.assertRaises(Error) as cm:
                        rt.exec(f"import {name}")
                    self.assertEqual(cm.exception.type, kind)


class LoaderTest(unittest.TestCase):
    def test_loads_source(self):
        calls = []

        def load(name):
            calls.append(name)
            return {"greeting": "WORD = 'hi'"}.get(name)

        with Runtime(loader=load) as rt:
            rt.exec("import greeting\nimport greeting")
            self.assertEqual(rt.eval("greeting.WORD"), "hi")
            with self.assertRaises(Error) as cm:
                rt.exec("import nowhere")
            self.assertEqual(cm.exception.type, "ModuleNotFoundError")
        self.assertEqual(calls.count("greeting"), 1)

    def test_loader_errors(self):
        def broken(name):
            raise ValueError("loader broke")

        with Runtime(loader=broken) as rt:
            with self.assertRaises(Error) as cm:
                rt.exec("import x")
            self.assertEqual(cm.exception.type, "ValueError")
            self.assertIsInstance(cm.exception.__cause__, ValueError)
        with Runtime(loader=lambda name: b"x = 1") as rt:
            with self.assertRaises(Error) as cm:
                rt.exec("import x")
            self.assertEqual(cm.exception.type, "TypeError")

    def test_loader_cannot_reenter(self):
        holder = []
        with Runtime(loader=lambda name: holder[0].eval("1") and "x = 1") as rt:
            holder.append(rt)
            with self.assertRaises(Error) as cm:
                rt.exec("import x")
            self.assertEqual(cm.exception.type, "RuntimeError")


class OutputTest(unittest.TestCase):
    def test_callback(self):
        out = []
        with Runtime(output=out.append) as rt:
            rt.exec("print('a', 1)\nprint('b', end='')\nprint('\\ud800é')")
        self.assertEqual("".join(out), "a 1\nb\ud800é\n")

    def test_default_is_sys_stdout(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer), Runtime() as rt:
            rt.exec("print('to stdout')\nimport sys\nsys.stdout.write('direct\\n')")
        self.assertEqual(buffer.getvalue(), "to stdout\ndirect\n")

    def test_failing_output(self):
        def broken(text):
            raise ValueError("output broke")

        hook, sys.unraisablehook = sys.unraisablehook, lambda info: None
        try:
            with Runtime(output=broken) as rt:
                with self.assertRaises(Error) as cm:
                    rt.exec("print('x')")
                self.assertEqual(cm.exception.type, "OSError")
        finally:
            sys.unraisablehook = hook

    def test_output_cannot_reenter(self):
        holder = []
        with Runtime(output=lambda text: holder[0].eval("1")) as rt:
            holder.append(rt)
            hook, sys.unraisablehook = sys.unraisablehook, lambda info: None
            try:
                with self.assertRaises(Error):
                    rt.exec("print('x')")
            finally:
                sys.unraisablehook = hook

    def test_input_is_not_available(self):
        with Runtime() as rt:
            with self.assertRaises(Error) as cm:
                rt.eval("input()")
            self.assertEqual(cm.exception.type, "EOFError")


@unittest.skipIf(sys.platform == "win32", "open() needs a POSIX host")
class MountTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = self.directory.name
        with open(os.path.join(self.path, "data.txt"), "w") as f:
            f.write("hello")

    def tearDown(self):
        self.directory.cleanup()

    def test_nothing_mounted(self):
        with Runtime() as rt:
            for source in ["open('x.txt', 'w')", f"open({os.path.join(self.path, 'data.txt')!r})"]:
                with self.assertRaises(Error) as cm:
                    rt.exec(source)
                self.assertEqual(cm.exception.type, "PermissionError")

    def test_read_write(self):
        with Runtime() as rt:
            rt.mount(self.path, "/work")
            self.assertEqual(rt.eval("open('/work/data.txt').read()"), "hello")
            rt.exec("with open('/work/out.txt', 'w') as f:\n    f.write('hi')")
            with open(os.path.join(self.path, "out.txt")) as f:
                self.assertEqual(f.read(), "hi")
            self.assertEqual(rt.eval("open('out.txt').read()"), "hi")

    def test_default_path_and_pathlike(self):
        from pathlib import Path
        with Runtime() as rt:
            rt.mount(Path(self.path))
            real = os.path.realpath(self.path)
            self.assertEqual(rt.eval(f"open({os.path.join(real, 'data.txt')!r}).read()"), "hello")

    def test_read_only(self):
        with Runtime() as rt:
            rt.mount(self.path, "/ro", read_only=True)
            self.assertEqual(rt.eval("open('/ro/data.txt').read()"), "hello")
            with self.assertRaises(Error) as cm:
                rt.exec("open('/ro/new.txt', 'w')")
            self.assertEqual(cm.exception.type, "OSError")
            self.assertFalse(os.path.exists(os.path.join(self.path, "new.txt")))

    def test_cannot_escape(self):
        os.symlink("/etc", os.path.join(self.path, "link"))
        with Runtime() as rt:
            rt.mount(self.path, "/work")
            for path in ["/work/../etc/hosts", "/work/link/hosts", "../etc/hosts"]:
                with self.subTest(path=path):
                    with self.assertRaises(Error):
                        rt.exec(f"open({path!r})")

    def test_errors(self):
        with Runtime() as rt:
            with self.assertRaises(Error):
                rt.mount(os.path.join(self.path, "missing"))
            with self.assertRaises(TypeError):
                rt.mount(self.path, "/x", True)
            with self.assertRaises(TypeError):
                rt.mount(42)


class NativeTest(unittest.TestCase):
    """The example native module, compiled here, so every platform the wheels
    are tested on loads one built for it."""

    @classmethod
    def setUpClass(cls):
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
        cls.directory = tempfile.TemporaryDirectory()
        cls.path = os.path.join(cls.directory.name, "fib.dll" if sys.platform == "win32" else "fib.so")
        crash = os.path.join(cls.directory.name, "crash.c")
        with open(crash, "w") as f:
            f.write('#include <stdlib.h>\n#include "spy-module.h"\n'
                    "SPY_MODULE int spy_init_crash(SPYContext *c, SPYValue *m) { (void)c, (void)m; abort(); }\n")
        cls.crash = os.path.splitext(crash)[0] + os.path.splitext(cls.path)[1]
        compiler = os.environ.get("CC", "gcc" if sys.platform == "win32" else "cc")
        for source, library in [(os.path.join(root, "examples", "fib.c"), cls.path), (crash, cls.crash)]:
            subprocess.run([compiler, "-shared", "-fPIC", "-DSPY_SHARED_MODULE", "-I", root, source, "-o", library],
                           check=True)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_load(self):
        with Runtime() as rt:
            rt.load_native("fib", self.path)
            self.assertEqual(rt.eval("__import__('fib').fib(50)"), 12586269025)
            with self.assertRaises(Error) as cm:
                rt.exec("import fib\nfib.fib(-1)")
            self.assertEqual(str(cm.exception), "ValueError: fib() argument must be in 0..92")

    def test_policy(self):
        events = []

        def policy(event, args):
            if event == "dlopen":
                events.append(args)
                if args[0] == "refused":
                    raise PermissionError("no native code")

        real = os.path.realpath(self.path)
        with Runtime(policy=policy) as rt:
            rt.load_native("fib", self.path)
            with self.assertRaises(Error) as cm:
                rt.load_native("refused", self.path)
            self.assertEqual(str(cm.exception), "PermissionError: no native code")
            self.assertEqual(events, [("fib", real), ("refused", real)])
            self.assertEqual(rt.eval("__import__('fib').fib(10)"), 55)

    def test_failures(self):
        with Runtime() as rt:
            for name, path in [("missing", self.path + ".missing"), ("source", __file__)]:
                with self.subTest(name=name), self.assertRaises(Error) as cm:
                    rt.load_native(name, path)
                self.assertEqual(cm.exception.type, "ImportError")
            with self.assertRaises(Error) as cm:
                rt.load_native("other", self.path)
            self.assertEqual(cm.exception.message,
                             "dynamic module does not define module export function (spy_init_other)")
            for name, path in [("fib\0", self.path), ("fib", self.path + "\0")]:
                with self.assertRaisesRegex(ValueError, "^embedded null character$"):
                    rt.load_native(name, path)
            with self.assertRaises(TypeError):
                rt.load_native(42, self.path)
            with self.assertRaises(Error) as cm:
                rt.exec("import missing")
            self.assertEqual(cm.exception.type, "ModuleNotFoundError")

    def test_worker_refuses_null_characters(self):
        # The worker's own check (protocol.md 7.1), for parents that send NUL.
        from small_python import _wire
        with Runtime() as rt:
            for name, path in [("fib\0", self.path), ("fib", self.path + "\0")]:
                with self.assertRaises(Error) as cm:
                    rt._run(_wire.NATIVE, name, path)
                self.assertEqual(str(cm.exception), "ValueError: embedded null character")

    def test_crashing_init_loses_only_the_runtime(self):
        with Runtime() as rt:
            rt.load_native("crash", self.crash)
            with self.assertRaises(WorkerError):
                rt.exec("import crash")
            with self.assertRaises(WorkerError):
                rt.eval("1")
        with Runtime() as rt:
            self.assertEqual(rt.eval("6 * 7"), 42)

    def test_only_before_code_runs(self):
        with Runtime() as rt:
            rt.exec("pass")
            with self.assertRaises(Error) as cm:
                rt.load_native("fib", self.path)
            self.assertEqual(str(cm.exception), "PermissionError: cannot load a native module after code has run")


@unittest.skipUnless(sys.platform == "win32", "open() reaches mounts on POSIX hosts")
class NoFilesTest(unittest.TestCase):
    def test_mount_unsupported(self):
        with tempfile.TemporaryDirectory() as path, Runtime() as rt:
            with self.assertRaises(Error) as cm:
                rt.mount(path)
            self.assertEqual(cm.exception.type, "OSError")


if __name__ == "__main__":
    unittest.main()
