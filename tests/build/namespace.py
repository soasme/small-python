# build: -I lib
# bundles: namespace.py plugins/a.py lib/plugins/b.py
# description: a namespace package (PEP 420) gathers portions from every search root; it has no file.
import plugins.a
import plugins.b
assert plugins.a.NAME == "a" and plugins.b.NAME == "b"
assert plugins.__file__ is None
assert plugins.b.__package__ == "plugins"
