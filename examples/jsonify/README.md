# jsonify

`jsonify FILE` prints a JSON file indented by two spaces, in color. The
program is Python ([`jsonify.py`](jsonify.py)): it opens the file, loads it
with `json`, and colors keys, strings, numbers and constants as it writes
them. The `json` module is Rust ([`src/lib.rs`](src/lib.rs)), on
[serde_json](https://crates.io/crates/serde_json).

```sh
make             # needs cargo; builds libjson.a, then the program
./jsonify package.json
make test        # compares json with the Python running the test
```

## How it is built

The crate is a `staticlib` named `json`, so cargo writes
`target/release/libjson.a`. It exports `spy_init_json`, which fills the
module, and calls the engine through the `spy.h` functions it declares in an
`extern "C"` block. It does not link an engine of its own: the program links
`libspy.a`. spyc takes the archive as an input and registers it as `json`
([docs/build.md 5.4](../../docs/build.md#54-native-modules)):

```sh
cargo build --release
spyc -o jsonify jsonify.py target/release/libjson.a -- $RUSTLIBS
```

`RUSTLIBS` is what Rust's standard library needs from the system: nothing
on macOS, and `-lgcc_s -lutil -lrt -lpthread -lm -ldl -lc` on Linux
(`rustc --print native-static-libs`). The program needs no Python file or
shared library at run time. It opens files under its working directory,
which the program mounts, and reads its arguments from `sys.argv`
([5.5](../../docs/build.md#55-the-programs-start)).

## The json module

`loads(s)`, `load(fp)`, `dumps(obj, *, indent=None, ensure_ascii=True,
allow_nan=True)` and `dump(obj, fp, ...)` work as Python's do for `dict`,
`list`, `tuple`, `str`, `int` of any size, `float`, `bool` and `None`.
Objects keep their key order, and later duplicate keys win. Numbers keep
their text, so `dumps` writes floats as `repr` does. `loads` takes `str` or
UTF-8 `bytes`. [`probe.py`](probe.py) runs under CPython and as a built
program, and `make test` requires both to print the same, for about 150
values, separators, indents, escapes and errors.

Where it differs from Python's json:

- Errors are `ValueError` with serde_json's message, not `JSONDecodeError`.
- `loads` does not read `NaN`, `Infinity` or `-Infinity`, and neither form
  reads a lone surrogate (`"\udcff"`), which raise `ValueError`.
- Arrays and objects nest at most 1000 deep in either direction; deeper
  ones raise `RecursionError`, where CPython goes on to its stack's limit.
- No other keyword arguments (`sort_keys`, `separators`, `default`, `cls`,
  hooks), no subclasses of the container types, and no encoder or decoder
  classes.
