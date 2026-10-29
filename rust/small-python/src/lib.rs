//! Embed [Small Python](https://github.com/soasme/small-python), a small
//! Python 3.15 engine written in C11, in a Rust program.
//!
//! The engine is compiled from source by `small-python-sys`, so there is
//! nothing to install. A [`Runtime`] owns one engine context; every
//! [`Value`] borrows the runtime it came from, so values cannot outlive it.
//!
//! ```
//! use small_python::{Runtime, Result};
//!
//! # fn main() -> Result<()> {
//! let rt = Runtime::new()?;
//! rt.define("add", |rt, args| {
//!     let (a, b): (i64, i64) = args.extract()?;
//!     rt.to_py(a + b)
//! })?;
//! let n: i64 = rt.eval("add(40, 2)")?;
//! assert_eq!(n, 42);
//! # Ok(())
//! # }
//! ```
//!
//! The engine runs in this process, so it is only as trustworthy as its C
//! code. To run untrusted code, use `small-python-worker`, which runs each
//! runtime in its own sandboxed process.

use std::cell::RefCell;
use std::collections::HashMap;
use std::ffi::{c_char, c_int, c_void, CStr, CString};
use std::mem::ManuallyDrop;
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::path::Path;
use std::ptr::NonNull;
use std::sync::Arc;

pub use ffi;

mod conv;
mod error;
#[cfg(feature = "serde")]
mod serde;
mod value;

pub use conv::{FromArgs, FromPy, IntoArgs, IntoPy};
pub use error::{Error, Result};
pub use value::{Args, Iter, Value};

/// The engine version, as `spy.h` defines it.
pub const SPY_VERSION: &str = ffi::SPY_VERSION;

type HostFn = Box<dyn for<'a> Fn(&'a Runtime, Args<'a>) -> Result<Value<'a>> + Send>;
type Output = Box<dyn FnMut(&str) + Send>;
type Loader = Box<dyn FnMut(&str) -> Option<String> + Send>;
type ModuleInit = Arc<dyn for<'a> Fn(&'a Runtime, &Value<'a>) -> Result<()> + Send + Sync>;

/// What the context's callbacks reach through its opaque pointer.
#[derive(Default)]
struct Hooks {
    output: RefCell<Option<Output>>,
    loader: RefCell<Option<Loader>>,
    modules: RefCell<HashMap<String, ModuleInit>>,
}

/// One independent engine context.
///
/// A runtime may move between threads but is used by one at a time.
/// Inside a host function, the `&Runtime` it receives is the same context.
pub struct Runtime {
    ctx: NonNull<ffi::SPYContext>,
    hooks: NonNull<Hooks>,
}

// A context has no thread-affine state, and everything stored with it is Send.
unsafe impl Send for Runtime {}

impl Runtime {
    /// A runtime with the standard modules (`sys`, `gc`, `weakref`, ...).
    pub fn new() -> Result<Runtime> {
        let rt = Runtime::bare()?;
        rt.check(unsafe { ffi::spy_std_init(rt.ctx()) })?;
        Ok(rt)
    }

    /// A runtime with only the language core and its `builtins`.
    pub fn bare() -> Result<Runtime> {
        let ctx = NonNull::new(unsafe { ffi::spy_context_new() })
            .ok_or_else(|| Error::new("MemoryError", "cannot create a context"))?;
        let hooks = NonNull::from(Box::leak(Box::<Hooks>::default()));
        unsafe { ffi::spy_set_opaque(ctx.as_ptr(), hooks.as_ptr().cast()) };
        Ok(Runtime { ctx, hooks })
    }

    /// Runs `source` and converts the value of its last expression statement.
    pub fn eval<'rt, T: FromPy<'rt>>(&'rt self, source: &str) -> Result<T> {
        let source = c_source(source)?;
        let value = unsafe { ffi::spy_eval(self.ctx(), source.as_ptr(), c"<string>".as_ptr()) };
        T::from_py(&self.wrap(value)?)
    }

    /// Runs `source` for its effects.
    pub fn exec(&self, source: &str) -> Result<()> {
        let source = c_source(source)?;
        self.check(unsafe { ffi::spy_exec(self.ctx(), source.as_ptr(), c"<string>".as_ptr()) })
    }

    /// Reads a global.
    pub fn get<'rt, T: FromPy<'rt>>(&'rt self, name: &str) -> Result<T> {
        let name = c_name(name)?;
        T::from_py(&self.wrap(unsafe { ffi::spy_get_global(self.ctx(), name.as_ptr()) })?)
    }

    /// Sets a global.
    pub fn set(&self, name: &str, value: impl IntoPy) -> Result<()> {
        let value = value.into_py(self)?;
        let name = c_name(name)?;
        self.check(unsafe { ffi::spy_set_global(self.ctx(), name.as_ptr(), value.as_ptr()) })
    }

    /// Converts a Rust value into an engine value.
    pub fn to_py(&self, value: impl IntoPy) -> Result<Value<'_>> {
        value.into_py(self)
    }

    /// A builtin function calling `f` with the call's arguments. The engine
    /// keeps `f` until the function value is freed.
    pub fn function<F>(&self, name: &str, f: F) -> Result<Value<'_>>
    where
        F: for<'a> Fn(&'a Runtime, Args<'a>) -> Result<Value<'a>> + Send + 'static,
    {
        let name = c_name(name)?;
        let data = Box::into_raw(Box::new(Box::new(f) as HostFn));
        self.wrap(unsafe { ffi::spy_native(self.ctx(), name.as_ptr(), call_host, data.cast(), Some(release_host)) })
    }

    /// Binds [`function`](Runtime::function) as the global `name`.
    pub fn define<F>(&self, name: &str, f: F) -> Result<()>
    where
        F: for<'a> Fn(&'a Runtime, Args<'a>) -> Result<Value<'a>> + Send + 'static,
    {
        self.set(name, self.function(name, f)?)
    }

    /// Makes `import name` create a module and call `init` to fill it, as
    /// QuickJS's `JS_NewCModule`. Registering a name again replaces `init`.
    pub fn register_module<F>(&self, name: &str, init: F) -> Result<()>
    where
        F: for<'a> Fn(&'a Runtime, &Value<'a>) -> Result<()> + Send + Sync + 'static,
    {
        let cname = c_name(name)?;
        self.hooks().modules.borrow_mut().insert(name.to_owned(), Arc::new(init));
        self.check(unsafe { ffi::spy_new_module(self.ctx(), cname.as_ptr(), init_module) })
    }

    /// Runs `source` with `module`'s namespace as its globals.
    pub fn exec_module(&self, module: &Value<'_>, source: &str, filename: &str) -> Result<()> {
        let source = c_source(source)?;
        let filename = c_name(filename)?;
        let module = module.clone().into_py(self)?;
        self.check(unsafe { ffi::spy_exec_module(self.ctx(), module.as_ptr(), source.as_ptr(), filename.as_ptr()) })
    }

    /// Receives everything engine code prints. Without it, output goes to
    /// the process's standard output.
    pub fn set_output(&self, output: impl FnMut(&str) + Send + 'static) {
        *self.hooks().output.borrow_mut() = Some(Box::new(output));
        unsafe { ffi::spy_set_output(self.ctx(), Some(write_output), self.hooks.as_ptr().cast()) };
    }

    /// Maps a module name to its source, or `None` when there is none. For
    /// `import pkg.mod` it is asked for `pkg.mod.__init__` (a package), then
    /// `pkg.mod`, then `pkg.mod.__namespace__` (a namespace package).
    pub fn set_loader(&self, loader: impl FnMut(&str) -> Option<String> + Send + 'static) {
        *self.hooks().loader.borrow_mut() = Some(Box::new(loader));
        unsafe { ffi::spy_set_module_loader(self.ctx(), Some(load_module), self.hooks.as_ptr().cast()) };
    }

    /// Lets `open()` reach `directory` at the absolute engine path `path`
    /// (default: the directory's own resolved path).
    pub fn mount(&self, directory: impl AsRef<Path>, path: Option<&str>, read_only: bool) -> Result<()> {
        let directory = directory.as_ref().to_str().ok_or_else(|| Error::new("ValueError", "path is not UTF-8"))?;
        let directory = c_name(directory)?;
        let path = path.map(c_name).transpose()?;
        let flags = if read_only { ffi::SPY_MOUNT_READ_ONLY } else { 0 };
        let path = path.as_ref().map_or(std::ptr::null(), |p| p.as_ptr());
        self.check(unsafe { ffi::spy_mount(self.ctx(), directory.as_ptr(), path, flags) })
    }

    /// Bounds the evaluation steps of each top-level `eval` or `exec`; 0 is
    /// unlimited. Exceeding it raises `RuntimeError`.
    pub fn set_step_limit(&self, limit: usize) {
        unsafe { ffi::spy_set_step_limit(self.ctx(), limit) }
    }

    /// The optimization level, as `python -O` (1) and `-OO` (2).
    pub fn set_optimize(&self, level: i32) {
        unsafe { ffi::spy_set_optimize(self.ctx(), level) }
    }

    /// Runs the cycle collector; returns the number of values freed.
    pub fn collect(&self) -> usize {
        unsafe { ffi::spy_collect(self.ctx()) }
    }

    /// The context, for calls into [`ffi`].
    pub fn ctx(&self) -> *mut ffi::SPYContext {
        self.ctx.as_ptr()
    }

    fn hooks(&self) -> &Hooks {
        unsafe { self.hooks.as_ref() }
    }

    /// An owned engine result as a value, or the pending error.
    pub(crate) fn wrap(&self, value: *mut ffi::SPYValue) -> Result<Value<'_>> {
        match NonNull::new(value) {
            Some(ptr) => Ok(unsafe { Value::from_raw(self, ptr) }),
            None => Err(unsafe { Error::take(self.ctx()) }),
        }
    }

    pub(crate) fn check(&self, status: c_int) -> Result<()> {
        if status == 0 {
            Ok(())
        } else {
            Err(unsafe { Error::take(self.ctx()) })
        }
    }

    /// The runtime a callback runs in: the same context, not owned.
    unsafe fn borrowed(c: *mut ffi::SPYContext) -> ManuallyDrop<Runtime> {
        let hooks = ffi::spy_get_opaque(c).cast::<Hooks>();
        ManuallyDrop::new(Runtime { ctx: NonNull::new_unchecked(c), hooks: NonNull::new_unchecked(hooks) })
    }
}

impl Drop for Runtime {
    fn drop(&mut self) {
        // Every Value borrows the runtime, so none is left to release.
        unsafe {
            ffi::spy_context_free(self.ctx());
            drop(Box::from_raw(self.hooks.as_ptr()));
        }
    }
}

/// Runs a Rust callback for the engine, turning an error or a panic into an
/// engine exception: a panic must not unwind into C.
fn guard(c: *mut ffi::SPYContext, f: impl FnOnce() -> Result<*mut ffi::SPYValue>) -> *mut ffi::SPYValue {
    match catch_unwind(AssertUnwindSafe(f)) {
        Ok(Ok(value)) => value,
        Ok(Err(error)) => unsafe { error.raise(c) },
        Err(panic) => {
            let what = panic.downcast_ref::<&str>().copied().or(panic.downcast_ref::<String>().map(String::as_str));
            let message = format!("a Rust callback panicked: {}", what.unwrap_or("Box<dyn Any>"));
            unsafe { Error::new("RuntimeError", message).raise(c) }
        }
    }
}

unsafe extern "C" fn call_host(
    c: *mut ffi::SPYContext,
    argc: usize,
    argv: *const *mut ffi::SPYValue,
    keywords: *mut ffi::SPYValue,
    data: *mut c_void,
) -> *mut ffi::SPYValue {
    let f = &*data.cast::<HostFn>();
    let rt = Runtime::borrowed(c);
    guard(c, || {
        let args = Args::new(&rt, argc, argv, keywords);
        Ok(f(&rt, args)?.into_raw())
    })
}

unsafe extern "C" fn release_host(data: *mut c_void) {
    drop(Box::from_raw(data.cast::<HostFn>()));
}

unsafe extern "C" fn init_module(c: *mut ffi::SPYContext, module: *mut ffi::SPYValue) -> c_int {
    let rt = Runtime::borrowed(c);
    let result = guard(c, || {
        let module = Value::from_raw(&rt, NonNull::new_unchecked(ffi::spy_retain(module)));
        let name: String = module.getattr("__name__")?.extract()?;
        let init = rt.hooks().modules.borrow().get(&name).cloned();
        let init = init.ok_or_else(|| Error::new("ImportError", format!("no module named '{name}'")))?;
        init(&rt, &module)?;
        Ok(ffi::spy_none(c))
    });
    if result.is_null() {
        return -1;
    }
    ffi::spy_release(result);
    0
}

unsafe extern "C" fn write_output(data: *mut c_void, text: *const c_char, n: usize) -> c_int {
    let hooks = &*data.cast::<Hooks>();
    let text = String::from_utf8_lossy(std::slice::from_raw_parts(text.cast::<u8>(), n));
    let written = catch_unwind(AssertUnwindSafe(|| {
        if let Some(output) = hooks.output.borrow_mut().as_mut() {
            output(&text);
        }
    }));
    if written.is_ok() {
        0
    } else {
        -1
    }
}

extern "C" {
    fn malloc(size: usize) -> *mut c_void;
}

unsafe extern "C" fn load_module(data: *mut c_void, name: *const c_char) -> *mut c_char {
    let hooks = &*data.cast::<Hooks>();
    let name = CStr::from_ptr(name).to_string_lossy();
    let source = catch_unwind(AssertUnwindSafe(|| hooks.loader.borrow_mut().as_mut().and_then(|load| load(&name))));
    let Ok(Some(source)) = source else { return std::ptr::null_mut() };
    // The engine frees the source with free().
    let copy = malloc(source.len() + 1).cast::<u8>();
    if !copy.is_null() {
        std::ptr::copy_nonoverlapping(source.as_ptr(), copy, source.len());
        *copy.add(source.len()) = 0;
    }
    copy.cast()
}

/// Text for the engine's own messages: an interior NUL ends it.
pub(crate) fn cstring(text: &str) -> CString {
    CString::new(text.split('\0').next().unwrap_or_default()).unwrap_or_default()
}

pub(crate) fn c_name(name: &str) -> Result<CString> {
    CString::new(name).map_err(|_| Error::new("ValueError", "embedded null character"))
}

fn c_source(source: &str) -> Result<CString> {
    CString::new(source).map_err(|_| Error::new("SyntaxError", "source code string cannot contain null bytes"))
}
