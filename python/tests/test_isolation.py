"""The worker boundary: crashes, hostile workers, limits, and interruption."""
import os
import signal
import struct
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from unittest import mock

import small_python._runtime as runtime_module
from small_python import Error, Runtime, Timeout, WorkerError


class CrashTest(unittest.TestCase):
    def test_signals_mid_operation(self):
        for number in (signal.SIGSEGV, signal.SIGABRT, signal.SIGKILL):
            with self.subTest(signal=number.name):
                rt = Runtime()
                rt.define("crash", lambda: os.kill(rt._process.pid, number) or time.sleep(5))
                with self.assertRaises(WorkerError) as cm:
                    rt.eval("crash()")
                self.assertEqual(cm.exception.returncode, -number)
                self.assertIn(number.name, str(cm.exception))
                self.assertTrue(rt.closed)
                with self.assertRaises(WorkerError):
                    rt.eval("1")
                rt.close()

    def test_objects_of_a_lost_runtime(self):
        rt = Runtime()
        obj = rt.eval("object()")
        os.kill(rt._process.pid, signal.SIGKILL)
        with self.assertRaises(WorkerError):
            rt.eval("1")
        with self.assertRaises(WorkerError):
            str(obj)
        del obj

    def test_other_runtimes_survive(self):
        with Runtime() as healthy:
            doomed = Runtime()
            os.kill(doomed._process.pid, signal.SIGKILL)
            with self.assertRaises(WorkerError):
                doomed.eval("1")
            self.assertEqual(healthy.eval("6 * 7"), 42)

    def test_cannot_start(self):
        with mock.patch.object(runtime_module, "WORKER", "/nonexistent/spy-worker"):
            with self.assertRaises(WorkerError):
                Runtime()


def fake_worker(body):
    """A worker that answers INIT, then runs body (Python) with send(bytes)."""
    script = textwrap.dedent(f"""\
        #!{sys.executable}
        import os, struct, sys
        def read(n):
            data = b""
            while len(data) < n:
                chunk = os.read(0, n - len(data))
                if not chunk:
                    sys.exit(0)
                data += chunk
            return data
        def receive():
            return read(struct.unpack("<I", read(4))[0])
        def send(payload):
            os.write(1, struct.pack("<I", len(payload)) + payload)
        receive()
        send(b"\\x40s" + struct.pack("<I", 5) + b"0.1.0")
        receive()
    """) + textwrap.dedent(body)
    handle, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(handle, "w") as f:
        f.write(script)
    os.chmod(path, 0o700)
    return path


def u32(n):
    return struct.pack("<I", n)


def string(s):
    return b"s" + u32(len(s)) + s


class HostileWorkerTest(unittest.TestCase):
    CASES = {
        "unknown kind": 'send(b"\\x7f")',
        "unknown tag": 'send(b"\\x40?")',
        "truncated value": 'send(b"\\x40i\\x01")',
        "trailing bytes": 'send(b"\\x40NN")',
        "length over limit": 'os.write(1, struct.pack("<I", 0xFFFFFFFF))',
        "zero length": 'os.write(1, struct.pack("<I", 0))',
        "count over message": 'send(b"\\x40l" + struct.pack("<I", 10**6))',
        "invalid utf-8": 'send(b"\\x40s" + struct.pack("<I", 2) + b"\\xc0\\x80")',
        "non-canonical int": 'send(b"\\x40I" + struct.pack("<I", 3) + b"0x5")',
        "leading zero int": 'send(b"\\x40I" + struct.pack("<I", 21) + b"0x0" + b"f" * 18)',
        "deep nesting": 'send(b"\\x40" + b"l\\x01\\x00\\x00\\x00" * 300 + b"N")',
        "unknown function": 'send(b"\\x21i" + struct.pack("<q", 99) + b"t\\x00\\x00\\x00\\x00d\\x00\\x00\\x00\\x00")',
        "parent-only tag": 'send(b"\\x40p" + struct.pack("<Q", 1) + b"s\\x00\\x00\\x00\\x00")',
        "malformed error": 'send(b"\\x41N")',
        "stream ends": 'sys.exit(0)',
        "truncated stream": 'os.write(1, struct.pack("<I", 10) + b"\\x40")',
    }

    def test_violations(self):
        for name, body in self.CASES.items():
            with self.subTest(case=name):
                path = fake_worker(body)
                try:
                    with mock.patch.object(runtime_module, "WORKER", path):
                        rt = Runtime(timeout=10)
                    with self.assertRaises(WorkerError):
                        rt.eval("1")
                    self.assertTrue(rt.closed)
                finally:
                    os.unlink(path)

    def test_silent_worker_times_out(self):
        path = fake_worker("import time\ntime.sleep(60)")
        try:
            with mock.patch.object(runtime_module, "WORKER", path):
                rt = Runtime(timeout=2)
            started = time.monotonic()
            with self.assertRaises(Timeout):
                rt.eval("1")
            self.assertLess(time.monotonic() - started, 10)
        finally:
            os.unlink(path)


class LimitTest(unittest.TestCase):
    def test_timeout(self):
        with Runtime(timeout=0.3) as rt:
            started = time.monotonic()
            with self.assertRaises(Timeout) as cm:
                rt.exec("while True:\n    pass")
            self.assertIsInstance(cm.exception, TimeoutError)
            self.assertLess(time.monotonic() - started, 5)
            self.assertTrue(rt.closed)

    def test_timeout_excludes_host_time(self):
        with Runtime(timeout=0.5) as rt:
            rt.define("slow", lambda: time.sleep(0.3))
            rt.exec("for _ in range(4):\n    slow()")
            self.assertEqual(rt.eval("1"), 1)

    def test_timeout_resets_per_operation(self):
        with Runtime(timeout=0.5) as rt:
            for _ in range(3):
                rt.exec("n = 0\nwhile n < 20000:\n    n += 1")
                time.sleep(0.2)

    def test_memory_limit(self):
        with Runtime(memory_limit=32 << 20) as rt:
            with self.assertRaises(Error) as cm:
                rt.exec("x = 'a' * (64 << 20)")
            self.assertEqual(cm.exception.type, "MemoryError")
            rt.exec("try:\n    chunks = [bytes(1 << 20) for _ in range(100)]\nexcept MemoryError:\n    caught = True")
            self.assertTrue(rt["caught"])
            self.assertEqual(rt.eval("len('b' * (8 << 20))"), 8 << 20)

    def test_message_limit(self):
        with Runtime(message_limit=1 << 16) as rt:
            with self.assertRaises(Error) as cm:
                rt.eval("'x' * (1 << 17)")
            self.assertEqual(cm.exception.type, "OverflowError")
            with self.assertRaises(ValueError):
                rt["big"] = "y" * (1 << 17)
            rt.define("big", lambda: "z" * (1 << 17))
            with self.assertRaises(Error):
                rt.eval("big()")
            self.assertEqual(rt.eval("len('x' * 100)"), 100)

    def test_bad_options(self):
        for options in ({"memory_limit": -1}, {"timeout": 0}, {"message_limit": 0}, {"step_limit": 1.5}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                Runtime(**options)


class ProtocolTest(unittest.TestCase):
    def test_nested_callbacks(self):
        with Runtime() as rt:
            rt.define("down", lambda f, n: f(n - 1) if n else 0)
            rt.exec("def up(n):\n    return down(up, n) + 1")
            self.assertEqual(rt.eval("up(30)"), 31)

    def test_handles_are_released(self):
        with Runtime() as rt:
            for _ in range(2000):
                rt.eval("object()")
            rt.eval("1")
            self.assertLess(len(rt._released), 2)
            live = rt.eval("len(__import__('gc').get_objects())")
            for _ in range(2000):
                rt.eval("object()")
            rt.eval("1")
            self.assertLess(rt.eval("len(__import__('gc').get_objects())") - live, 50)

    def test_engine_subclasses_stay_objects(self):
        with Runtime() as rt:
            value = rt.eval("class D(dict):\n    def __getitem__(self, k): return 1\nD(a=2)")
            self.assertNotIsInstance(value, dict)
            self.assertEqual(value["a"], 1)


class InterruptTest(unittest.TestCase):
    def test_keyboard_interrupt_while_waiting(self):
        rt = Runtime()
        timer = threading.Timer(0.3, lambda: os.kill(os.getpid(), signal.SIGINT))
        timer.start()
        with self.assertRaises(KeyboardInterrupt):
            rt.exec("while True:\n    pass")
        timer.join()
        self.assertTrue(rt.closed)
        with self.assertRaises(WorkerError):
            rt.eval("1")

    def test_worker_dies_with_parent(self):
        code = textwrap.dedent("""
            import sys
            sys.path.insert(0, sys.argv[1])
            from small_python import Runtime
            rt = Runtime()
            print(rt._process.pid, flush=True)
            rt.exec("while True:\\n    pass")
        """)
        source = os.path.dirname(os.path.dirname(runtime_module.__file__))
        parent = subprocess.Popen([sys.executable, "-c", code, source], stdout=subprocess.PIPE, text=True)
        worker = int(parent.stdout.readline())
        parent.kill()
        parent.wait()
        parent.stdout.close()
        for _ in range(100):
            try:
                os.kill(worker, 0)
            except ProcessLookupError:
                return
            time.sleep(0.05)
        os.kill(worker, signal.SIGKILL)
        self.fail("the worker outlived its parent")


if __name__ == "__main__":
    unittest.main()
