# Replays LazyImports.tla: each case clears the fixture modules (the
# Imports.files of LazyImports.files) from the module cache and the lazy-module registry,
# runs the spec's statements, and compares the result and the modules' run
# log with the model's.
from harness import host

FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

FIXTURES = ("pkg", "nspkg", "plain", "cycle_a", "cycle_b", "tracelog", "nosuchmod")
PLACEHOLDER = "result = type(globals()['%s']).__name__"
SOURCES = {
    "unused": "lazy import pkg.sub\nresult = 'unused'",
    "used": "lazy import pkg.sub\nresult = pkg.sub.x",
    "from_unused": "lazy from pkg import sub\nresult = 'unused'",
    "from_used": "lazy from pkg import sub\nresult = sub.x",
    "placeholder": "lazy import pkg\n" + PLACEHOLDER % "pkg",
    "from_placeholder": "lazy from pkg import sub\n" + PLACEHOLDER % "sub",
    "missing_unused": "lazy import nosuchmod\nresult = 'unused'",
    "missing_used": "lazy import nosuchmod\nnosuchmod",
    "broken": "lazy import pkg.broken\nimport tracelog\np = pkg\nbefore = list(tracelog.events)\ntry:\n"
              "    p.broken\nexcept ValueError:\n    result = before",
    "as": "lazy import pkg.sub as s\nresult = s.x",
    "not_cached": "lazy import pkg\nfrom harness import host\nresult = 'pkg' in host.module_cache()",
    "in_function_use": "lazy import pkg\ndef f(): return pkg.pub\nresult = f()",
    "registry": "from harness import host\nlazy import pkg.inner.leaf\nresult = sorted(n for n in host.lazy_modules() if n.split('.')[0] == 'pkg')",
    "submodule": "lazy import pkg.inner.leaf\np = pkg\ni = p.inner\nresult = i.leaf.subx",
    "in_function": "def f():\n    lazy import pkg",
    "in_try": "try:\n    lazy import pkg\nexcept ImportError:\n    pass",
    "in_class": "class C:\n    lazy import pkg",
    "star": "lazy from pkg import *",
    "future": "lazy from __future__ import annotations",
    "compat": "__lazy_modules__ = ['pkg']\nimport pkg\n" + PLACEHOLDER % "pkg",
    "compat_used": "__lazy_modules__ = ['pkg']\nimport pkg\nresult = pkg.pub",
    "compat_other": "__lazy_modules__ = ['other']\nimport pkg\n" + PLACEHOLDER % "pkg",
    "compat_from": "__lazy_modules__ = ['pkg']\nfrom pkg import sub\n" + PLACEHOLDER % "sub",
    "compat_try": "__lazy_modules__ = ['pkg']\ntry:\n    import pkg\nfinally:\n    pass\n" + PLACEHOLDER % "pkg",
    "compat_function": "__lazy_modules__ = ['pkg']\ndef f():\n    import pkg\n    return type(pkg).__name__\nresult = f()",
}


def clean():
    modules, lazy_modules = host.module_cache(), host.lazy_modules()
    for name in list(modules):
        if name.split(".")[0] in FIXTURES:
            del modules[name]
    for name in list(lazy_modules):
        if name.split(".")[0] in FIXTURES:
            lazy_modules.discard(name)


def outcome(p):
    clean()
    namespace = {}
    try:
        exec(SOURCES[p["case"]], namespace)
        result = repr(namespace.get("result"))
    except (ImportError, SyntaxError) as error:
        result = "%s: %s" % (type(error).__name__, str(error).split(" (")[0])
    import tracelog
    log = tracelog.events
    clean()
    return "%s %r" % (result, log)


check_programs(outcome)
