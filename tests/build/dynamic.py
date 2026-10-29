# build: -D plugins.*
# bundles: dynamic.py plugins/__init__.py plugins/csv.py plugins/json.py plugins/sub/__init__.py plugins/sub/deep.py literal.py
# description: -D PKG.* includes every module under a package for computed imports; a literal __import__ is followed without it.
import plugins
formats = [__import__("plugins." + name, fromlist=["FORMAT"]).FORMAT for name in plugins.NAMES]
assert formats == ["csv", "json"]
deep = __import__(".".join(["plugins", "sub", "deep"]), fromlist=["*"])
assert deep.DEPTH == 2
assert __import__("literal").VALUE == "literal"
