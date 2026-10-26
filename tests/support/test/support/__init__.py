"""Test-only adaptation of CPython's test.support; never installed or embedded.

Upstream test modules import it unchanged in place of Lib/test/support, whose
own initialization needs inspect, logging, os, re, sysconfig, and time. The
definitions follow the pinned Lib/test/support/__init__.py (see
docs/licenses/python.txt); platform queries describe Small Python, which is not
CPython, so CPython-only tests are skipped exactly as on other
implementations. Missing helpers fail at import, never silently.
"""

import sys
import unittest


class Error(Exception):
    """Base class for regression test exceptions."""


class TestFailed(Error):
    """Test failed."""
    def __init__(self, msg, *args, stats=None):
        self.msg = msg
        self.stats = stats
        super().__init__(msg, *args)

    def __str__(self):
        return self.msg


class ResourceDenied(unittest.SkipTest):
    """Test skipped because it requested a disallowed resource."""


verbose = 1
use_resources = None
failfast = False
real_max_memuse = 0
max_memuse = 0
SHORT_TIMEOUT = 30.0
LONG_TIMEOUT = 5 * 60.0
LOOPBACK_TIMEOUT = 10.0
INTERNET_TIMEOUT = 60.0

_1M = 1024 * 1024
_1G = 1024 * _1M
_2G = 2 * _1G
_4G = 4 * _1G
MAX_Py_ssize_t = sys.maxsize
NHASHBITS = sys.hash_info.width

MS_WINDOWS = sys.platform == 'win32'
is_jython = False
is_android = False
is_apple_mobile = False
is_apple = sys.platform == 'darwin'
is_emscripten = False
is_wasi = False
is_wasm32 = False
has_fork_support = False
has_subprocess_support = False
has_socket_support = False
Py_DEBUG = False
Py_GIL_DISABLED = False
Py_TRACE_REFS = False
HAVE_DOCSTRINGS = True
MISSING_C_DOCSTRINGS = False
TEST_SUPPORT_DIR = 'Lib/test/support'
TEST_HOME_DIR = 'Lib/test'


def _id(obj):
    return obj


def _parse_guards(guards):
    # Returns a tuple ({platform_name: run_me}, default_value)
    if not guards:
        return ({'cpython': True}, False)
    is_true = list(guards.values())[0]
    assert list(guards.values()) == [is_true] * len(guards)   # all True or all False
    return (guards, not is_true)


def check_impl_detail(**guards):
    guards, default = _parse_guards(guards)
    return guards.get(sys.implementation.name, default)


def impl_detail(msg=None, **guards):
    if check_impl_detail(**guards):
        return _id
    if msg is None:
        guardnames, default = _parse_guards(guards)
        if default:
            msg = "implementation detail not available on {0}"
        else:
            msg = "implementation detail specific to {0}"
        guardnames = sorted(guardnames.keys())
        msg = msg.format(' or '.join(guardnames))
    return unittest.skip(msg)


def cpython_only(test):
    """Decorator for tests only applicable on CPython."""
    return impl_detail(cpython=True)(test)


def refcount_test(test):
    return cpython_only(test)


def no_tracing(func):
    # Small Python has no trace functions.
    return func


def is_resource_enabled(resource):
    return use_resources is None or resource in use_resources


def requires(resource, msg=None):
    if not is_resource_enabled(resource):
        if msg is None:
            msg = "Use of the %r resource not enabled" % resource
        raise ResourceDenied(msg)
    if resource in {"network", "urlfetch"} and not has_socket_support:
        raise ResourceDenied("No socket support")


def requires_resource(resource):
    if is_resource_enabled(resource):
        return _id
    return unittest.skip("resource {0!r} is not enabled".format(resource))


def requires_subprocess():
    return unittest.skipUnless(has_subprocess_support, "requires subprocess support")


def requires_fork():
    return unittest.skipUnless(has_fork_support, "requires working os.fork()")


def requires_working_socket(*, module=False):
    msg = "requires socket support"
    if module:
        if not has_socket_support:
            raise unittest.SkipTest(msg)
    else:
        return unittest.skipUnless(has_socket_support, msg)


requires_IEEE_754 = unittest.skipUnless(
    float.__getformat__("double").startswith("IEEE"),
    "test requires IEEE 754 doubles")

requires_docstrings = unittest.skipUnless(HAVE_DOCSTRINGS, "test requires docstrings")


def skip_emscripten_stack_overflow():
    return unittest.skipIf(is_emscripten, "Exhausts stack on Emscripten")


def skip_wasi_stack_overflow():
    return unittest.skipIf(is_wasi, "Exhausts stack on WASI")


def skip_if_huge_c_stack(depth=150_000):
    # The engine bounds its C recursion by the stack it has used.
    return _id


def skip_if_sanitizer(reason=None, *, address=False, memory=False, ub=False, thread=False):
    return _id


def thread_unsafe(reason):
    if isinstance(reason, str):
        return _id
    return reason


def force_not_colorized(func):
    return func


def force_not_colorized_test_class(cls):
    return cls


def exceeds_recursion_limit():
    """For recursion tests, easily exceeds default recursion limit."""
    return 150_000


def get_attribute(obj, name):
    """Get an attribute, raising SkipTest if AttributeError is raised."""
    try:
        attribute = getattr(obj, name)
    except AttributeError:
        raise unittest.SkipTest("object %r has no attribute %r" % (obj, name))
    else:
        return attribute


def gc_collect():
    import gc
    gc.collect()
    gc.collect()
    gc.collect()


class disable_gc:
    def __enter__(self):
        import gc
        self.enabled = gc.isenabled()
        gc.disable()

    def __exit__(self, *exc):
        import gc
        if self.enabled:
            gc.enable()


def run_code(code, extra_names=None):
    """Run a piece of code after dedenting it, and return its global namespace."""
    import textwrap
    ns = {}
    if extra_names:
        ns.update(extra_names)
    exec(textwrap.dedent(code), ns)
    return ns


def run_no_yield_async_fn(async_fn, /, *args, **kwargs):
    coro = async_fn(*args, **kwargs)
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value
    else:
        raise AssertionError("coroutine did not complete")
    finally:
        coro.close()


def check_syntax_error(testcase, statement, errtext='', *, lineno=None, offset=None):
    with testcase.assertRaisesRegex(SyntaxError, errtext) as cm:
        compile(statement, '<test string>', 'exec')
    err = cm.exception
    testcase.assertIsNotNone(err.lineno)
    if lineno is not None:
        testcase.assertEqual(err.lineno, lineno)
    testcase.assertIsNotNone(err.offset)
    if offset is not None:
        testcase.assertEqual(err.offset, offset)


class _Swap:
    # contextlib.contextmanager versions of swap_attr and swap_item.
    def __init__(self, obj, key, new_val, item):
        self.obj, self.key, self.new_val, self.item = obj, key, new_val, item

    def _has(self):
        return self.key in self.obj if self.item else hasattr(self.obj, self.key)

    def _get(self):
        return self.obj[self.key] if self.item else getattr(self.obj, self.key)

    def _set(self, value):
        if self.item:
            self.obj[self.key] = value
        else:
            setattr(self.obj, self.key, value)

    def __enter__(self):
        self.existed = self._has()
        real_val = self._get() if self.existed else None
        self.real_val = real_val
        self._set(self.new_val)
        return real_val

    def __exit__(self, *exc):
        if self.existed:
            self._set(self.real_val)
        elif self._has():
            if self.item:
                del self.obj[self.key]
            else:
                delattr(self.obj, self.key)


def swap_attr(obj, attr, new_val):
    """Temporary swap out an attribute with a new object."""
    return _Swap(obj, attr, new_val, False)


def swap_item(obj, item, new_val):
    """Temporary swap out an item with a new object."""
    return _Swap(obj, item, new_val, True)


class _CapturedOutput:
    def __init__(self, stream_name):
        self.stream_name = stream_name

    def __enter__(self):
        import io
        self.orig = getattr(sys, self.stream_name)
        setattr(sys, self.stream_name, io.StringIO())
        return getattr(sys, self.stream_name)

    def __exit__(self, *exc):
        setattr(sys, self.stream_name, self.orig)


def captured_output(stream_name):
    return _CapturedOutput(stream_name)


def captured_stdout():
    return captured_output("stdout")


def captured_stderr():
    return captured_output("stderr")


def captured_stdin():
    return captured_output("stdin")


class _AdjustLimit:
    def __init__(self, get, set, value):
        self.get, self.set, self.value = get, set, value

    def __enter__(self):
        self.current = self.get()
        self.set(self.value)

    def __exit__(self, *exc):
        self.set(self.current)


def adjust_int_max_str_digits(max_digits):
    """Temporarily change the integer string conversion length limit."""
    return _AdjustLimit(sys.get_int_max_str_digits, sys.set_int_max_str_digits, max_digits)


def get_recursion_depth():
    """Get the recursion depth of the caller function."""
    # Without frames, find the smallest limit setrecursionlimit() accepts.
    limit = sys.getrecursionlimit()
    low, high = 1, limit
    try:
        while low < high:
            middle = (low + high) // 2
            try:
                sys.setrecursionlimit(middle)
            except RecursionError:
                low = middle + 1
            else:
                high = middle
    finally:
        sys.setrecursionlimit(limit)
    # Exclude this frame and the frame of the caller's caller of interest.
    return low - 2


def set_recursion_limit(limit):
    """Temporarily change the recursion limit."""
    return _AdjustLimit(sys.getrecursionlimit, sys.setrecursionlimit, limit)


def infinite_recursion(max_depth=None):
    if max_depth is None:
        max_depth = 20_000
    elif max_depth < 3:
        raise ValueError(f"max_depth must be at least 3, got {max_depth}")
    depth = get_recursion_depth()
    depth = max(depth - 1, 1)  # Ignore infinite_recursion() frame.
    limit = depth + max_depth
    return set_recursion_limit(limit)


def check_free_after_iterating(test, iter, cls, args=()):
    done = False
    def wrapper():
        class A(cls):
            def __del__(self):
                nonlocal done
                done = True
                try:
                    next(it)
                except StopIteration:
                    pass

        it = iter(A(*args))
        # Issue 26494: Shouldn't crash
        test.assertRaises(StopIteration, next, it)

    wrapper()
    # The sequence should be deallocated just after the end of iterating
    gc_collect()
    test.assertTrue(done)


def check_disallow_instantiation(testcase, tp, *args, **kwds):
    mod = tp.__module__
    name = tp.__name__
    if mod != 'builtins':
        qualname = f"{mod}.{name}"
    else:
        qualname = f"{name}"
    # Upstream searches for the escaped message; a substring test is equal.
    msg = f"cannot create '{qualname}' instances"
    with testcase.assertRaises(TypeError) as cm:
        tp(*args, **kwds)
    testcase.assertIn(msg, str(cm.exception))
    with testcase.assertRaises(TypeError) as cm:
        tp.__new__(tp, *args, **kwds)
    testcase.assertIn(msg, str(cm.exception))


def subTests(arg_names, arg_values, /, *, _do_cleanups=False):
    """Run multiple subtests with different parameters."""
    single_param = False
    if isinstance(arg_names, str):
        arg_names = arg_names.replace(',', ' ').split()
        if len(arg_names) == 1:
            single_param = True
    arg_values = tuple(arg_values)
    def decorator(func):
        if isinstance(func, type):
            raise TypeError('subTests() can only decorate methods, not classes')
        def wrapper(self, /, *args, **kwargs):
            for values in arg_values:
                if single_param:
                    values = (values,)
                subtest_kwargs = dict(zip(arg_names, values))
                with self.subTest(**subtest_kwargs):
                    func(self, *args, **kwargs, **subtest_kwargs)
                if _do_cleanups:
                    self.doCleanups()
        wrapper.__name__ = func.__name__
        wrapper.__qualname__ = func.__qualname__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


class _ALWAYS_EQ:
    """
    Object that is equal to anything.
    """
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False

ALWAYS_EQ = _ALWAYS_EQ()


class _NEVER_EQ:
    """
    Object that is not equal to anything.
    """
    def __eq__(self, other):
        return False
    def __ne__(self, other):
        return True
    def __hash__(self):
        return 1

NEVER_EQ = _NEVER_EQ()


class _LARGEST:
    """
    Object that is greater than anything (except itself).
    """
    # functools.total_ordering, written out.
    def __eq__(self, other):
        return isinstance(other, _LARGEST)
    def __lt__(self, other):
        return False
    def __gt__(self, other):
        return not self.__eq__(other)
    def __le__(self, other):
        return self.__eq__(other)
    def __ge__(self, other):
        return True

LARGEST = _LARGEST()


class _SMALLEST:
    """
    Object that is less than anything (except itself).
    """
    def __eq__(self, other):
        return isinstance(other, _SMALLEST)
    def __gt__(self, other):
        return False
    def __lt__(self, other):
        return not self.__eq__(other)
    def __ge__(self, other):
        return self.__eq__(other)
    def __le__(self, other):
        return True

SMALLEST = _SMALLEST()


class BrokenIter:
    def __init__(self, init_raises=False, next_raises=False, iter_raises=False):
        if init_raises:
            1/0
        self.next_raises = next_raises
        self.iter_raises = iter_raises

    def __next__(self):
        if self.next_raises:
            1/0

    def __iter__(self):
        if self.iter_raises:
            1/0
        return self


def bigmemtest(size, memuse, dry_run=True):
    """Decorator for bigmem tests; without -M they run at a small size."""
    def decorator(f):
        def wrapper(self):
            size = wrapper.size
            memuse = wrapper.memuse
            maxsize = 5147
            if not dry_run and real_max_memuse < maxsize * memuse:
                raise unittest.SkipTest(
                    "not enough memory: %.1fG minimum needed"
                    % (size * memuse / (1024 ** 3)))
            return f(self, maxsize)
        wrapper.size = size
        wrapper.memuse = memuse
        wrapper.__name__ = f.__name__
        wrapper.__qualname__ = f.__qualname__
        return wrapper
    return decorator


def bigaddrspacetest(f):
    def wrapper(self):
        raise unittest.SkipTest("not enough memory: try a 32-bit build instead")
    wrapper.__name__ = f.__name__
    return wrapper


def nomemtest(f):
    # Needs _testcapi.set_nomemory; CPython only.
    return cpython_only(f)


class catch_unraisable_exception:
    """Context manager catching unraisable exception using sys.unraisablehook."""
    def __init__(self):
        self.unraisable = None
        self._old_hook = None

    def _hook(self, unraisable):
        self.unraisable = unraisable

    def __enter__(self):
        self._old_hook = sys.unraisablehook
        sys.unraisablehook = self._hook
        return self

    def __exit__(self, *exc_info):
        sys.unraisablehook = self._old_hook
        del self.unraisable
