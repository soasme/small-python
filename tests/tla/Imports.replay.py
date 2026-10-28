# Replays Imports.tla: each case clears the fixture modules (Imports.files)
# from the module cache, runs the spec's import statements, and compares the
# result and the modules' run log with the model's.
from harness import host

FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

FIXTURES = ("pkg", "nspkg", "plain", "cycle_a", "cycle_b", "tracelog")
SOURCES = {
    "import_sub": "import pkg.sub\nresult = pkg.sub.x",
    "binds": "import pkg.sub\nresult = sorted(k for k in dir() if not k.startswith('__'))",
    "import_as": "import pkg.sub as s\nresult = s.__name__",
    "from_submodule": "from pkg import sub\nresult = sub.x",
    "from_missing": "from pkg import missing",
    "from_star": "from pkg import *\nresult = sorted(k for k in dir() if not k.startswith('__'))",
    "relative": "import pkg.inner\nresult = (pkg.inner.leaf.subx, pkg.inner.up.__name__)",
    "broken": "from harness import host\ntry:\n    import pkg.broken\nexcept ValueError:\n"
              "    result = ('pkg.broken' in host.module_cache(), 'pkg' in host.module_cache(), hasattr(host.module_cache()['pkg'], 'broken'))",
    "beyond": "import pkg.beyond",
    "no_parent": "import plain",
    "namespace": "import nspkg.mod\nresult = (nspkg.__file__, all(type(p) is str for p in nspkg.__path__), nspkg.mod.__package__)",
    "twice": "import pkg\nimport pkg\nimport pkg.sub\nimport pkg.sub\nresult = 'twice'",
    "none_cached": "from harness import host\nhost.module_cache()['pkg'] = None\nimport pkg",
    "replaced": "from harness import host\nhost.module_cache()['pkg'] = 5\nimport pkg\nresult = pkg",
    "cycle": "import cycle_a\nresult = cycle_a.cycle_b.B",
    "attributes": "import pkg.sub\nresult = (pkg.__name__, pkg.__package__, pkg.sub.__package__, hasattr(pkg, '__path__'),"
                  " hasattr(pkg.sub, '__path__'))",
    "plain_attributes": "import cycle_b\nresult = (cycle_b.__package__, hasattr(cycle_b, '__path__'))",
    "missing_module": "import nosuchmodule",
    "missing_sub": "import pkg.nosuch",
    "from_inner_missing": "from pkg.inner import nothing",
}


def clean():
    modules = host.module_cache()
    for name in list(modules):
        if name.split(".")[0] in FIXTURES:
            del modules[name]


def outcome(p):
    clean()
    namespace = {}
    try:
        exec(SOURCES[p["case"]], namespace)
        result = repr(namespace.get("result"))
    except ImportError as error:
        result = "%s: %s" % (type(error).__name__, str(error).split(" (")[0])
    import tracelog
    log = tracelog.events
    clean()
    return "%s %r" % (result, log)


check_programs(outcome)
