# small-python

Embed [Small Python](https://github.com/soasme/small-python), a small Python
3.15 engine written in C11, in Rust. The engine is compiled from source by
`small-python-sys` with the `cc` crate, so there is nothing to install.

```rust
use small_python::{Result, Runtime};

fn main() -> Result<()> {
    let rt = Runtime::new()?;
    rt.define("add", |rt, args| {
        let (a, b): (i64, i64) = args.extract()?;
        rt.to_py(a + b)
    })?;
    let n: i64 = rt.eval("add(40, 2)")?;
    assert_eq!(n, 42);
    Ok(())
}
```

The `serde` feature converts any `Serialize` value in with
`Runtime::to_value` and any `Deserialize` value out with
`Runtime::from_value`.

The engine runs in your process. For untrusted code, use
[`small-python-worker`](https://crates.io/crates/small-python-worker), which
runs each runtime in a sandboxed process of its own. See
`docs/packaging/rust.md` in the repository.
