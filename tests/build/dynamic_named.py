# build: -D handlers.save
# bundles: dynamic_named.py handlers/__init__.py handlers/save.py
# description: -D MODULE includes one module, with its parent package, for a computed import; its siblings stay out.
name = "save"
handler = __import__("handlers." + name, fromlist=["run"])
assert handler.run() == "saved"
