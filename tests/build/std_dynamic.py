# build: -D sys
# bundles: std_dynamic.py
# description: -D names a standard module that only a dynamic import reaches, which registers it.
name = "s" + "ys"
module = __import__(name)
assert module.modules[name] is module
