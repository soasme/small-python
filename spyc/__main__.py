"""spyc: build a Python program into one C file and an executable, and run
or test programs so built (docs/build.md).

spyc is itself a Python program on spy: this package, with the C module
_spyc for the host services, built into one executable by the previous
release's spyc (docs/build.md 9).
"""

import _spyc   # first: it registers _spy
import _spy
from . import output, scan
from .resolve import MODULE, PACKAGE, NAMESPACE, NATIVE, STANDARD, Build, Module, Origin, stderr

USAGE = """\
usage: spyc [build] [options] [-o program] (input.py | -m module) [module.c | libmodule.a]... [-- cc-arguments]
       spyc [build] -e [options] [-o program.c] (input.py | -m module) [module.c | libmodule.a]...
       spyc [build] -c [options] [-o modules.c] (input.py | -m module)...
       spyc run [options] [module.c | libmodule.a]... (input.py | -m module) [argument]...
       spyc test [options] [module.c | libmodule.a]... [test.py | directory]...
       spyc clean
       spyc version
options: -I dir, -x module, -D module[.*], -N name, --alias name=target,
         -O, -OO, --minify, --metafile file, --deps file, --analyze, -Werror, -v
"""
CACHE = "__pycache__/spyc"   # spyc run and spyc test build here (docs/build.md 2.3)
TAKES = ("-o", "-m", "-I", "-x", "-D", "-N", "--alias", "--metafile", "--deps")


class Usage(Exception):
    pass


def error(text):
    stderr(f"spyc: error: {text}")


def command(words):
    """A command line for _spyc: each word, as the system's bytes, ended by NUL."""
    return b"".join(word.encode("utf-8", "surrogateescape") + b"\0" for word in words)


def home(self, installed):
    """Where spy.h and the libraries are: beside spyc, or a directory up
    from a build tree's bin/, or else under the install prefix."""
    directory = self.rpartition("/")[0] if "/" in self else "."
    head, slash, tail = directory.rpartition("/")
    parent = (head or "/") if slash else ".." if directory == "." else "."
    for candidate in (directory, parent):
        if _spyc.kind(candidate + "/spy.h") == "f":
            return candidate
    return _spyc.prefix + installed


class Entry:
    """An entry: the __file__ and __package__ it runs with, its C name, and
    its file, read as a module that names no table entry."""

    def __init__(self, path, file, package, symbol):
        self.module, self.file, self.package, self.symbol = Module(None, path), file, package, symbol


class Options:
    def __init__(self, args, cached):
        self.files, self.mains, self.includes, self.more = [], [], [], []   # more: cc's arguments
        self.roots, self.externals, self.natives, self.aliases = [], [], {}, {}   # natives: name to file
        self.output = self.metafile = self.deps = self.loader = None
        self.bare = self.with_main = self.verbose = self.analyze = self.werror = self.minify = False
        self.optimize, self.passed, self.rest = 0, False, len(args)
        i = 0
        while i < len(args):
            a = args[i]
            value = args[i + 1] if i + 1 < len(args) else None
            i += 1
            if self.passed or a == "--":
                if self.passed:
                    self.more.append(a)
                self.passed = True
                continue
            if len(a) > 2 and a[-2:] in (".c", ".a"):
                # A C module, NAME.c or the archive libNAME.a, exporting spy_init_NAME.
                base = a.rpartition("/")[2]
                skip = 3 if a[-1] == "a" else 0
                name = base[skip:-2]
                if not base.startswith("lib"[:skip]) or not scan.identifier(name) or name in self.natives:
                    raise Usage
                self.natives[name] = a
                continue
            takes = a in TAKES
            if takes and value is None:
                raise Usage
            if takes:
                i += 1
            if a == "-c":
                self.bare = True
            elif a == "-e":
                self.with_main = True
            elif a == "-v":
                self.verbose = True
            elif a == "--analyze":
                self.analyze = True
            elif a == "-Werror":
                self.werror = True
            elif a == "--minify":
                self.minify = True
            elif a in ("-O", "-OO"):
                self.optimize = len(a) - 1
            elif a == "-o":
                self.output = value
            elif a == "--metafile":
                self.metafile = value
            elif a == "--deps":
                self.deps = value
            elif a == "-I":
                self.roots.append(value if not value or value.endswith("/") else value + "/")
            elif a == "-N":
                if not scan.identifier(value):
                    raise Usage
                self.loader = value
            elif a == "--alias":
                name, equals, target = value.partition("=")
                if not equals or not scan.dotted(name) or not scan.dotted(target):
                    raise Usage
                self.aliases[name] = target
            elif takes:
                star = a == "-D" and len(value) > 2 and value.endswith(".*")
                name = value[:-2] if star else value
                if not scan.dotted(name):
                    raise Usage
                {"-m": self.mains, "-x": self.externals, "-D": self.includes}[a].append(value)
            elif a.startswith("-"):
                raise Usage
            else:
                self.files.append(a)
            if cached and self.files + self.mains:
                self.rest = i
                break
        entries = len(self.files) + len(self.mains)
        if not entries or (self.bare and self.with_main) or (not self.bare and entries > 1) or \
                (self.bare and (self.natives or self.optimize)) or \
                ((self.bare or self.with_main) and self.passed) or \
                (cached and (self.bare or self.with_main or self.passed or self.output)):
            raise Usage
        self.executable = not self.bare and not self.with_main
        if self.output is None:
            self.output = CACHE if cached else "a.out" if self.executable else "out.c"
        if self.output in self.files or self.output in self.natives.values():
            raise Usage


def build(self, args, cached=False):
    """One build of ARGS. With CACHED, for spyc run and spyc test, the
    arguments end at the entry and the executable is built in the cache.
    (status, the executable in the cache, the index after the entry)."""
    try:
        o = Options(args, cached)
    except Usage:
        _spy._write(USAGE, True)
        return 2, None, 0
    _spyc.guard()
    status, program = 1, None
    try:
        status, program = compose(self, args, o, cached)
    except OSError as e:
        error(e)
    _spyc.done(status != 0)
    return status, program, o.rest


def compose(self, args, o, cached):
    # The first root is the entry's directory, or the working directory for -m.
    first = o.files[0].rpartition("/")[0] + "/" if o.files and "/" in o.files[0] else ""
    b = Build([first] + o.roots, o.externals, o.natives, o.aliases, o.minify, o.bare)
    entries = []
    for path in o.files:
        e = Entry(path, path.rpartition("/")[2], None, output.c_name(path, False))
        entries.append(e)
        b.scan(e.module, None)
        if b.errors:
            break
    for name in o.mains if not b.errors else []:
        # -m runs MODULE, or a package's __main__, with its package set.
        m = b.find(name)
        run = name + ".__main__" if m.kind == PACKAGE else name
        target = b.find(run)
        if target.kind != MODULE:
            b.report(Origin(None, "-m"), f"No module named '{run}'")
            break
        e = Entry(target.path, run.replace(".", "/") + ".py", run.rpartition(".")[0], output.c_name(name, True))
        entries.append(e)
        if e.package:
            b.enqueue(b.find(e.package))
        b.scan(e.module, e.package)
    for include in o.includes if not b.errors else []:
        origin = Origin(None, "-D " + include, entries[0].module)
        if include.endswith(".*") and len(include) > 2:
            package = b.find(include[:-2])
            if package.kind in (PACKAGE, NAMESPACE):
                b.include_all(origin, package)
            elif package.found():
                b.report(origin, f"'{include[:-2]}' is not a package")
            else:
                b.request(origin, include[:-2], True, "include")
        else:
            b.request(origin, include, True, "include")
        if b.errors:
            break
    if not b.errors:
        b.discover(entries[0].module)
    if o.werror and b.warnings:
        b.errors += 1
    if b.errors:
        return 1, None

    # The modules the program registers: the standard ones it imports, and
    # the C modules, those named first, then those found, by name. Each C
    # module's init is spy_init_ and its last name.
    reached = sorted((m for m in b.modules.values() if m.queued), key=lambda m: m.name)
    o.standard = [m.name for m in reached if m.kind == STANDARD]
    natives = [b.find(name) for name in o.natives] + [m for m in reached if m.kind == NATIVE and m.name not in o.natives]
    inits = {}
    for m in natives:
        m.array = "spy_init_" + m.name.rpartition(".")[2]
        if m.array in inits:
            error(f"{inits[m.array].path} and {m.path} both define {m.array}")
            return 1, None
        inits[m.array] = m
    o.natives = natives

    # The table, sorted by the keys the loader answers; the inputs, the
    # entries and then the table's other files, each with the C array
    # holding its source. A module that is also an entry shares its array.
    table = sorted((m for m in b.modules.values() if m.queued and m.found()), key=Module.key)
    inputs = []
    for e in entries:
        e.module.array = e.symbol if o.bare else "source"
        inputs.append(e.module)
    for i, m in enumerate(table):
        shared = next((e for e in entries if e.module.path == m.path), None) if m.path else None
        if not m.path:
            m.array = '""'
        elif shared:
            m.array = shared.module.array
        else:
            m.array = f"module_{i}"
            inputs.append(m)
    loader = (o.loader or entries[0].symbol) + "_load"
    code = output.generate(entries, table, inputs, loader, o.bare, o.standard, o.natives, o.optimize)

    program = None
    if cached:
        program = cache(self, args[:o.rest], code, o)
        if program is None:
            return 1, None
        o.output = program
    elif o.executable:
        if not compile_c(self, o.output, code, o):
            return 1, None
    elif not _spyc.write(o.output, code):
        error(f"cannot write {o.output}")
        return 1, None
    if o.metafile and not _spyc.write(o.metafile, output.metafile(inputs, o.output, len(code), entries[0].module.path)):
        error(f"cannot write {o.metafile}")
        return 1, None
    if o.deps and not _spyc.write(o.deps, output.rule(o.output, inputs, [m.path for m in o.natives]).encode("utf-8")):
        error(f"cannot write {o.deps}")
        return 1, None
    if o.analyze:
        # The inputs, largest in the output first.
        stderr(f"  {o.output}  {len(code)} bytes")
        for m in sorted(inputs, key=lambda m: (-len(m.source), m.path)):
            stderr(f"    {m.path}  {len(m.source)}")
    return 0, program


def compile_c(self, target, code, o):
    """The executable: the C compiler of spyc's build compiles the C file,
    written to a temporary file, the C modules, and the arguments after --,
    against spy.h and the libraries."""
    source = _spyc.temp(code)
    include, lib = home(self, "/include"), home(self, "/lib")
    args = _spyc.cc.split() + ["-O2", "-I", include, "-o", target, "-x", "c", source, "-x", "none"] + [m.path for m in o.natives] + o.more
    args += ([lib + "/libspy-std.a"] if o.standard else []) + [lib + "/libspy.a", "-lm"]
    if o.verbose:
        print(" ".join(args))
    try:
        ok = _spyc.compile(target, command(args))
    finally:
        _spyc.unlink(source)
    return ok


def fnv(h, data):
    return _spyc.fnv(h, data) if data is not None else h


def cache(self, words, code, o):
    """spyc run and spyc test build into the cache, __pycache__/spyc in the
    working directory (docs/build.md 2.3). An executable is named by two hashes:
    its slot, of the build's arguments, and its stamp, of what it is made
    from: the C file, the compiler, the C modules, spy.h and the libraries.
    A name that exists is complete: the compiler writes beside it, and the
    file is renamed into place. The build then removes its slot's other
    stamps. The executable, or None."""
    basis = 0xcbf29ce484222325 - (1 << 64)   # FNV-1a's offset basis, as a signed 64-bit int
    slot, stamp = basis, fnv(basis, (_spyc.cc + "\0").encode("utf-8"))
    for word in words:
        slot = fnv(slot, (word + "\0").encode("utf-8"))
    stamp = fnv(stamp, code)
    for m in o.natives:
        stamp = fnv(stamp, _spyc.read(m.path))
    include, lib = home(self, "/include"), home(self, "/lib")
    made = [include + "/spy.h"] + ([include + "/spy-std.h", lib + "/libspy-std.a"] if o.standard else []) + [lib + "/libspy.a"]
    for path in made:
        stamp = fnv(stamp, _spyc.read(path))
    name = f"{CACHE}/{slot & 0xffffffffffffffff:016x}-{stamp & 0xffffffffffffffff:016x}"
    if _spyc.executable(name):
        return name
    temp = f"{name}.{_spyc.pid()}"
    _spyc.mkdir("__pycache__")
    _spyc.mkdir(CACHE)
    if not compile_c(self, temp, code, o):
        return None
    if not _spyc.rename(temp, name):
        error(f"cannot write {name}")
        return None
    base = name[len(CACHE) + 1:]
    for entry in _spyc.listdir(CACHE) or []:
        if len(entry) == 33 and entry[:17] == base[:17] and entry != base:
            _spyc.unlink(CACHE + "/" + entry)
    return name


def gather(tests, path, named):
    """spyc test: each test file below PATH, test_*.py, in name order;
    hidden directories are passed over. PATH is a test if it is a file."""
    kind = _spyc.kind(path)
    if kind == "f":
        base = path.rpartition("/")[2]
        if named or (base.startswith("test_") and base.endswith(".py")):
            tests.append(path)
    elif kind == "d":
        for name in sorted(_spyc.listdir(path) or []):
            if not name.startswith("."):
                gather(tests, name if path == "." else path + ("" if path.endswith("/") else "/") + name, False)


def test(self, args):
    words, paths, tests = [], [], []
    i = 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "-m":
            _spy._write(USAGE, True)
            return 2
        if a.startswith("-") or (len(a) > 2 and a[-2:] in (".c", ".a")):
            words.append(a)
            if a in TAKES and i < len(args):
                words.append(args[i])
                i += 1
        else:
            paths.append(a)
    for path in paths or ["."]:
        before = len(tests)
        gather(tests, path, True)
        if len(tests) == before:
            error(f"no tests in {path}")
            return 1
    passed = failed = 0
    for path in tests:
        status, program, _ = build(self, words + [path], True)
        if status == 2:
            return 2
        if not status:
            try:
                status = _spyc.spawn(program, command([path]))
            except OSError as e:
                error(e)
                status = 1
            print(f"ok    {path}" if not status else f"FAIL  {path} (exit {status})")
        else:
            print(f"FAIL  {path} (build)")
        failed += status != 0
        passed += status == 0
    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


def clean():
    """spyc clean: the cache's files, then the cache, if nothing else is in
    it, and __pycache__, if that is empty then."""
    names = _spyc.listdir(CACHE)
    if names is None:
        return 0
    for name in names:
        if len(name) > 16 and all(ch in "0123456789abcdef" for ch in name[:16]) and name[16] == "-":
            _spyc.unlink(CACHE + "/" + name)
    failure = _spyc.rmdir(CACHE)
    if failure:
        error(f"cannot remove {CACHE}: {failure}")
        return 1
    _spyc.rmdir("__pycache__")
    return 0


def main(argv):
    self, verb, args = argv[0], argv[1] if len(argv) > 1 else "", argv[2:]
    if verb in ("version", "clean") and args:
        _spy._write(USAGE, True)
        return 2
    if verb == "version":
        print("spyc " + _spyc.version)
        return 0
    if verb == "clean":
        return clean()
    if verb == "test":
        return test(self, args)
    if verb != "run":
        return build(self, argv[2:] if verb == "build" else argv[1:])[0]
    status, program, rest = build(self, args, True)
    if status:
        return status
    # The program's arguments: the entry as given, then the rest.
    try:
        _spyc.exec(program, command(args[rest - 1:]))
    except OSError as e:
        error(e)
    return 1


raise SystemExit(main(list(_spy.argv)))
