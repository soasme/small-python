//! The module `json` for Small Python, on serde_json: `loads`, `load`,
//! `dumps` and `dump`, as Python's json module has them, with the keyword
//! arguments `indent`, `ensure_ascii` and `allow_nan`. Built as the static library
//! libjson.a, it calls the engine through spy.h's functions, which the
//! program links from libspy.a; `spyc app.py libjson.a` registers it.

use serde::{Deserialize, Serialize};
use serde_json::ser::Formatter;
use serde_json::{Map, Number, Value};
use std::ffi::{c_char, c_int, c_void, CStr, CString};
use std::{io, ptr, slice};

#[repr(C)]
pub struct SPYContext {
    _private: [u8; 0],
}
#[repr(C)]
pub struct SPYValue {
    _private: [u8; 0],
}
type Context = *mut SPYContext;
type Object = *mut SPYValue;
type Native = unsafe extern "C" fn(Context, usize, *const Object, Object, *mut c_void) -> Object;

// The SPYType values (spy.h) this module tells apart.
const SPY_NONE: c_int = 0;
const SPY_BOOL: c_int = 1;
const SPY_INT: c_int = 2;
const SPY_FLOAT: c_int = 3;
const SPY_STRING: c_int = 4;
const SPY_LIST: c_int = 5;
const SPY_TUPLE: c_int = 6;
const SPY_DICT: c_int = 7;
const SPY_BYTES: c_int = 27;

extern "C" {
    fn spy_none(c: Context) -> Object;
    fn spy_bool(c: Context, b: c_int) -> Object;
    fn spy_int(c: Context, n: i64) -> Object;
    fn spy_float(c: Context, x: f64) -> Object;
    fn spy_string(c: Context, s: *const c_char, n: usize) -> Object;
    fn spy_list(c: Context) -> Object;
    fn spy_dict(c: Context) -> Object;
    fn spy_list_append(c: Context, list: Object, item: Object) -> c_int;
    fn spy_get_item(c: Context, v: Object, key: Object) -> Object;
    fn spy_set_item(c: Context, v: Object, key: Object, item: Object) -> c_int;
    fn spy_get_attr(c: Context, v: Object, name: *const c_char) -> Object;
    fn spy_set_attr(c: Context, v: Object, name: *const c_char, item: Object) -> c_int;
    fn spy_iter(c: Context, v: Object) -> Object;
    fn spy_next(c: Context, iterator: Object) -> Object;
    fn spy_type(v: *const SPYValue) -> c_int;
    fn spy_as_int(c: Context, v: Object, out: *mut i64) -> c_int;
    fn spy_as_float(c: Context, v: Object, out: *mut f64) -> c_int;
    fn spy_as_string(c: Context, v: Object, n: *mut usize) -> *const c_char;
    fn spy_as_bytes(c: Context, v: Object, n: *mut usize) -> *const u8;
    fn spy_truth(c: Context, v: Object) -> c_int;
    fn spy_str(c: Context, v: Object) -> Object;
    fn spy_repr(c: Context, v: Object) -> Object;
    fn spy_call(c: Context, f: Object, argc: usize, argv: *const Object) -> Object;
    fn spy_native(c: Context, name: *const c_char, call: Native, data: *mut c_void,
                  release: Option<unsafe extern "C" fn(*mut c_void)>) -> Object;
    fn spy_release(v: Object);
    fn spy_error(c: Context, kind: *const c_char, message: *const c_char) -> Object;
    fn spy_error_type(c: *const SPYContext) -> *const c_char;
    fn spy_clear_error(c: Context);
}

/// The engine's error is set; the caller returns NULL or -1.
struct Raised;
type Result<T> = std::result::Result<T, Raised>;

fn raise<T>(c: Context, kind: &CStr, message: &str) -> Result<T> {
    let message = CString::new(message.replace('\0', "\\0")).unwrap_or_default();
    unsafe { spy_error(c, kind.as_ptr(), message.as_ptr()) };
    Err(Raised)
}

/// An owned reference, released when dropped.
struct Owned(Object);
impl Owned {
    fn new(v: Object) -> Result<Owned> {
        if v.is_null() { Err(Raised) } else { Ok(Owned(v)) }
    }
    fn take(self) -> Object {
        let v = self.0;
        std::mem::forget(self);
        v
    }
}
impl Drop for Owned {
    fn drop(&mut self) {
        unsafe { spy_release(self.0) }
    }
}

/// The bytes of a str (UTF-8) or of a bytes, borrowed from v.
unsafe fn text<'a>(c: Context, v: Object) -> Result<&'a [u8]> {
    let mut n = 0;
    let data: *const u8 = if spy_type(v) == SPY_BYTES { spy_as_bytes(c, v, &mut n) } else { spy_as_string(c, v, &mut n).cast() };
    if data.is_null() { Err(Raised) } else { Ok(slice::from_raw_parts(data, n)) }
}
unsafe fn string(c: Context, s: &str) -> Result<Owned> {
    Owned::new(spy_string(c, s.as_ptr().cast(), s.len()))
}
/// str(v) or repr(v), as Rust text.
unsafe fn spelling(c: Context, v: Object, repr: bool) -> Result<String> {
    let s = Owned::new(if repr { spy_repr(c, v) } else { spy_str(c, v) })?;
    Ok(String::from_utf8_lossy(text(c, s.0)?).into_owned())
}
unsafe fn type_name(c: Context, v: Object) -> Result<String> {
    let class = Owned::new(spy_get_attr(c, v, c"__class__".as_ptr()))?;
    let name = Owned::new(spy_get_attr(c, class.0, c"__name__".as_ptr()))?;
    Ok(String::from_utf8_lossy(text(c, name.0)?).into_owned())
}

// == loads ==

unsafe fn to_python(c: Context, value: &Value) -> Result<Owned> {
    match value {
        Value::Null => Owned::new(spy_none(c)),
        Value::Bool(b) => Owned::new(spy_bool(c, *b as c_int)),
        Value::Number(n) => number(c, n),
        Value::String(s) => string(c, s),
        Value::Array(items) => {
            let list = Owned::new(spy_list(c))?;
            for item in items {
                if spy_list_append(c, list.0, to_python(c, item)?.0) != 0 { return Err(Raised); }
            }
            Ok(list)
        }
        Value::Object(map) => {
            let dict = Owned::new(spy_dict(c))?;
            for (key, item) in map {
                if spy_set_item(c, dict.0, string(c, key)?.0, to_python(c, item)?.0) != 0 { return Err(Raised); }
            }
            Ok(dict)
        }
    }
}
/// A number keeps its text: an integer of any size becomes an int, as
/// int(text) makes it, and anything with a fraction or exponent a float.
unsafe fn number(c: Context, n: &Number) -> Result<Owned> {
    if let Some(i) = n.as_i64() { return Owned::new(spy_int(c, i)); }
    let spelled = n.as_str();
    if spelled.contains(['.', 'e', 'E']) { return Owned::new(spy_float(c, spelled.parse().unwrap_or(f64::NAN))); }
    let zero = Owned::new(spy_int(c, 0))?;
    let int = Owned::new(spy_get_attr(c, zero.0, c"__class__".as_ptr()))?;
    let digits = string(c, spelled)?;
    Owned::new(spy_call(c, int.0, 1, &digits.0))
}
unsafe fn parse(c: Context, source: Object) -> Result<Owned> {
    let Ok(data) = text(c, source) else {
        spy_clear_error(c);
        return raise(c, c"TypeError", &format!("the JSON object must be str or bytes, not {}", type_name(c, source)?));
    };
    // Converting is recursive, so the nesting is bounded before parsing.
    let (mut depth, mut deepest, mut quoted, mut escaped) = (0usize, 0, false, false);
    for &byte in data {
        match byte {
            _ if escaped => escaped = false,
            b'\\' if quoted => escaped = true,
            b'"' => quoted = !quoted,
            b'[' | b'{' if !quoted => { depth += 1; deepest = deepest.max(depth) }
            b']' | b'}' if !quoted => depth = depth.saturating_sub(1),
            _ => {}
        }
    }
    if deepest > DEPTH { return raise(c, c"RecursionError", "maximum recursion depth exceeded while decoding a JSON document"); }
    let mut deserializer = serde_json::Deserializer::from_slice(data);
    deserializer.disable_recursion_limit();
    let value = Value::deserialize(&mut deserializer).and_then(|value| deserializer.end().map(|()| value));
    match value {
        Ok(value) => to_python(c, &value),
        Err(error) => raise(c, c"ValueError", &error.to_string()),
    }
}
/// How deeply arrays and objects may nest, in either direction: a bound
/// on the C stack the recursive conversions use, as Python's default
/// recursion limit is.
const DEPTH: usize = 1000;

// == dumps ==

/// How dumps writes: Python's separators, an indent string or none, and
/// non-ASCII text escaped or as it is.
struct Python {
    indent: Option<Vec<u8>>,
    ascii: bool,
    level: usize,
    has_value: bool,
}
impl Python {
    fn separate<W: ?Sized + io::Write>(&self, w: &mut W, first: bool) -> io::Result<()> {
        if !first { w.write_all(if self.indent.is_some() { b"," } else { b", " })?; }
        self.newline(w)
    }
    fn newline<W: ?Sized + io::Write>(&self, w: &mut W) -> io::Result<()> {
        if let Some(indent) = &self.indent {
            w.write_all(b"\n")?;
            for _ in 0..self.level { w.write_all(indent)?; }
        }
        Ok(())
    }
    fn open<W: ?Sized + io::Write>(&mut self, w: &mut W, bracket: &[u8]) -> io::Result<()> {
        self.level += 1;
        self.has_value = false;
        w.write_all(bracket)
    }
    fn close<W: ?Sized + io::Write>(&mut self, w: &mut W, bracket: &[u8]) -> io::Result<()> {
        self.level -= 1;
        if self.has_value { self.newline(w)?; }
        w.write_all(bracket)
    }
}
impl Formatter for Python {
    fn begin_array<W: ?Sized + io::Write>(&mut self, w: &mut W) -> io::Result<()> { self.open(w, b"[") }
    fn end_array<W: ?Sized + io::Write>(&mut self, w: &mut W) -> io::Result<()> { self.close(w, b"]") }
    fn begin_array_value<W: ?Sized + io::Write>(&mut self, w: &mut W, first: bool) -> io::Result<()> { self.separate(w, first) }
    fn end_array_value<W: ?Sized + io::Write>(&mut self, _: &mut W) -> io::Result<()> { self.has_value = true; Ok(()) }
    fn begin_object<W: ?Sized + io::Write>(&mut self, w: &mut W) -> io::Result<()> { self.open(w, b"{") }
    fn end_object<W: ?Sized + io::Write>(&mut self, w: &mut W) -> io::Result<()> { self.close(w, b"}") }
    fn begin_object_key<W: ?Sized + io::Write>(&mut self, w: &mut W, first: bool) -> io::Result<()> { self.separate(w, first) }
    fn begin_object_value<W: ?Sized + io::Write>(&mut self, w: &mut W) -> io::Result<()> { w.write_all(b": ") }
    fn end_object_value<W: ?Sized + io::Write>(&mut self, _: &mut W) -> io::Result<()> { self.has_value = true; Ok(()) }
    fn write_string_fragment<W: ?Sized + io::Write>(&mut self, w: &mut W, fragment: &str) -> io::Result<()> {
        if !self.ascii { return w.write_all(fragment.as_bytes()); }
        for ch in fragment.chars() {
            if (ch as u32) < 0x7f { w.write_all(&[ch as u8])?; continue; }
            for unit in ch.encode_utf16(&mut [0; 2]) { write!(w, "\\u{unit:04x}")?; }
        }
        Ok(())
    }
}

/// What dumps converts with: whether NaN and the infinities are written,
/// and the containers on the way to the current value, to find a cycle.
struct Encoder {
    allow_nan: bool,
    path: Vec<Object>,
}

/// The JSON value of a Python object.
unsafe fn from_python(c: Context, v: Object, encoder: &mut Encoder) -> Result<Value> {
    Ok(match spy_type(v) {
        SPY_NONE => Value::Null,
        SPY_BOOL => Value::Bool(spy_truth(c, v) > 0),
        SPY_INT | SPY_FLOAT => Value::Number(Number::from_string_unchecked(numeral(c, v, encoder.allow_nan)?)),
        SPY_STRING => Value::String(unicode(c, v)?),
        kind @ (SPY_LIST | SPY_TUPLE | SPY_DICT) => {
            if encoder.path.contains(&v) { return raise(c, c"ValueError", "Circular reference detected"); }
            if encoder.path.len() == DEPTH {
                return raise(c, c"RecursionError", "maximum recursion depth exceeded while encoding a JSON object");
            }
            encoder.path.push(v);
            let iterator = Owned::new(spy_iter(c, v))?;
            let mut items = Vec::new();
            let mut map = Map::new();
            loop {
                let next = spy_next(c, iterator.0);
                if next.is_null() { break; }
                let item = Owned(next);
                if kind != SPY_DICT { items.push(from_python(c, item.0, encoder)?); continue; }
                let value = Owned::new(spy_get_item(c, v, item.0))?;
                map.insert(key(c, item.0, encoder.allow_nan)?, from_python(c, value.0, encoder)?);
            }
            // spy_next sets an error when the iteration failed.
            if !CStr::from_ptr(spy_error_type(c)).is_empty() { return Err(Raised); }
            encoder.path.pop();
            if kind == SPY_DICT { Value::Object(map) } else { Value::Array(items) }
        }
        _ => return raise(c, c"TypeError", &format!("Object of type {} is not JSON serializable", type_name(c, v)?)),
    })
}
/// The text a number is written as: str(int), repr(float), or NaN,
/// Infinity and -Infinity where they are allowed.
unsafe fn numeral(c: Context, v: Object, allow_nan: bool) -> Result<String> {
    let mut x = 0.0;
    if spy_type(v) == SPY_FLOAT && spy_as_float(c, v, &mut x) == 0 && !x.is_finite() {
        if !allow_nan {
            return raise(c, c"ValueError", &format!("Out of range float values are not JSON compliant: {}", spelling(c, v, true)?));
        }
        return Ok(if x.is_nan() { "NaN" } else if x > 0.0 { "Infinity" } else { "-Infinity" }.to_owned());
    }
    spelling(c, v, spy_type(v) == SPY_FLOAT)
}
unsafe fn unicode(c: Context, v: Object) -> Result<String> {
    match std::str::from_utf8(text(c, v)?) {
        Ok(s) => Ok(s.to_owned()),
        Err(_) => raise(c, c"ValueError", "surrogates not allowed"),
    }
}
/// A key as Python's json writes it: a str, or the JSON text of a number,
/// bool or None.
unsafe fn key(c: Context, k: Object, allow_nan: bool) -> Result<String> {
    match spy_type(k) {
        SPY_STRING => unicode(c, k),
        SPY_INT | SPY_FLOAT => numeral(c, k, allow_nan),
        SPY_BOOL => Ok(if spy_truth(c, k) > 0 { "true" } else { "false" }.to_owned()),
        SPY_NONE => Ok("null".to_owned()),
        _ => raise(c, c"TypeError", &format!("keys must be str, int, float, bool or None, not {}", type_name(c, k)?)),
    }
}
/// dumps' keyword arguments: indent (None, a number of spaces, or a str),
/// ensure_ascii and allow_nan.
unsafe fn options(c: Context, name: &str, keywords: Object) -> Result<(Python, Encoder)> {
    let mut python = Python { indent: None, ascii: true, level: 0, has_value: false };
    let mut encoder = Encoder { allow_nan: true, path: Vec::new() };
    if keywords.is_null() { return Ok((python, encoder)); }
    let iterator = Owned::new(spy_iter(c, keywords))?;
    loop {
        let next = spy_next(c, iterator.0);
        if next.is_null() { break; }
        let k = Owned(next);
        let v = Owned::new(spy_get_item(c, keywords, k.0))?;
        match text(c, k.0)? {
            b"indent" => {
                python.indent = match spy_type(v.0) {
                    SPY_NONE => None,
                    SPY_STRING => Some(text(c, v.0)?.to_vec()),
                    _ => {
                        let mut n = 0;
                        if spy_as_int(c, v.0, &mut n) != 0 { return Err(Raised); }
                        Some(b" ".repeat(n.clamp(0, 1 << 16) as usize))
                    }
                }
            }
            b"ensure_ascii" => python.ascii = truth(c, v.0)?,
            b"allow_nan" => encoder.allow_nan = truth(c, v.0)?,
            other => {
                let other = String::from_utf8_lossy(other);
                return raise(c, c"TypeError", &format!("{name}() got an unexpected keyword argument '{other}'"));
            }
        }
    }
    Ok((python, encoder))
}
unsafe fn truth(c: Context, v: Object) -> Result<bool> {
    match spy_truth(c, v) {
        -1 => Err(Raised),
        truth => Ok(truth == 1),
    }
}
unsafe fn serialize(c: Context, v: Object, name: &str, keywords: Object) -> Result<Owned> {
    let (formatter, mut encoder) = options(c, name, keywords)?;
    let value = from_python(c, v, &mut encoder)?;
    let mut out = Vec::new();
    let mut serializer = serde_json::Serializer::with_formatter(&mut out, formatter);
    if let Err(error) = value.serialize(&mut serializer) {
        return raise(c, c"ValueError", &error.to_string());
    }
    Owned::new(spy_string(c, out.as_ptr().cast(), out.len()))
}

// == The module ==

unsafe fn arguments<'a>(c: Context, name: &str, argc: usize, argv: *const Object, wanted: usize) -> Result<&'a [Object]> {
    if argc != wanted {
        let s = if wanted == 1 { "" } else { "s" };
        return raise(c, c"TypeError", &format!("{name}() takes {wanted} positional argument{s} but {argc} were given"));
    }
    Ok(slice::from_raw_parts(argv, argc))
}
/// A call passes keywords as a dict, which may be empty, or as NULL.
unsafe fn no_keywords(c: Context, name: &str, keywords: Object) -> Result<()> {
    if keywords.is_null() { return Ok(()); }
    let iterator = Owned::new(spy_iter(c, keywords))?;
    let next = spy_next(c, iterator.0);
    if next.is_null() { return Ok(()); }
    spy_release(next);
    raise(c, c"TypeError", &format!("{name}() takes no keyword arguments"))
}
fn result(r: Result<Owned>) -> Object {
    r.map_or(ptr::null_mut(), Owned::take)
}
/// A method of an object, called with the given arguments.
unsafe fn call_method(c: Context, v: Object, name: &CStr, args: &[Object]) -> Result<Owned> {
    let method = Owned::new(spy_get_attr(c, v, name.as_ptr()))?;
    Owned::new(spy_call(c, method.0, args.len(), args.as_ptr()))
}

unsafe extern "C" fn loads(c: Context, argc: usize, argv: *const Object, keywords: Object, _: *mut c_void) -> Object {
    result((|| {
        let args = arguments(c, "loads", argc, argv, 1)?;
        no_keywords(c, "loads", keywords)?;
        parse(c, args[0])
    })())
}
unsafe extern "C" fn load(c: Context, argc: usize, argv: *const Object, keywords: Object, _: *mut c_void) -> Object {
    result((|| {
        let args = arguments(c, "load", argc, argv, 1)?;
        no_keywords(c, "load", keywords)?;
        parse(c, call_method(c, args[0], c"read", &[])?.0)
    })())
}
unsafe extern "C" fn dumps(c: Context, argc: usize, argv: *const Object, keywords: Object, _: *mut c_void) -> Object {
    result((|| serialize(c, arguments(c, "dumps", argc, argv, 1)?[0], "dumps", keywords))())
}
unsafe extern "C" fn dump(c: Context, argc: usize, argv: *const Object, keywords: Object, _: *mut c_void) -> Object {
    result((|| {
        let args = arguments(c, "dump", argc, argv, 2)?;
        let text = serialize(c, args[0], "dump", keywords)?;
        call_method(c, args[1], c"write", &[text.0])?;
        Owned::new(spy_none(c))
    })())
}

/// The module's init, which spyc's generated main registers as json.
#[no_mangle]
pub unsafe extern "C" fn spy_init_json(c: Context, module: Object) -> c_int {
    let functions: [(&CStr, Native); 4] = [(c"loads", loads), (c"load", load), (c"dumps", dumps), (c"dump", dump)];
    for (name, call) in functions {
        let Ok(function) = Owned::new(spy_native(c, name.as_ptr(), call, ptr::null_mut(), None)) else { return -1 };
        if spy_set_attr(c, module, name.as_ptr(), function.0) != 0 { return -1; }
    }
    0
}
