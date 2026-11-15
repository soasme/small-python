# spec: PLS-315 16.6.1, 14.2
# description: a module body executed with a mapping whose __setitem__ is
# Python, which may loop, binds __annotate__, then
# __conditional_annotations__, through it before its first statement,
# then each annotated assignment's name in order; an error from the
# mapping stops the body there. Executed from functions as at module
# level.
from harness import *

log = []

class Namespace(dict):
    def __setitem__(self, key, value):
        for _ in (): pass
        log.append(key)
        super().__setitem__(key, value)

class Refusing(dict):
    def __setitem__(self, key, value):
        for _ in (): pass
        log.append(key)
        if key == "__conditional_annotations__": raise KeyError(key)
        super().__setitem__(key, value)

def run(source, namespace):
    log.clear()
    exec(source, {}, namespace)
    return log[:], sorted(namespace)

assert_eq(run("x: int = 2", Namespace()),
          (["__annotate__", "__conditional_annotations__", "x"], ["__annotate__", "__conditional_annotations__", "x"]))
assert_eq(run("a = 1\nx: int = 2\nif a:\n    y: str = 3\nb = 3\n", Namespace())[0],
          ["__annotate__", "__conditional_annotations__", "a", "x", "y", "b"])
ns = Namespace()
assert_eq(run("if 1:\n    z: int\n", ns)[0], ["__annotate__", "__conditional_annotations__"])
assert_eq(ns["__conditional_annotations__"], {0})
assert_eq(run("a = 1\ndel a\nw: int = 4", Namespace())[0], ["__annotate__", "__conditional_annotations__", "a", "w"])

def refused():
    log.clear()
    try: exec("q: int = 1\nr = 2", {}, Refusing())
    except KeyError as e: return e.args, log

assert_eq(refused(), (("__conditional_annotations__",), ["__annotate__", "__conditional_annotations__"]))
log.clear()
exec("v: int = 5", {}, Namespace())
assert_eq(log, ["__annotate__", "__conditional_annotations__", "v"])
