# spec: PLS-315 16.4.2, 17.5
# description: A class definition reads a base's __mro_entries__ and the
# metaclass's __prepare__ by GetAttribute, so a module base or metaclass
# whose attribute is a lazy import object reifies it, then calls the
# reified function: the base is replaced by its entries, and __prepare__
# runs before the module, which is not callable, is called as the
# metaclass. A lazy import of a loaded module binds at once; one made
# before its module is loaded reifies from the loaded module.
from harness import *
import builtins

def holder(name):
    h = type(builtins)("h")
    exec("lazy from spec_clr_value import " + name, h.__dict__)
    return h

def classes():
    host.module_cache().pop("spec_clr_value", None)
    base, meta = holder("entries as __mro_entries__"), holder("prepare as __prepare__")
    assert_eq(type(base.__dict__["__mro_entries__"]).__name__, "lazy_import")
    class C(base):
        pass
    assert_eq(C.__bases__, (object,))
    assert_eq(C.__orig_bases__, (base,))
    assert_eq(type(base.__dict__["__mro_entries__"]).__name__, "function")
    # The module is loaded now: meta's read reifies without loading it.
    try:
        class D(metaclass=meta):
            x = 1
    except TypeError as e:
        message = str(e)
    assert_eq(message, "'module' object is not callable")
    assert_eq(type(meta.__dict__["__prepare__"]).__name__, "function")
    loaded = holder("entries")
    assert_eq(type(loaded.__dict__["entries"]).__name__, "function")

classes()
# Again, the module loaded before the placeholders: each read completes at once.
def again():
    host.module_cache().pop("spec_clr_value", None)
    base, meta = holder("entries as __mro_entries__"), holder("prepare as __prepare__")
    import spec_clr_value
    class C(base):
        pass
    assert_eq(C.__bases__, (object,))
    try:
        class D(metaclass=meta):
            pass
    except TypeError as e:
        assert_eq(str(e), "'module' object is not callable")
    else:
        raise AssertionError("no TypeError")
again()
