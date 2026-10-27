# spec: PLS-315 9.8, 17.2, B.1.3
# description: The main module is __main__, entered in the module cache with its standard attributes.
from harness import *

assert_eq(__name__, "__main__")
main = host.module_cache()["__main__"]
assert_is(main.__dict__, globals())
assert_true(__file__.endswith("test_spec.py"))
assert_is(__spec__, None) if __spec__ is None else assert_eq(__spec__.name, "__main__")
assert_true("__builtins__" in globals())
assert_eq(__doc__, None)
assert_eq(__package__, None) if __package__ is None else assert_eq(__package__, "")
# builtins is in the module cache before the main module runs.
assert_true("builtins" in host.module_cache())
builtins_module = host.module_cache()["builtins"]
assert_is(builtins_module.len, len)
assert_eq(builtins_module.__name__, "builtins")
