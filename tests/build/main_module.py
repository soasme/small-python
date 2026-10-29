# build: -m app.tool
# bundles: app/__init__.py app/tool.py app/util.py
# description: -m runs a module as __main__ with its package set, so its relative imports work; importing it by name runs it again as a module.
from . import util
from .util import helper
import app
MARK = __name__
if __name__ == "__main__":
    assert __package__ == "app" and app.ROLE == "package" and helper() == "util"
    import app.tool as again
    assert again.MARK == "app.tool" and again.util is util
