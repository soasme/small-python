# small-python-src

The C sources of [Small Python](https://github.com/soasme/small-python), a
small embeddable Python engine, packaged for the build scripts of
`small-python-sys` and `small-python-worker`. You probably want [`small-python`](https://crates.io/crates/small-python) or
[`small-python-worker`](https://crates.io/crates/small-python-worker) instead.

The engine is C11 and needs only the C runtime and the math library. MSVC
lacks C11 complex numbers; on Windows build for `x86_64-pc-windows-gnu`.
The Unicode and Python licenses of the tables it carries are in
`csrc/licenses/`.
