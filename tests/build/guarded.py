# build:
# bundles: guarded.py
# description: a missing module imported inside a try that catches ImportError, ModuleNotFoundError, Exception, or BaseException, or a bare except, is left out and raises at run time.
try:
    import nosuch_a
except ImportError:
    nosuch_a = None
try:
    import nosuch_b.sub
except ModuleNotFoundError:
    nosuch_b = None
try:
    from nosuch_c import name
except (ValueError, ImportError):
    name = None
try:
    import nosuch_d
except:
    nosuch_d = None
try:
    import nosuch_e
except Exception as error:
    assert type(error) is ModuleNotFoundError and error.name == "nosuch_e"
else:
    raise AssertionError("nosuch_e was found")


def later():
    try:
        import nosuch_f
    except BaseException:
        return "fallback"


assert (nosuch_a, nosuch_b, name, nosuch_d) == (None, None, None, None)
assert later() == "fallback"
