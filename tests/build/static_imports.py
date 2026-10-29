# build:
# bundles: static_imports.py log.py alpha.py beta/__init__.py beta/gamma.py
# description: import, import as, and from-import of modules, submodules, and attributes; each module runs once, parents first, with its name, package, and file.
import log
import alpha
import beta.gamma
import beta.gamma as g
from beta import gamma, value
from alpha import twice
assert g is beta.gamma is gamma
assert value == "beta" and twice(4) == 8
assert alpha.__name__ == "alpha" and beta.gamma.__name__ == "beta.gamma"
assert alpha.__package__ == "" and beta.__package__ == "beta" and beta.gamma.__package__ == "beta"
assert alpha.__file__.endswith("alpha.py")
assert beta.__file__.replace("\\", "/").endswith("beta/__init__.py")
assert beta.gamma.__file__.replace("\\", "/").endswith("beta/gamma.py")
assert hasattr(beta, "__path__") and not hasattr(alpha, "__path__")
assert log.events == ["alpha", "beta", "beta.gamma"], log.events
assert __name__ == "__main__" and __file__.endswith("static_imports.py")
