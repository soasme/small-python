# Replays ConcreteExceptions.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
def unicode_error(kind, start, end):
    if kind == "decode":
        e = UnicodeDecodeError("utf-8", b"\x80\xffA", start, end, "r")
    elif kind == "encode":
        e = UnicodeEncodeError("ascii", "\xe9α\U0001f600A", start, end, "r")
    else:
        e = UnicodeTranslateError("\xe9α\U0001f600A", start, end, "r")
    return ascii(str(e))
class Obj:
    pass

SOURCES = {
    "attributeerror_attrs": 'try:\n    Obj().missing\nexcept AttributeError as e:\n    result = (e.name, type(e.obj).__name__, str(e))',
    "attributeerror_kw": "e = AttributeError('m', name='n', obj=1)\nresult = (e.name, e.obj, e.args)",
    "attributeerror_bad_kw": 'result = AttributeError(x=1)',
    "nameerror_name": 'try:\n    undefined_name\nexcept NameError as e:\n    result = (e.name, str(e))',
    "nameerror_suggestion_attr": "result = NameError('m', name='q').name",
    "unboundlocal": 'def f():\n    print(v)\n    v = 1\ntry:\n    f()\nexcept UnboundLocalError as e:\n    result = (type(e).__mro__[1].__name__, e.name, str(e))',
    "importerror_attrs": "e = ImportError('msg', name='n', path='p')\nresult = (e.name, e.path, e.msg, str(e), e.name_from)",
    "importerror_bad_kw": 'result = ImportError(x=1)',
    "importerror_from": 'try:\n    from builtins import nosuchname\nexcept ImportError as e:\n    result = (e.name, e.name_from, type(e).__name__)',
    "modulenotfound": 'try:\n    import nosuchmod_q\nexcept ModuleNotFoundError as e:\n    result = (e.name, e.path, str(e))',
    "indexerror": 'try:\n    [][0]\nexcept IndexError as e:\n    result = str(e)',
    "keyerror_missing": 'try:\n    {}[()]\nexcept KeyError as e:\n    result = (e.args, str(e))',
    "oserror_args": "e = OSError(2, 'No such file', 'f.txt')\nresult = (type(e).__name__, e.errno, e.strerror, e.filename, str(e))",
    "oserror_two_files": "e = OSError(1, 'x', 'a', None, 'b')\nresult = (e.filename, e.filename2, str(e))",
    "oserror_single_arg": "e = OSError('just')\nresult = (e.errno, e.strerror, e.args, str(e))",
    "stopiteration_in_gen": 'def g():\n    raise StopIteration\n    yield\ntry:\n    next(g())\nexcept RuntimeError as e:\n    result = (str(e), type(e.__cause__).__name__)',
    "stopasync_in_agen": 'async def g():\n    raise StopAsyncIteration\n    yield\nc = g().__anext__()\ntry:\n    c.send(None)\nexcept RuntimeError as e:\n    result = str(e)',
    "syntaxerror_attrs": "try:\n    compile('a +', 'f.py', 'exec')\nexcept SyntaxError as e:\n    result = (e.filename, e.lineno, e.text, e.msg)",
    "syntaxerror_build": "e = SyntaxError('m', ('f', 1, 2, 'txt', 1, 3))\nresult = (e.msg, e.filename, e.lineno, e.offset, e.text, e.end_lineno, e.end_offset, str(e))",
    "syntaxerror_str_no_file": "result = str(SyntaxError('m', (None, 1, 2, 't')))",
    "indentation_tab": 'result = (issubclass(TabError, IndentationError), issubclass(IndentationError, SyntaxError))',
    "unicode_decode": "try:\n    b'\\xff'.decode('utf-8')\nexcept UnicodeDecodeError as e:\n    result = (e.encoding, e.object, e.start, e.end, e.reason, str(e))",
    "unicode_encode": "try:\n    '\\xe9'.encode('ascii')\nexcept UnicodeEncodeError as e:\n    result = (e.encoding, e.object, e.start, e.end, e.reason, str(e))",
    "unicode_build_bad": "result = UnicodeDecodeError('utf-8', 'notbytes', 0, 1, 'r')",
    "unicode_translate": "e = UnicodeTranslateError('\\xe9', 0, 1, 'bad')\nresult = (e.encoding, str(e))",
    "zero_division": 'try:\n    1 % 0\nexcept ZeroDivisionError as e:\n    result = str(e)',
    "overflow_float": 'try:\n    2.0 ** 10000\nexcept OverflowError as e:\n    result = e.args',
    "recursion": "def r(): return r()\ntry:\n    r()\nexcept RecursionError as e:\n    result = 'maximum recursion depth exceeded' in str(e)",
    "notimplemented_error": 'result = issubclass(NotImplementedError, RuntimeError) and NotImplementedError is not NotImplemented',
    "assertion_msg": "try:\n    assert 1 == 2, ('m', 1)\nexcept AssertionError as e:\n    result = e.args",
    "systemexit_attrs": "e = SystemExit('bye')\nresult = (e.code, str(e))",
    "generator_exit_close": 'def g():\n    try:\n        yield\n    except GeneratorExit as e:\n        log.append(type(e).__name__)\n        raise\nlog = []\nx = g()\nnext(x)\nx.close()\nresult = log',
    "eoferror_type": 'result = issubclass(EOFError, Exception)',
    "memoryerror_type": 'result = (issubclass(MemoryError, Exception), MemoryError().args)',
    "typeerror_args": "result = TypeError('a', 'b').args",
    "buffererror": "b = bytearray(b'a')\nm = memoryview(b)\ntry:\n    b.append(1)\nexcept BufferError as e:\n    result = str(e)",
    "finalization_error": 'result = issubclass(PythonFinalizationError, RuntimeError)',
    "import_cycle_error": 'result = issubclass(ImportCycleError, ImportError)'
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return unicode_error(p["kind"], p["start"], p["end"])


def run(p):
    if "case" not in p:
        return generated(p)
    namespace = dict(TYPES)
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
        return repr(namespace.get("result"))
    except SyntaxError as error:
        return "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


def outcome(p):
    # TLA+ strings are ASCII.
    return run(p).encode("ascii", "backslashreplace").decode()


check_programs(outcome)
