"""Module resolution and discovery (docs/build.md 3).

Modules are found as CPython's path finder finds them over the search
roots, comparing names by exact spelling as FileFinder compares its
directory listing, whatever the file system's case rules. Imports are
followed from the entries until no module is left to visit.
"""

import sys

import _spyc
from . import scan

MODULE, PACKAGE, NAMESPACE, EXTERNAL, REGISTERED = "module", "package", "namespace", "external", "registered"


class Module:
    def __init__(self, name, path=None):
        self.name, self.path, self.kind, self.queued = name, path, None, False
        self.locations = []   # where a package's submodules are searched; each ends in '/' or is ''
        self.all = []         # a literal __all__
        self.source = None    # read once queued; minified with --minify
        self.bytes = 0        # the size of the file read
        self.array = None     # the C array of its source in the output
        self.imports = []     # (path, original, kind, flag): flag 1 external, 2 missing

    def found(self):
        return self.kind in (MODULE, PACKAGE, NAMESPACE)

    def key(self):
        return self.name + (".__init__" if self.kind == PACKAGE else ".__namespace__" if self.kind == NAMESPACE else "")


class Origin:
    """What an import reports against: a file and line, or an option."""

    def __init__(self, path=None, option=None, owner=None):
        self.path, self.option, self.line, self.owner = path, option, 0, owner


def under(prefix, name):
    return name == prefix or name.startswith(prefix + ".")


def entry_kind(directory, name):
    names = _spyc.listdir(directory or ".")
    return _spyc.kind(directory + name) if names is not None and name in names else None


class Build:
    def __init__(self, roots, externals, registered, natives, aliases, minify):
        self.roots, self.externals, self.registered, self.natives = roots, externals, registered, natives
        self.aliases, self.minify = aliases, minify
        self.modules, self.queue, self.stars = {}, [], []
        self.errors = self.warnings = 0

    def report(self, origin, message):
        if origin.option:
            print(f"spyc: error: {origin.option}: {message}", file=sys.stderr)
        else:
            print(f"{origin.path}:{origin.line}: error: {message}", file=sys.stderr)
        self.errors += 1

    def search(self, m, locations, tail):
        """FileFinder over each location in turn, keeping namespace
        portions (PathFinder)."""
        portions = []
        for d in locations:
            package = d + tail + "/"
            if entry_kind(d, tail) == "d" and entry_kind(package, "__init__.py") == "f":
                m.kind, m.path, m.locations = PACKAGE, package + "__init__.py", [package]
                return
            if entry_kind(d, tail + ".py") == "f":
                m.kind, m.path = MODULE, d + tail + ".py"
                return
            if entry_kind(d, tail) == "d":
                portions.append(package)
        if portions:
            m.kind, m.locations = NAMESPACE, portions

    def find(self, name):
        m = self.modules.get(name)
        if m:
            return m
        m = self.modules[name] = Module(name)
        if any(under(prefix, name) for prefix in self.externals):
            m.kind = EXTERNAL
        if name in self.registered or name in self.natives:
            m.kind = REGISTERED
        if m.kind:
            return m
        if name in self.aliases:
            target = self.find(self.aliases[name])
            if target.found():
                m.kind, m.path, m.locations = target.kind, target.path, list(target.locations)
            return m
        parent, dot, tail = name.rpartition(".")
        if not dot:
            self.search(m, self.roots, name)
        else:
            p = self.find(parent)
            if p.kind in (PACKAGE, NAMESPACE):
                self.search(m, p.locations, tail)
        return m

    def enqueue(self, m):
        if not m.queued:
            m.queued = True
            self.queue.append(m)

    def request(self, origin, name, required, kind):
        """An import of NAME: a required one that does not resolve fails the
        build with CPython's message; a guarded one, or a from-import name
        that may be an attribute, is left out."""
        m = self.find(name)
        if m.kind in (EXTERNAL, REGISTERED):
            record(origin.owner, name, name, kind, 1)
        elif m.found():
            self.enqueue(m)
            record(origin.owner, m.path or name, name, kind, 0)
        elif not required:
            if kind != "maybe":
                record(origin.owner, name, name, kind, 2)
        else:
            # The first part that is missing, or that is a module and not a package.
            parts = name.split(".")
            for n in range(1, len(parts)):
                prefix = ".".join(parts[:n])
                p = self.find(prefix)
                if not p.found():
                    return self.report(origin, f"No module named '{prefix}'")
                if p.kind == MODULE:
                    return self.report(origin, f"No module named '{name}'; '{prefix}' is not a package")
            self.report(origin, f"No module named '{name}'")

    def absolute(self, origin, package, level, name, required):
        """The absolute name of a relative import (PEP 328), or None with an
        error reported for a required one."""
        if not level:
            return name
        parts = package.split(".") if package else []
        if len(parts) < level:
            if required:
                self.report(origin, "attempted relative import beyond top-level package" if parts else
                            "attempted relative import with no known parent package")
            return None
        base = ".".join(parts[:len(parts) - level + 1])
        return base + "." + name if name else base

    def scan(self, m, package):
        """Read, walk, and with --minify minify the source of M."""
        m.source = _spyc.read(m.path)
        if m.source is None:
            print(f"spyc: error: cannot read {m.path}", file=sys.stderr)
            self.errors += 1
            return
        if b"\0" in m.source:
            m.source = m.source[:m.source.index(b"\0")]
        m.bytes = len(m.source)
        origin = Origin(m.path, None, m)
        try:
            compile(m.source, m.path, "exec")
        except SyntaxError as error:
            print(f"{m.path}:{error.lineno}: error: {error.msg}", file=sys.stderr)
            self.errors += 1
            return

        def request(name, required, kind, line):
            origin.line = line
            self.request(origin, name, required, kind)

        def warn(line, text):
            print(f"{m.path}:{line}: warning: {text}", file=sys.stderr)
            self.warnings += 1

        def resolve(level, name, required, line):
            origin.line = line
            return self.absolute(origin, package, level, name, required)

        m.all, stars = scan.scan(m.source, m.path, request, warn, resolve)
        self.stars += stars
        if not self.minify:
            return
        small = scan.minify(m.source, m.path)
        if small is None:
            print(f"{m.path}: error: --minify changed the program's tokens", file=sys.stderr)
            self.errors += 1
            return
        m.source = small

    def discover(self, entry):
        """Visit queued modules until none is left, then the submodules
        named by the __all__ of modules imported with *, which may queue
        more."""
        done, at = 0, 0
        while not self.errors:
            while not self.errors and at < len(self.queue):
                m = self.queue[at]
                at += 1
                parent, dot, _ = m.name.rpartition(".")
                if dot:
                    self.enqueue(self.find(parent))
                if m.path:
                    self.scan(m, m.name if m.kind == PACKAGE else parent)
            if self.errors or done == len(self.stars):
                break
            while done < len(self.stars):
                base = self.find(self.stars[done])
                origin = Origin(None, "from-import *", entry)
                for name in base.all:
                    self.request(origin, base.name + "." + name, False, "maybe")
                done += 1

    def include_all(self, origin, package):
        """-D PKG.*: every module and package below PKG, at any depth."""
        for d in package.locations:
            for e in sorted(_spyc.listdir(d or ".") or []):
                py = e.endswith(".py") and len(e) > 3
                stem = e[:-3] if py else e
                if not scan.identifier(stem) or (py and stem == "__init__"):
                    continue
                name = package.name + "." + stem
                m = self.find(name)
                if m.kind in (MODULE, PACKAGE):
                    self.request(origin, name, True, "include")
                if m.kind in (PACKAGE, NAMESPACE):
                    self.include_all(origin, m)


def record(owner, path, original, kind, flag):
    if owner is not None and not any(e[:3] == (path, original, kind) for e in owner.imports):
        owner.imports.append((path, original, kind, flag))
