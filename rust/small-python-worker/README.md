# small-python-worker

Run untrusted Python, including code written by a language model, from Rust.
Each `Runtime` runs [Small Python](https://github.com/soasme/small-python)
in its own `spy-worker` process, sandboxed by the operating system, and
talks to it over pipes. Nothing the engine does, a memory-safety bug
included, can crash or take over the Rust program.

```rust
use small_python_worker::{Runtime, Value};
use std::time::Duration;

let mut rt = Runtime::builder().timeout(Duration::from_secs(5)).spawn()?;
rt.define("greet", |_, args, _| match &args[..] {
    [Value::Str(name)] => Ok(format!("hello {name}").into()),
    _ => Err(small_python_worker::Error::python("TypeError", "greet(name)")),
})?;
assert_eq!(rt.eval("greet('spy')")?, Value::from("hello spy"));
# Ok::<(), small_python_worker::Error>(())
```

The build script compiles the worker from source with the `cc` crate and
the crate embeds it; on first use it is written to the user's cache
directory. See `docs/packaging/rust.md` in the repository.
