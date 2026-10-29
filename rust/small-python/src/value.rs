use std::fmt;
use std::ptr::NonNull;

use crate::conv::{FromArgs, FromPy, IntoArgs, IntoPy};
use crate::{c_name, ffi, Result, Runtime};

/// An owned reference to an engine value. It borrows its runtime, and
/// releases its reference when dropped.
pub struct Value<'rt> {
    rt: &'rt Runtime,
    ptr: NonNull<ffi::SPYValue>,
}

impl<'rt> Value<'rt> {
    /// Takes ownership of a reference returned by the C API.
    ///
    /// # Safety
    /// `ptr` must be an owned reference to a value of `rt`'s context.
    pub unsafe fn from_raw(rt: &'rt Runtime, ptr: NonNull<ffi::SPYValue>) -> Value<'rt> {
        Value { rt, ptr }
    }

    /// Gives up ownership of the reference, for returning it to the C API.
    pub fn into_raw(self) -> *mut ffi::SPYValue {
        let ptr = self.ptr.as_ptr();
        std::mem::forget(self);
        ptr
    }

    /// The value, borrowed, for calls into [`ffi`](crate::ffi).
    pub fn as_ptr(&self) -> *mut ffi::SPYValue {
        self.ptr.as_ptr()
    }

    pub fn runtime(&self) -> &'rt Runtime {
        self.rt
    }

    /// The engine's type tag: one of the `ffi::SPY_*` constants.
    pub fn kind(&self) -> ffi::SPYType {
        unsafe { ffi::spy_type(self.as_ptr()) }
    }

    pub fn is_none(&self) -> bool {
        self.kind() == ffi::SPY_NONE
    }

    /// Converts to a Rust value.
    pub fn extract<T: FromPy<'rt>>(&self) -> Result<T> {
        T::from_py(self)
    }

    /// Python truth, as `bool(value)`.
    pub fn truth(&self) -> bool {
        unsafe { ffi::spy_truth(self.as_ptr()) != 0 }
    }

    pub fn getattr(&self, name: &str) -> Result<Value<'rt>> {
        let name = c_name(name)?;
        self.rt.wrap(unsafe { ffi::spy_get_attr(self.rt.ctx(), self.as_ptr(), name.as_ptr()) })
    }

    pub fn setattr(&self, name: &str, value: impl IntoPy) -> Result<()> {
        let value = value.into_py(self.rt)?;
        let name = c_name(name)?;
        self.rt.check(unsafe { ffi::spy_set_attr(self.rt.ctx(), self.as_ptr(), name.as_ptr(), value.as_ptr()) })
    }

    /// `value[key]`
    pub fn get_item(&self, key: impl IntoPy) -> Result<Value<'rt>> {
        let key = key.into_py(self.rt)?;
        self.rt.wrap(unsafe { ffi::spy_get_item(self.rt.ctx(), self.as_ptr(), key.as_ptr()) })
    }

    /// `value[key] = item`
    pub fn set_item(&self, key: impl IntoPy, item: impl IntoPy) -> Result<()> {
        let key = key.into_py(self.rt)?;
        let item = item.into_py(self.rt)?;
        self.rt.check(unsafe { ffi::spy_set_item(self.rt.ctx(), self.as_ptr(), key.as_ptr(), item.as_ptr()) })
    }

    /// Calls the value with positional arguments: `()`, a tuple, or a `Vec`.
    pub fn call<T: FromPy<'rt>>(&self, args: impl IntoArgs) -> Result<T> {
        let args = args.into_args(self.rt)?;
        let argv: Vec<_> = args.iter().map(Value::as_ptr).collect();
        let result = unsafe { ffi::spy_call(self.rt.ctx(), self.as_ptr(), argv.len(), argv.as_ptr()) };
        T::from_py(&self.rt.wrap(result)?)
    }

    /// Calls the value with positional arguments and keyword arguments,
    /// which convert to a `dict` with `str` keys.
    pub fn call_with_keywords<T: FromPy<'rt>>(&self, args: impl IntoArgs, keywords: impl IntoPy) -> Result<T> {
        let args = args.into_args(self.rt)?;
        let keywords = keywords.into_py(self.rt)?;
        let argv: Vec<_> = args.iter().map(Value::as_ptr).collect();
        let result = unsafe {
            ffi::spy_call_keywords(self.rt.ctx(), self.as_ptr(), argv.len(), argv.as_ptr(), keywords.as_ptr())
        };
        T::from_py(&self.rt.wrap(result)?)
    }

    /// Iterates the value, as a `for` loop does.
    pub fn iter(&self) -> Result<Iter<'rt>> {
        let iterator = self.rt.wrap(unsafe { ffi::spy_iter(self.rt.ctx(), self.as_ptr()) })?;
        Ok(Iter { iterator })
    }

    /// `repr(value)`
    pub fn repr(&self) -> Result<String> {
        self.rt.wrap(unsafe { ffi::spy_repr(self.rt.ctx(), self.as_ptr()) })?.extract()
    }

    /// `str(value)`
    pub fn str(&self) -> Result<String> {
        self.rt.wrap(unsafe { ffi::spy_str(self.rt.ctx(), self.as_ptr()) })?.extract()
    }
}

impl Clone for Value<'_> {
    fn clone(&self) -> Self {
        unsafe { ffi::spy_retain(self.as_ptr()) };
        Value { rt: self.rt, ptr: self.ptr }
    }
}

impl Drop for Value<'_> {
    fn drop(&mut self) {
        unsafe { ffi::spy_release(self.as_ptr()) }
    }
}

impl fmt::Debug for Value<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self.repr() {
            Ok(text) => f.write_str(&text),
            Err(error) => write!(f, "<unrepresentable: {error}>"),
        }
    }
}

impl fmt::Display for Value<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self.str() {
            Ok(text) => f.write_str(&text),
            Err(error) => write!(f, "<unprintable: {error}>"),
        }
    }
}

/// An engine iterator, yielding values until it is exhausted or raises.
pub struct Iter<'rt> {
    iterator: Value<'rt>,
}

impl<'rt> Iterator for Iter<'rt> {
    type Item = Result<Value<'rt>>;

    fn next(&mut self) -> Option<Self::Item> {
        let rt = self.iterator.rt;
        let item = unsafe { ffi::spy_next(rt.ctx(), self.iterator.as_ptr()) };
        if item.is_null() && unsafe { *ffi::spy_error_type(rt.ctx()) } == 0 {
            return None;
        }
        Some(rt.wrap(item))
    }
}

/// The arguments of a call to a host function.
pub struct Args<'rt> {
    positional: Vec<Value<'rt>>,
    keywords: Option<Value<'rt>>,
}

impl<'rt> Args<'rt> {
    pub(crate) unsafe fn new(
        rt: &'rt Runtime,
        argc: usize,
        argv: *const *mut ffi::SPYValue,
        keywords: *mut ffi::SPYValue,
    ) -> Args<'rt> {
        let retain = |v: *mut ffi::SPYValue| Value::from_raw(rt, NonNull::new_unchecked(ffi::spy_retain(v)));
        let positional = match argc {
            0 => Vec::new(),
            _ => std::slice::from_raw_parts(argv, argc).iter().map(|&v| retain(v)).collect(),
        };
        let keywords = (!keywords.is_null()).then(|| retain(keywords)).filter(Value::truth);
        Args { positional, keywords }
    }

    /// The positional arguments.
    pub fn positional(&self) -> &[Value<'rt>] {
        &self.positional
    }

    /// The keyword arguments as a `dict`, or `None` when there are none.
    pub fn keywords(&self) -> Option<&Value<'rt>> {
        self.keywords.as_ref()
    }

    /// The keyword argument `name`, if it was passed.
    pub fn keyword(&self, name: &str) -> Result<Option<Value<'rt>>> {
        let Some(keywords) = &self.keywords else { return Ok(None) };
        match keywords.get_item(name) {
            Ok(value) => Ok(Some(value)),
            Err(error) if error.type_name == "KeyError" => Ok(None),
            Err(error) => Err(error),
        }
    }

    /// Converts the positional arguments: a tuple of [`FromPy`] types checks
    /// their count, a `Vec` takes them all.
    pub fn extract<T: FromArgs<'rt>>(&self) -> Result<T> {
        T::from_args(&self.positional)
    }
}
