"""The behaviour of sys and gc that docs/standards/std.md specifies, printed so that
tests/std.py can compare spy with the pinned CPython 3.15 oracle. Values the
specification leaves to the host (sizes, paths, hash algorithm, streams) are
not printed."""
import builtins
import gc
import sys


def show(label, thunk):
    try:
        result = thunk()
    except BaseException as e:
        result = f"{type(e).__name__}: {e}"
    print(f"{label}: {result!r}" if not isinstance(result, str) else f"{label}: {result}")


def calls(module, sources):
    for source in sources:
        show(source, lambda: eval(source, {module.__name__: module}))


# Clause 2: no private names beyond CPython's.
CPYTHON_PRIVATE = {"_base_executable", "_baserepl", "_clear_internal_caches", "_clear_type_cache",
                   "_current_exceptions", "_current_frames", "_debugmallocstats", "_dump_tracelets",
                   "_framework", "_get_cpu_count_config", "_getframe", "_getframemodulename", "_git", "_home",
                   "_is_gil_enabled", "_is_immortal", "_is_interned", "_jit", "_setprofileallthreads",
                   "_settraceallthreads", "_stdlib_dir", "_xoptions"}
show("sys private", lambda: [n for n in dir(sys) if n[:1] == "_" and n[:2] != "__" and n not in CPYTHON_PRIVATE])
show("gc private", lambda: [n for n in dir(gc) if n[:1] == "_" and n[:2] != "__"])

# 5.1
show("modules", lambda: (type(sys.modules).__name__, sys.modules["sys"] is sys, sys.modules["builtins"] is builtins))
show("lazy_modules", lambda: type(sys.lazy_modules).__name__)
show("stdlib_module_names", lambda: (type(sys.stdlib_module_names).__name__, sorted(sys.stdlib_module_names)))
show("pycache_prefix", lambda: sys.pycache_prefix)
show("dont_write_bytecode", lambda: type(sys.dont_write_bytecode).__name__)
show("import state", lambda: [type(getattr(sys, n)).__name__ for n in ("path", "meta_path", "path_hooks", "path_importer_cache")])

# 5.2
calls(sys, ["sys.exception()", "sys.exc_info()", "sys.exception(1)", "sys.exc_info(1)", "sys.exc_info(x=1)"])
try:
    raise KeyError("k")
except KeyError as e:
    show("handled", lambda: (sys.exception() is e, sys.exc_info()[0] is KeyError, sys.exc_info()[1] is e,
                             sys.exc_info()[2] is e.__traceback__))

# 5.3
calls(sys, ["sys.getrecursionlimit()", "sys.setrecursionlimit(0)", "sys.setrecursionlimit(-5)",
            "sys.setrecursionlimit(2**70)", "sys.setrecursionlimit(1.5)", "sys.setrecursionlimit()",
            "sys.get_int_max_str_digits()", "sys.set_int_max_str_digits(100)", "sys.set_int_max_str_digits(-1)",
            "sys.set_int_max_str_digits('x')", "sys.set_int_max_str_digits()",
            "sys.set_int_max_str_digits(maxdigits=5000)", "sys.get_int_max_str_digits()",
            "sys.set_int_max_str_digits(4300)", "sys.getswitchinterval()", "sys.setswitchinterval(0)",
            "sys.setswitchinterval(-1)", "sys.setswitchinterval('x')", "sys.setswitchinterval()",
            "sys.setswitchinterval(interval=1)", "sys.setswitchinterval(0.25)", "sys.getswitchinterval()",
            "sys.setswitchinterval(0.005)", "sys.getswitchinterval(1)"])


def deep(n):
    return deep(n - 1) if n else sys.setrecursionlimit(5)


show("limit too low", lambda: deep(20))

# 5.4
def frames():
    return (sys._getframe().f_code.co_name, sys._getframe(-1).f_code.co_name, sys._getframe(1).f_code.co_name,
            sys._getframemodulename(), sys._getframemodulename(1000))


show("frames", frames)
calls(sys, ["sys._getframe(1000)", "sys._getframe('x')"])

# 5.5
show("streams", lambda: (sys.__stdout__ is sys.stdout, sys.__stderr__ is sys.stderr,
                         callable(sys.stdout.write), callable(sys.stdout.flush)))

# 5.6
show("display None", lambda: sys.displayhook(None))
builtins._ = "unchanged"
show("display 7", lambda: (sys.displayhook(7), builtins._))
calls(sys, ["sys.displayhook()", "sys.displayhook(1, 2)", "sys.displayhook(object=1)"])
show("hook defaults", lambda: [getattr(sys, n) is getattr(sys, f"__{n}__") for n in ("displayhook", "breakpointhook")])

# 5.7
for args in [(), (None,), (0,), (3,), ("bye",)]:
    try:
        sys.exit(*args)
    except SystemExit as e:
        print(f"exit{args}: {e.args!r} {str(e)!r} {e.code!r}")
calls(sys, ["sys.exit(1, 2)", "sys.exit(status=1)", "sys.is_finalizing()", "sys.is_finalizing(1)"])

# 5.9
# The oracle may be a later 3.15 release than the 3.15.0 baseline: micro is not compared.
show("version_info", lambda: (type(sys.version_info).__name__, sys.version_info[:2], sys.version_info >= (3, 15),
                              sys.version_info.major, sys.version_info.releaselevel, sys.version_info.serial))
show("version", lambda: (hex(sys.hexversion & ~0xFF00), sys.api_version, sys.version.startswith("3.15.")))
show("implementation", lambda: [hasattr(sys.implementation, n) for n in ("name", "cache_tag", "version", "hexversion")])
show("numbers", lambda: (sys.maxsize == 2**63 - 1, sys.maxunicode, sys.float_repr_style, sys.float_info))
show("int_info", lambda: (sys.int_info._fields if hasattr(sys.int_info, "_fields") else None,
                          sys.int_info.default_max_str_digits, sys.int_info.str_digits_check_threshold))
show("hash_info", lambda: tuple(sys.hash_info)[:5])
show("abi", lambda: (sys.abiflags, sys.abi_info.pointer_bits, sys.abi_info.free_threaded, sys.abi_info.debug,
                     sys.abi_info.byteorder == sys.byteorder))
show("flags", lambda: (sys.flags.n_fields, sys.flags.n_sequence_fields, sys.flags.optimize,
                       [n for n in dir(sys.flags) if not n.startswith("_") and n not in
                        ("count", "index", "n_fields", "n_sequence_fields", "n_unnamed_fields")]))
for name in ("version_info", "flags", "float_info", "int_info", "hash_info"):
    structseq = type(getattr(sys, name))
    show(f"{name} type", lambda: (structseq.n_fields, structseq.n_sequence_fields, structseq.n_unnamed_fields))
    show(f"{name}((1,))", lambda: structseq((1,)))
    show(f"{name}(itself)", lambda: structseq(tuple(getattr(sys, name))) == getattr(sys, name))

# 5.10
show("intern", lambda: sys.intern("".join(["a", "b"])) is sys.intern("ab"))
calls(sys, ["sys.intern(1)", "sys.intern()", "sys.intern(string='a')", "sys.getdefaultencoding()",
            "sys.getdefaultencoding(1)", "sys.getfilesystemencoding()", "sys.getfilesystemencodeerrors()",
            "type(sys.getunicodeinternedsize())", "sys.getunicodeinternedsize(1)"])
show("intern subclass", lambda: sys.intern(type("S", (str,), {})("a")))


# 5.11
class Size:
    def __init__(self, result):
        self.result = result

    def __sizeof__(self):
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


calls(sys, ["sys.getsizeof()", "sys.getsizeof(x=1)", "sys.getsizeof(1, 2, 3)", "type(sys.getrefcount(sys))",
            "sys.getrefcount()", "type(sys.getallocatedblocks())", "sys.getallocatedblocks(1)"])
show("getsizeof", lambda: (type(sys.getsizeof(0)), sys.getsizeof([]) - [].__sizeof__() > 0,
                           sys.getsizeof(1) == (1).__sizeof__()))
for result in (TypeError("t"), ValueError("v"), -1, "x", 2**70):
    show(f"getsizeof {result!r}", lambda: sys.getsizeof(Size(result)))
    show(f"getsizeof {result!r}, 7", lambda: sys.getsizeof(Size(result), 7))

# 6
calls(gc, ["gc.isenabled()", "gc.disable()", "gc.isenabled()", "gc.enable()", "gc.isenabled()", "gc.enable(1)",
           "gc.isenabled(1)", "gc.disable(1)", "gc.get_threshold()", "gc.get_threshold(1)", "gc.set_threshold()",
           "gc.set_threshold(1, 2, 3, 4)", "gc.set_threshold(x=1)", "gc.set_threshold(1.5)",
           "gc.set_threshold(2**80)", "gc.set_threshold(500)", "gc.get_threshold()",
           "gc.set_threshold(2000, 10, 10)", "type(gc.get_count())", "len(gc.get_count())", "gc.get_count(1)",
           "type(gc.collect())", "gc.collect(3)", "gc.collect(-1)", "gc.collect('x')", "gc.collect(1, 2)",
           "type(gc.collect(generation=1))", "[sorted(s) for s in gc.get_stats()]", "gc.get_stats(1)",
           "gc.get_debug()", "gc.set_debug('x')", "gc.set_debug()", "gc.set_debug(flags=1)", "gc.get_debug(1)",
           "(gc.DEBUG_STATS, gc.DEBUG_COLLECTABLE, gc.DEBUG_UNCOLLECTABLE, gc.DEBUG_SAVEALL, gc.DEBUG_LEAK)",
           "gc.garbage", "gc.callbacks", "gc.get_objects(3)", "gc.get_objects(2.0)", "gc.get_objects(1, 2)",
           "type(gc.get_objects(-1))", "type(gc.get_objects(generation=0))", "gc.is_tracked()",
           "gc.is_tracked(1, 2)", "gc.is_tracked(obj=1)", "gc.is_finalized()", "gc.is_finalized(obj=1)",
           "gc.get_referents([1, 'a'])", "gc.get_referents(1)", "type(gc.get_referrers(gc))",
           "gc.freeze()", "gc.unfreeze()", "type(gc.get_freeze_count())", "gc.freeze(1)",
           "gc.get_freeze_count(1)"])


class Node:
    def __init__(self):
        self.me = self


show("tracked", lambda: [gc.is_tracked(x) for x in (None, 1, 1.0, "s", b"", (), (1,), ([],), frozenset(),
                                                    frozenset({()}), [], {}, Node(), Node, type, len, ValueError,
                                                    lambda: 0)])

seen = []
gc.callbacks.append(lambda phase, info: seen.append((phase, sorted(info), info["generation"],
                                                     type(info["duration"]).__name__)))
gc.collect()
gc.callbacks.clear()
show("callbacks", lambda: seen[:2])
show("stats", lambda: [sorted(s) == ["candidates", "collected", "collections", "duration", "uncollectable"]
                       for s in gc.get_stats()])

gc.set_debug(gc.DEBUG_SAVEALL)
node = Node()
del node
gc.collect()
show("saveall", lambda: any(type(x) is Node for x in gc.garbage))
gc.set_debug(0)
gc.garbage.clear()

revived = []


class Phoenix:
    def __init__(self):
        self.me = self

    def __del__(self):
        revived.append(self)


phoenix = Phoenix()
show("finalized before", lambda: gc.is_finalized(phoenix))
del phoenix
gc.collect()
show("finalized after", lambda: (len(revived), gc.is_finalized(revived[0]), gc.is_finalized(Node())))

ended = []


class Mortal:
    def __init__(self):
        self.me = self

    def __del__(self):
        ended.append(1)


gc.collect()
before = gc.get_count()[0]
cells = [[] for _ in range(50)]
show("count grows", lambda: gc.get_count()[0] >= before + 50)
mortal = Mortal()
gc.freeze()
show("frozen", lambda: (gc.get_freeze_count() > 0, any(x is mortal for x in gc.get_objects())))
del mortal
gc.collect()
show("frozen survives", lambda: ended)
gc.unfreeze()
gc.collect()
show("unfrozen", lambda: (ended, gc.get_freeze_count()))


class Errors:
    def __init__(self):
        self.text = []

    def write(self, text):
        self.text.append(text)
        return len(text)


sys.stderr = Errors()
node = Node()
del node
gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_COLLECTABLE)
gc.collect()
gc.set_debug(0)
errors, sys.stderr = sys.stderr, sys.__stderr__
lines = "".join(errors.text).splitlines()
show("debug stats", lambda: (lines[0], lines[1].split(":")[0], lines[2].split(":")[0], lines[-1].split(",")[0]))
show("debug collectable", lambda: any(line.startswith("gc: collectable <Node 0x") for line in lines))

# 5.1.3, 5.1.4
calls(sys, ["sys.get_lazy_imports()", "sys.get_lazy_imports(1)", "sys.set_lazy_imports('x')",
            "sys.set_lazy_imports(1)", "sys.set_lazy_imports()", "sys.set_lazy_imports('all', 1)",
            "sys.get_lazy_imports_filter()", "sys.get_lazy_imports_filter(1)", "sys.set_lazy_imports_filter(1)",
            "sys.set_lazy_imports_filter()", "sys.set_lazy_imports_filter(filter=None)"])
filtered = []
sys.set_lazy_imports_filter(lambda *args: filtered.append(args) or args[1] != "_probe_eager")
sys.set_lazy_imports("all")
import _probe_lazy
from _probe_lazy import name
try:
    import _probe_eager
except ImportError:
    pass


def imports_in_function():
    try:
        import _probe_inner
    except ImportError:
        return "eager"


show("lazy mode", lambda: (sys.get_lazy_imports(), type(globals()["_probe_lazy"]).__name__,
                           type(globals()["name"]).__name__, filtered, imports_in_function()))
sys.set_lazy_imports("normal")
sys.set_lazy_imports_filter(None)
del _probe_lazy, name

# 5.8
calls(sys, ["sys.get_asyncgen_hooks()", "sys.get_asyncgen_hooks(1)", "sys.set_asyncgen_hooks(1)",
            "sys.set_asyncgen_hooks(None, 1)", "sys.set_asyncgen_hooks(1, 2, 3)", "sys.set_asyncgen_hooks(x=1)",
            "type(sys.get_asyncgen_hooks())((1,))", "type(sys.get_asyncgen_hooks())((1, 2))",
            "sys.get_coroutine_origin_tracking_depth()", "sys.get_coroutine_origin_tracking_depth(1)",
            "sys.set_coroutine_origin_tracking_depth(-1)", "sys.set_coroutine_origin_tracking_depth(1.5)",
            "sys.set_coroutine_origin_tracking_depth(2**70)", "sys.set_coroutine_origin_tracking_depth()"])
hooked = []


async def agen():
    yield 1


sys.set_asyncgen_hooks(firstiter=lambda g: hooked.append(("firstiter", g.__name__)),
                       finalizer=lambda g: hooked.append(("finalizer", g.__name__)))
running = agen()
step = running.__anext__()
try:
    step.send(None)
except StopIteration:
    pass
del running, step
gc.collect()
show("asyncgen hooks", lambda: hooked)
sys.set_asyncgen_hooks(None, None)


async def coroutine():
    pass


def make_coroutine():
    return coroutine()


sys.set_coroutine_origin_tracking_depth(depth=2)
made = make_coroutine()
show("cr_origin", lambda: [(line, name) for _, line, name in made.cr_origin])
made.close()
sys.set_coroutine_origin_tracking_depth(0)
made = make_coroutine()
show("cr_origin off", lambda: (made.cr_origin, sys.get_coroutine_origin_tracking_depth()))
made.close()

# 5.9.3, 5.12
show("thread_info", lambda: (type(sys.thread_info).n_fields, type(sys.thread_info)((1, 2, 3))))
calls(sys, ["sys.call_tracing(len, ([1],))", "sys.call_tracing(len, [1])", "sys.call_tracing(len)",
            "sys.call_tracing(f=len, args=())", "type(sys.is_remote_debug_enabled())",
            "sys.is_remote_debug_enabled(1)"])

# 5.6.2, 5.6.3
calls(sys, ["sys.excepthook()", "sys.excepthook(1, 2)", "sys.excepthook(1, 2, 3, 4)", "sys.unraisablehook()",
            "sys.unraisablehook(1)", "sys.__excepthook__ is sys.excepthook",
            "sys.__unraisablehook__ is sys.unraisablehook"])


def captured(thunk):
    sys.stderr = Errors()
    try:
        thunk()
    finally:
        errors, sys.stderr = sys.stderr, sys.__stderr__
    return "".join(errors.text)


class Unprintable(Exception):
    def __str__(self):
        raise RuntimeError


def chained():
    try:
        raise KeyError("k")
    except KeyError as error:
        outer = ValueError("v")
        outer.__context__, outer.__cause__ = error, TypeError("t")
        return outer


noted = ValueError("noted")
noted.add_note("first\nsecond")
for case in (None, "text", ValueError(), Unprintable(), noted, chained(),
             SyntaxError("bad", ("f.py", 2, 5, "  x = = 1\n", 2, 7)), SyntaxError("bare"),
             ExceptionGroup("eg", [ValueError(1), ExceptionGroup("inner", [TypeError(2)])]),
             ExceptionGroup("wide", [ValueError(i) for i in range(17)])):
    show(f"excepthook {type(case).__name__}",
         lambda: captured(lambda: sys.excepthook(type(case), case, None)).splitlines())

unraisable = []
sys.unraisablehook = lambda args: unraisable.append(
    (type(args).__name__, args.exc_type.__name__, str(args.exc_value), args.exc_traceback is not None,
     args.err_msg.split("<")[0], args.object))


class Failing:
    def __del__(self):
        raise ValueError("in __del__")


def closing():
    try:
        yield 1
    finally:
        raise KeyError("in close")


failing = Failing()
del failing
suspended = closing()
next(suspended)
del suspended
gc.collect()
show("unraisable", lambda: unraisable)


def drop_failing():
    Failing()
    gc.collect()


sys.unraisablehook = lambda args: 1 / 0
show("failing unraisablehook", lambda: captured(drop_failing).splitlines()[0].split("<")[0])
sys.unraisablehook = sys.__unraisablehook__
show("default unraisablehook", lambda: captured(drop_failing).splitlines()[0].split("<")[0])

# 5.12
calls(sys, ["sys.settrace()", "sys.settrace(f=1)", "sys.gettrace()", "sys.setprofile()", "sys.getprofile()"])
traced = []


def tracer(frame, event, arg):
    traced.append((frame.f_code.co_name, event, frame.f_lineno - frame.f_code.co_firstlineno,
                   arg[0].__name__ if event == "exception" else arg))
    return tracer


def traced_loop(x):
    y = x
    for i in range(2):
        y += i
    return y


def traced_generator():
    yield 1
    yield 2
    i = 0
    while i < 3:
        i += 1
        if i == 2:
            continue
        yield i
    for j in range(2):
        yield j


def traced_raise():
    try:
        raise ValueError("v")
    except ValueError:
        pass
    raise KeyError("k")


sys.settrace(tracer)
traced_loop(1)
list(traced_generator())
try:
    traced_raise()
except KeyError:
    pass
sys.settrace(None)
show("settrace", lambda: traced)
profiled = []
sys.setprofile(lambda frame, event, arg: profiled.append((frame.f_code.co_name, event, arg)))
traced_loop(2)
sys.setprofile(None)
show("setprofile", lambda: [entry for entry in profiled if not entry[1].startswith("c_")])


def failing_tracer(frame, event, arg):
    if event == "line":
        raise RuntimeError("tracer")
    return failing_tracer


sys.settrace(failing_tracer)
try:
    traced_loop(3)
except RuntimeError as error:
    show("failing tracer", lambda: (str(error), sys.gettrace()))
