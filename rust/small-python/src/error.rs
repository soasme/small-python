use std::ffi::CStr;
use std::fmt;

use crate::ffi;

/// An exception: one raised by engine code, or one Rust raises into it.
///
/// Errors cross between Rust and the engine by type name and message. An
/// engine exception that escapes into Rust is copied into an `Error` and
/// cleared; returning it from a host function raises a new exception of the
/// same type name with the same message.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Error {
    /// The class name, qualified by its module unless it is a builtin.
    pub type_name: String,
    /// The text CPython's traceback shows after the type.
    pub message: String,
    /// Where it was raised, when it came from the engine.
    pub filename: Option<String>,
    pub line: Option<usize>,
}

pub type Result<T, E = Error> = std::result::Result<T, E>;

impl Error {
    pub fn new(type_name: impl Into<String>, message: impl Into<String>) -> Error {
        Error { type_name: type_name.into(), message: message.into(), filename: None, line: None }
    }

    pub(crate) fn type_error(message: impl Into<String>) -> Error {
        Error::new("TypeError", message)
    }

    /// Takes the context's pending error, leaving none.
    pub(crate) unsafe fn take(c: *mut ffi::SPYContext) -> Error {
        let text = |s: *const std::ffi::c_char| CStr::from_ptr(s).to_string_lossy().into_owned();
        let type_name = text(ffi::spy_error_type(c));
        let message = text(ffi::spy_error_display(c));
        let filename = text(ffi::spy_error_filename(c));
        let line = ffi::spy_error_line(c);
        ffi::spy_clear_error(c);
        Error {
            type_name: if type_name.is_empty() { "SystemError".into() } else { type_name },
            message,
            filename: (!filename.is_empty()).then_some(filename),
            line: (line != 0).then_some(line),
        }
    }

    /// Sets this as the context's pending error; returns NULL for the caller.
    pub(crate) unsafe fn raise(&self, c: *mut ffi::SPYContext) -> *mut ffi::SPYValue {
        let type_name = crate::cstring(&self.type_name);
        let message = crate::cstring(&self.message);
        ffi::spy_error(c, type_name.as_ptr(), message.as_ptr())
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.message.is_empty() {
            f.write_str(&self.type_name)
        } else {
            write!(f, "{}: {}", self.type_name, self.message)
        }
    }
}

impl std::error::Error for Error {}
