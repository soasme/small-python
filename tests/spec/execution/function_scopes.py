# spec: PLS-315 14.9, 16.1, 27.2, 27.4, 27.5
# description: Yields belong to their lexical function, including yields in
# nested definition defaults; async-generator return errors follow binding errors.
from harness import *

for asynchronous in (False, True):
    for own_yield in (False, True):
        for nested_yield in (False, True):
            for default_yield in (False, True):
                for valued_return in (False, True):
                    source = ("async def" if asynchronous else "def") + " f():\n"
                    source += "    def inner(x=" + ("(yield None)" if default_yield else "None") + "):\n"
                    if nested_yield:
                        source += "        yield 1\n"
                    source += "        return 11\n"
                    if own_yield:
                        source += "    if False: yield 2\n"
                    source += "    return" + (" 7" if valued_return else "") + "\n"
                    generator = own_yield or default_yield
                    invalid = asynchronous and generator and valued_return
                    namespace = {}
                    try:
                        exec(compile(source, "<function-scopes>", "exec"), namespace)
                    except SyntaxError as error:
                        assert invalid
                        assert error.msg == "'return' with value in async generator"
                        continue
                    assert not invalid
                    f = namespace["f"]
                    expected = 0x200 if asynchronous and generator else 0x80 if asynchronous else 0x20 if generator else 0
                    assert f.__code__.co_flags & 0x2a0 == expected
                    value = f()
                    if asynchronous and generator:
                        assert type(value).__name__ == "async_generator"
                        try:
                            value.aclose().send(None)
                        except StopIteration:
                            pass
                        else:
                            assert False, "closing an unstarted async generator did not complete"
                    elif asynchronous or generator:
                        assert type(value).__name__ == ("coroutine" if asynchronous else "generator")
                        value.close()
                    else:
                        assert value == (7 if valued_return else None)

# Optimizing away an assertion does not remove its yield from the lexical
# function classification. This also holds for an asynchronous generator.
for optimize in (0, 1, 2):
    for asynchronous in (False, True):
        source = ("async def" if asynchronous else "def") + " f():\n    assert (yield 1)\n"
        namespace = {}
        exec(compile(source, "<optimized-yield>", "exec", optimize=optimize), namespace)
        f = namespace["f"]
        assert f.__code__.co_flags & 0x2a0 == (0x200 if asynchronous else 0x20)
        value = f()
        assert type(value).__name__ == ("async_generator" if asynchronous else "generator")
        if asynchronous:
            try:
                value.aclose().send(None)
            except StopIteration:
                pass
            else:
                assert False, "async generator close did not complete"
        else:
            value.close()

        if asynchronous:
            try:
                compile(source + "    return 7\n", "<optimized-return>", "exec", optimize=optimize)
            except SyntaxError as error:
                assert error.msg == "'return' with value in async generator"
            else:
                assert False, "optimized async generator accepted a valued return"

# Defaults, decorators, class headers and string fields execute in the
# enclosing scope. Nested bodies keep their own yields, even in assertions.
contexts = (
    ("g = lambda: (yield 1)", False),
    ("g = lambda x=(yield 1): None", True),
    ("@(yield 1)\ndef g(): pass", True),
    ("@(yield 1)\nclass C: pass", True),
    ("class C((yield 1)): pass", True),
    ("class C:\n    def g(self): yield 1", False),
    ("f'{(yield 1)}'", True),
    ("t'{(yield 1)}'", True),
    ("assert (lambda: (yield 1))", False),
    ("assert (lambda x=(yield 1): None)", True),
    ("assert f'{(yield 1)}'", True),
    ("assert t'{(yield 1)}'", True),
)
for body, generator in contexts:
    for asynchronous in (False, True):
        for optimize in (0, 1, 2):
            source = ("async def" if asynchronous else "def") + " f():\n"
            source += "    " + body.replace("\n", "\n    ") + "\n"
            namespace = {}
            exec(compile(source, "<yield-context>", "exec", optimize=optimize), namespace)
            f = namespace["f"]
            expected = 0x200 if asynchronous and generator else 0x80 if asynchronous else 0x20 if generator else 0
            assert f.__code__.co_flags & 0x2a0 == expected
            value = f()
            if asynchronous and generator:
                assert type(value).__name__ == "async_generator"
                try:
                    value.aclose().send(None)
                except StopIteration:
                    pass
                else:
                    assert False, "close did not complete"
            elif asynchronous or generator:
                assert type(value).__name__ == ("coroutine" if asynchronous else "generator")
                value.close()
            else:
                assert value is None

# Both branches contain invalid returns. Python 3.15 reports the else suite
# first, even though the handler occurs earlier in source order.
source = """async def f():
    yield 1
    try:
        pass
    except Exception:
        return 1
    else:
        return 2
"""
try:
    compile(source, "<return-order>", "exec")
except SyntaxError as error:
    assert error.msg == "'return' with value in async generator"
    assert error.lineno == 8
else:
    assert False, "valued async-generator return was accepted"

# Binding diagnostics precede the compiler's async-generator return check.
source = """async def f():
    yield 1
    return 2
    nonlocal missing
"""
try:
    compile(source, "<binding-order>", "exec")
except SyntaxError as error:
    assert error.msg == "no binding for nonlocal 'missing' found"
else:
    assert False, "missing nonlocal binding was accepted"
