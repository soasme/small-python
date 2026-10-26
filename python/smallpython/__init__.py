"""Python binding for Small Python, an embeddable Python engine.

    import smallpython

    rt = smallpython.Runtime()

    @rt.function
    def greet(name):
        return f"hello {name}"

    rt.eval("greet('spy')")  # 'hello spy'
"""
from ._core import SPY_VERSION, Error, Object, Runtime as _Runtime

__all__ = ["Error", "Object", "Runtime", "SPY_VERSION"]
__version__ = SPY_VERSION


def _error_property(index):
    return property(lambda self: self.args[index] if len(self.args) > index else None)


Error.type = _error_property(0)
Error.message = _error_property(1)
Error.exception = _error_property(2)
Error.__str__ = lambda self: f"{self.type}: {self.message}" if self.message else str(self.type)


class Runtime(_Runtime):
    """An independent Small Python engine context.

    Keyword arguments: ``std`` registers the standard modules (sys, gc,
    weakref, ...); ``step_limit`` bounds evaluation steps (0 is unlimited);
    ``output`` receives printed text (default ``sys.stdout.write``);
    ``loader`` maps a module name to its source, or None when not found.
    """

    def function(self, func=None, *, name=None):
        """Decorator binding a Python callable as a global host function."""
        def bind(func):
            self.define(name or func.__name__, func)
            return func
        return bind(func) if func is not None else bind

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
