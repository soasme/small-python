# build:
# bundles: dynamic_fromlist.py kit/__init__.py kit/save.py
# description: the string names of a literal __import__'s positional fromlist are bundled when they are modules.
kit = __import__("kit", None, None, ("save", "missing"))
assert kit.save.VALUE == "save"
