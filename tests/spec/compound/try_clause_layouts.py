# spec: PLS-315 15.4, 15.4.1
# description: A try statement's clauses run in their order of evaluation
# whatever the layout between them: comments and blank lines, clauses on
# their header's line, continued and bracketed clause headers, a lambda in
# an except expression, nested try statements in the else and handler
# blocks; an else block runs after the body only when it raised nothing,
# for except and except*, in function, class and module bodies.
from harness import *

out = []


def f(x):
    try:   # a comment after the colon
        if x == 1: raise ValueError
        out.append("body")

    # blank and comment lines between clauses

    except (ValueError,
            TypeError) as e:
        out.append("value")
    except \
        KeyError:
        out.append("key")
    except (lambda: ZeroDivisionError)():
        out.append("lambda")
    else:
        try: out.append("inner")
        finally: out.append("inner finally")
    finally:
        out.append("finally")
    try: x / 0
    except ZeroDivisionError: out.append("divided")
    try:
        try:
            raise KeyError
        except KeyError:
            try:
                pass
            except: pass
            else: out.append("nested else")
    except: out.append("never")
    else: out.append("outer else")
    return out


assert_same(f(0), ["body", "inner", "inner finally", "finally", "divided", "nested else", "outer else"])
del out[:]
assert_same(f(1), ["value", "finally", "divided", "nested else", "outer else"])
del out[:]


def group():
    try:
        raise ExceptionGroup("g", [ValueError(1), TypeError(2)])
    except* ValueError:
        out.append("value")
    except* TypeError:
        out.append("type")
    else:
        out.append("never")
    finally:
        out.append("finally")
    try:
        pass
    except* ValueError:
        out.append("never")
    else:
        out.append("else")
    return out


assert_same(group(), ["value", "type", "finally", "else"])


class C:
    try:
        x = 1
    except NameError as e:
        y = 2
    else:
        z = 3


assert_same((C.x, C.z, hasattr(C, "e"), hasattr(C, "y")), (1, 3, False, False))
try:
    a = 1
except:
    a = 2
else:
    a = 3
assert_same(a, 3)
