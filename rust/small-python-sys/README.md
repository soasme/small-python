# small-python-sys

Raw bindings to the C API of [Small Python](https://github.com/soasme/small-python)
(`spy.h` and `spy-std.h`). The build script compiles the engine from the
sources in [`small-python-src`](https://crates.io/crates/small-python-src)
with the `cc` crate and links it statically, so nothing needs to be
installed. Use [`small-python`](https://crates.io/crates/small-python) for a
safe API.
