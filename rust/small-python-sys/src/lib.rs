//! Raw bindings to Small Python's C API: `spy.h` and the standard layer of
//! `spy-std.h`. The comments in `spy.h` are the reference for ownership and
//! error rules; in short, every returned `*mut SPYValue` is owned and NULL
//! means an error is set on the context.

#![no_std]
#![allow(non_camel_case_types)]

use core::ffi::{c_char, c_int, c_void};

/// The engine version from `spy.h`.
pub const SPY_VERSION: &str = env!("SPY_VERSION");

#[repr(C)]
pub struct SPYContext {
    _private: [u8; 0],
}

#[repr(C)]
pub struct SPYValue {
    _private: [u8; 0],
}

/// `SPYType`, as an integer so that a value the bindings do not know is
/// never an invalid enum.
pub type SPYType = c_int;
pub const SPY_NONE: SPYType = 0;
pub const SPY_BOOL: SPYType = 1;
pub const SPY_INT: SPYType = 2;
pub const SPY_FLOAT: SPYType = 3;
pub const SPY_STRING: SPYType = 4;
pub const SPY_LIST: SPYType = 5;
pub const SPY_TUPLE: SPYType = 6;
pub const SPY_DICT: SPYType = 7;
pub const SPY_FUNCTION: SPYType = 8;
pub const SPY_NATIVE: SPYType = 9;
pub const SPY_MODULE: SPYType = 10;
pub const SPY_RANGE: SPYType = 11;
pub const SPY_BOUND_METHOD: SPYType = 12;
pub const SPY_ITERATOR: SPYType = 13;
pub const SPY_CLASS: SPYType = 14;
pub const SPY_INSTANCE: SPYType = 15;
pub const SPY_METHOD: SPYType = 16;
pub const SPY_SET: SPYType = 17;
pub const SPY_GENERATOR: SPYType = 18;
pub const SPY_CODE: SPYType = 19;
pub const SPY_SLICE: SPYType = 20;
pub const SPY_STATICMETHOD: SPYType = 21;
pub const SPY_CLASSMETHOD: SPYType = 22;
pub const SPY_PROPERTY: SPYType = 23;
pub const SPY_NOT_IMPLEMENTED: SPYType = 24;
pub const SPY_ELLIPSIS: SPYType = 25;
pub const SPY_COMPLEX: SPYType = 26;
pub const SPY_BYTES: SPYType = 27;
pub const SPY_COROUTINE: SPYType = 28;
pub const SPY_COROUTINE_ITERATOR: SPYType = 29;
pub const SPY_ASYNC_GENERATOR: SPYType = 30;
pub const SPY_ASYNC_GENERATOR_ASEND: SPYType = 31;
pub const SPY_ASYNC_GENERATOR_ATHROW: SPYType = 32;
pub const SPY_ANEXT_AWAITABLE: SPYType = 33;
pub const SPY_SUPER: SPYType = 34;
pub const SPY_FROZENSET: SPYType = 35;
pub const SPY_BYTEARRAY: SPYType = 36;
pub const SPY_DICT_KEYS: SPYType = 37;
pub const SPY_DICT_VALUES: SPYType = 38;
pub const SPY_DICT_ITEMS: SPYType = 39;
pub const SPY_TEMPLATE: SPYType = 40;
pub const SPY_INTERPOLATION: SPYType = 41;
pub const SPY_TEMPLATE_ITERATOR: SPYType = 42;
pub const SPY_MAPPINGPROXY: SPYType = 43;
pub const SPY_FROZENDICT: SPYType = 44;
pub const SPY_LAZY_IMPORT: SPYType = 45;
pub const SPY_FRAME: SPYType = 46;
pub const SPY_FRAME_LOCALS: SPYType = 47;
pub const SPY_MEMORYVIEW: SPYType = 48;
pub const SPY_SENTINEL: SPYType = 49;
pub const SPY_CELL: SPYType = 50;
pub const SPY_TRACEBACK: SPYType = 51;
pub const SPY_MEMBER_DESCRIPTOR: SPYType = 52;
pub const SPY_GETSET_DESCRIPTOR: SPYType = 53;

pub const SPY_MOUNT_READ_ONLY: c_int = 1;

pub type SPYNative = unsafe extern "C" fn(*mut SPYContext, usize, *const *mut SPYValue, *mut c_void) -> *mut SPYValue;
pub type SPYNativeKeywords =
    unsafe extern "C" fn(*mut SPYContext, usize, *const *mut SPYValue, *mut SPYValue, *mut c_void) -> *mut SPYValue;
pub type SPYWrite = unsafe extern "C" fn(*mut c_void, *const c_char, usize) -> c_int;
pub type SPYFlush = unsafe extern "C" fn(*mut c_void) -> c_int;
pub type SPYModuleLoader = unsafe extern "C" fn(*mut c_void, *const c_char) -> *mut c_char;
pub type SPYReadLine = unsafe extern "C" fn(*mut c_void) -> *mut c_char;
pub type SPYModuleInit = unsafe extern "C" fn(*mut SPYContext, *mut SPYValue) -> c_int;

extern "C" {
    pub fn spy_context_new() -> *mut SPYContext;
    pub fn spy_context_free(c: *mut SPYContext);
    pub fn spy_set_opaque(c: *mut SPYContext, opaque: *mut c_void);
    pub fn spy_get_opaque(c: *const SPYContext) -> *mut c_void;
    pub fn spy_set_output(c: *mut SPYContext, write: Option<SPYWrite>, data: *mut c_void);
    pub fn spy_set_flush(c: *mut SPYContext, flush: Option<SPYFlush>);
    pub fn spy_set_module_loader(c: *mut SPYContext, loader: Option<SPYModuleLoader>, data: *mut c_void);
    pub fn spy_set_input(c: *mut SPYContext, read: Option<SPYReadLine>, data: *mut c_void);
    pub fn spy_new_module(c: *mut SPYContext, name: *const c_char, init: SPYModuleInit) -> c_int;
    pub fn spy_init_primitives(c: *mut SPYContext, module: *mut SPYValue) -> c_int;
    pub fn spy_exec_module(
        c: *mut SPYContext,
        module: *mut SPYValue,
        source: *const c_char,
        filename: *const c_char,
    ) -> c_int;
    pub fn spy_mount(c: *mut SPYContext, directory: *const c_char, path: *const c_char, flags: c_int) -> c_int;
    pub fn spy_set_step_limit(c: *mut SPYContext, limit: usize);
    pub fn spy_set_optimize(c: *mut SPYContext, level: c_int);
    pub fn spy_collect(c: *mut SPYContext) -> usize;
    pub fn spy_live_values(c: *const SPYContext) -> usize;

    pub fn spy_eval(c: *mut SPYContext, source: *const c_char, filename: *const c_char) -> *mut SPYValue;
    pub fn spy_eval_interactive(c: *mut SPYContext, source: *const c_char, filename: *const c_char) -> *mut SPYValue;
    pub fn spy_exec(c: *mut SPYContext, source: *const c_char, filename: *const c_char) -> c_int;
    pub fn spy_get_global(c: *mut SPYContext, name: *const c_char) -> *mut SPYValue;
    pub fn spy_set_global(c: *mut SPYContext, name: *const c_char, value: *mut SPYValue) -> c_int;
    pub fn spy_define(c: *mut SPYContext, name: *const c_char, call: SPYNative, data: *mut c_void) -> c_int;
    pub fn spy_call(c: *mut SPYContext, f: *mut SPYValue, argc: usize, argv: *const *mut SPYValue) -> *mut SPYValue;
    pub fn spy_call_keywords(
        c: *mut SPYContext,
        f: *mut SPYValue,
        argc: usize,
        argv: *const *mut SPYValue,
        keywords: *mut SPYValue,
    ) -> *mut SPYValue;
    pub fn spy_native(
        c: *mut SPYContext,
        name: *const c_char,
        call: SPYNativeKeywords,
        data: *mut c_void,
        release: Option<unsafe extern "C" fn(*mut c_void)>,
    ) -> *mut SPYValue;

    pub fn spy_retain(v: *mut SPYValue) -> *mut SPYValue;
    pub fn spy_release(v: *mut SPYValue);
    pub fn spy_type(v: *const SPYValue) -> SPYType;
    pub fn spy_none(c: *mut SPYContext) -> *mut SPYValue;
    pub fn spy_bool(c: *mut SPYContext, b: c_int) -> *mut SPYValue;
    pub fn spy_int(c: *mut SPYContext, n: i64) -> *mut SPYValue;
    pub fn spy_float(c: *mut SPYContext, x: f64) -> *mut SPYValue;
    pub fn spy_string(c: *mut SPYContext, s: *const c_char, n: usize) -> *mut SPYValue;
    pub fn spy_bytes(c: *mut SPYContext, data: *const c_void, n: usize) -> *mut SPYValue;
    pub fn spy_list(c: *mut SPYContext) -> *mut SPYValue;
    pub fn spy_list_append(c: *mut SPYContext, list: *mut SPYValue, item: *mut SPYValue) -> c_int;
    pub fn spy_tuple(c: *mut SPYContext, n: usize, items: *const *mut SPYValue) -> *mut SPYValue;
    pub fn spy_dict(c: *mut SPYContext) -> *mut SPYValue;
    pub fn spy_get_item(c: *mut SPYContext, v: *mut SPYValue, key: *mut SPYValue) -> *mut SPYValue;
    pub fn spy_set_item(c: *mut SPYContext, v: *mut SPYValue, key: *mut SPYValue, item: *mut SPYValue) -> c_int;
    pub fn spy_get_attr(c: *mut SPYContext, v: *mut SPYValue, name: *const c_char) -> *mut SPYValue;
    pub fn spy_set_attr(c: *mut SPYContext, v: *mut SPYValue, name: *const c_char, item: *mut SPYValue) -> c_int;
    pub fn spy_iter(c: *mut SPYContext, v: *mut SPYValue) -> *mut SPYValue;
    pub fn spy_next(c: *mut SPYContext, iterator: *mut SPYValue) -> *mut SPYValue;
    pub fn spy_as_int(c: *mut SPYContext, v: *mut SPYValue, out: *mut i64) -> c_int;
    pub fn spy_as_float(c: *mut SPYContext, v: *mut SPYValue, out: *mut f64) -> c_int;
    pub fn spy_as_string(c: *mut SPYContext, v: *mut SPYValue, n: *mut usize) -> *const c_char;
    pub fn spy_as_bytes(c: *mut SPYContext, v: *mut SPYValue, n: *mut usize) -> *const u8;
    pub fn spy_truth(v: *mut SPYValue) -> c_int;
    pub fn spy_repr(c: *mut SPYContext, v: *mut SPYValue) -> *mut SPYValue;
    pub fn spy_str(c: *mut SPYContext, v: *mut SPYValue) -> *mut SPYValue;

    pub fn spy_error_type(c: *const SPYContext) -> *const c_char;
    pub fn spy_error_message(c: *const SPYContext) -> *const c_char;
    pub fn spy_error_display(c: *mut SPYContext) -> *const c_char;
    pub fn spy_error_filename(c: *const SPYContext) -> *const c_char;
    pub fn spy_error_line(c: *const SPYContext) -> usize;
    pub fn spy_clear_error(c: *mut SPYContext);
    pub fn spy_error(c: *mut SPYContext, type_: *const c_char, message: *const c_char) -> *mut SPYValue;
    pub fn spy_error_value(c: *mut SPYContext) -> *mut SPYValue;
    pub fn spy_raise(c: *mut SPYContext, exception: *mut SPYValue) -> *mut SPYValue;

    pub fn spy_std_init_module(c: *mut SPYContext, name: *const c_char) -> c_int;
    pub fn spy_std_init(c: *mut SPYContext) -> c_int;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn evaluates() {
        unsafe {
            let c = spy_context_new();
            assert!(!c.is_null());
            let v = spy_eval(c, c"6 * 7".as_ptr(), c"<test>".as_ptr());
            let mut n = 0;
            assert_eq!(spy_as_int(c, v, &mut n), 0);
            assert_eq!(n, 42);
            spy_release(v);
            spy_context_free(c);
        }
    }
}
