"""The package surface: exports, versions, Error, and type information."""
import importlib.resources
import re
import unittest

import small_python
from small_python import Error, Object, Runtime


class PackageTest(unittest.TestCase):
    def test_exports(self):
        self.assertEqual(sorted(small_python.__all__), ["Error", "Object", "Runtime", "SPY_VERSION", "Timeout", "WorkerError"])
        for name in small_python.__all__:
            self.assertTrue(hasattr(small_python, name))

    def test_versions(self):
        self.assertRegex(small_python.SPY_VERSION, r"^\d+\.\d+\.\d+")
        self.assertIsInstance(small_python.__version__, str)
        with Runtime() as rt:
            self.assertIn("Small Python", rt.eval("__import__('sys').version"))

    def test_typed(self):
        files = importlib.resources.files("small_python")
        self.assertTrue(files.joinpath("py.typed").is_file())
        stub = files.joinpath("_runtime.pyi").read_text()
        for name in ["class Runtime", "class Object", "class Error", "class WorkerError", "class Timeout", "def eval", "def exec",
                     "def call", "def define", "def register_module", "def mount", "def collect", "def close"]:
            self.assertIn(name, stub)

    def test_stub_matches_runtime_methods(self):
        stub = importlib.resources.files("small_python").joinpath("_runtime.pyi").read_text()
        runtime = stub[stub.index("class Runtime"):stub.index("class Object")]
        stubbed = set(re.findall(r"def (\w+)", runtime)) - {"__init__"}
        public = {name for name in dir(Runtime) if not name.startswith("_")}
        self.assertEqual(stubbed - {"__getitem__", "__setitem__", "__delitem__", "__enter__", "__exit__", "closed"},
                         public - {"closed"})


class ErrorTest(unittest.TestCase):
    def test_attributes(self):
        with Runtime() as rt:
            with self.assertRaises(Error) as cm:
                rt.exec("x = 1\nraise ValueError('bad')", filename="prog.py")
        error = cm.exception
        self.assertIsInstance(error, Exception)
        self.assertEqual((error.type, error.message), ("ValueError", "bad"))
        self.assertEqual((error.filename, error.lineno), ("prog.py", 2))
        self.assertIsInstance(error.exception, Object)
        self.assertEqual(str(error), "ValueError: bad")

    def test_engine_exception_object(self):
        with Runtime() as rt:
            rt.exec("class Quota(Exception):\n    def __init__(self, used):\n        super().__init__('over')\n"
                    "        self.used = used")
            with self.assertRaises(Error) as cm:
                rt.exec("raise Quota(120)")
            self.assertEqual(cm.exception.type, "__main__.Quota")
            self.assertEqual(cm.exception.exception.used, 120)
            self.assertEqual(cm.exception.exception.args, ("over",))

    def test_without_message(self):
        with Runtime() as rt:
            with self.assertRaises(Error) as cm:
                rt.exec("raise KeyError")
        self.assertEqual(str(cm.exception), "KeyError")
        self.assertEqual(cm.exception.message, "")

    def test_syntax_error(self):
        with Runtime() as rt:
            with self.assertRaises(Error) as cm:
                rt.exec("x = 1\nif x\n", filename="bad.py")
        self.assertEqual(cm.exception.type, "SyntaxError")
        self.assertEqual((cm.exception.filename, cm.exception.lineno), ("bad.py", 2))

    def test_constructed_directly(self):
        error = Error("ValueError", "m")
        self.assertEqual((error.type, error.message, error.exception), ("ValueError", "m", None))
        self.assertIsNone(error.filename)
        self.assertIsNone(error.lineno)
        self.assertEqual(str(error), "ValueError: m")
        self.assertIsNone(Error().type)


if __name__ == "__main__":
    unittest.main()
