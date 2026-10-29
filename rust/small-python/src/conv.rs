//! Conversions between Rust and engine values.

use std::collections::{BTreeMap, HashMap};
use std::hash::{BuildHasher, Hash};

use crate::{ffi, Error, Result, Runtime, Value};

/// A Rust value that converts into an engine value.
pub trait IntoPy {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>>;
}

/// A Rust value that converts from an engine value.
pub trait FromPy<'rt>: Sized {
    fn from_py(value: &Value<'rt>) -> Result<Self>;
}

/// Positional arguments for a call: `()`, a tuple, or a `Vec`.
pub trait IntoArgs {
    fn into_args(self, rt: &Runtime) -> Result<Vec<Value<'_>>>;
}

/// Positional arguments of a host function: `()`, a tuple, or a `Vec`.
pub trait FromArgs<'rt>: Sized {
    fn from_args(args: &[Value<'rt>]) -> Result<Self>;
}

impl IntoPy for Value<'_> {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        (&self).into_py(rt)
    }
}

impl IntoPy for &Value<'_> {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        if self.runtime().ctx() != rt.ctx() {
            return Err(Error::new("ValueError", "the value belongs to another runtime"));
        }
        rt.wrap(unsafe { ffi::spy_retain(self.as_ptr()) })
    }
}

impl<'rt> FromPy<'rt> for Value<'rt> {
    fn from_py(value: &Value<'rt>) -> Result<Self> {
        Ok(value.clone())
    }
}

impl IntoPy for () {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        rt.wrap(unsafe { ffi::spy_none(rt.ctx()) })
    }
}

impl FromPy<'_> for () {
    fn from_py(value: &Value<'_>) -> Result<Self> {
        if value.is_none() {
            Ok(())
        } else {
            Err(Error::type_error("expected None"))
        }
    }
}

impl IntoPy for bool {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        rt.wrap(unsafe { ffi::spy_bool(rt.ctx(), self.into()) })
    }
}

impl FromPy<'_> for bool {
    fn from_py(value: &Value<'_>) -> Result<Self> {
        if value.kind() == ffi::SPY_BOOL {
            Ok(value.truth())
        } else {
            Err(Error::type_error("expected bool"))
        }
    }
}

fn overflow() -> Error {
    Error::new("OverflowError", "int out of range for the Rust type")
}

macro_rules! integer {
    ($($t:ty),*) => {$(
        impl IntoPy for $t {
            fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
                let n = i64::try_from(self).map_err(|_| overflow())?;
                rt.wrap(unsafe { ffi::spy_int(rt.ctx(), n) })
            }
        }

        impl FromPy<'_> for $t {
            fn from_py(value: &Value<'_>) -> Result<Self> {
                let rt = value.runtime();
                let mut n = 0;
                rt.check(unsafe { ffi::spy_as_int(rt.ctx(), value.as_ptr(), &mut n) })?;
                <$t>::try_from(n).map_err(|_| overflow())
            }
        }
    )*};
}

integer!(i8, i16, i32, i64, i128, isize, u8, u16, u32, u64, u128, usize);

macro_rules! float {
    ($($t:ty),*) => {$(
        impl IntoPy for $t {
            fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
                rt.wrap(unsafe { ffi::spy_float(rt.ctx(), self.into()) })
            }
        }

        impl FromPy<'_> for $t {
            fn from_py(value: &Value<'_>) -> Result<Self> {
                let rt = value.runtime();
                let mut x = 0.0;
                rt.check(unsafe { ffi::spy_as_float(rt.ctx(), value.as_ptr(), &mut x) })?;
                Ok(x as $t)
            }
        }
    )*};
}

float!(f32, f64);

impl IntoPy for &str {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        rt.wrap(unsafe { ffi::spy_string(rt.ctx(), self.as_ptr().cast(), self.len()) })
    }
}

impl IntoPy for String {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        self.as_str().into_py(rt)
    }
}

impl IntoPy for &String {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        self.as_str().into_py(rt)
    }
}

impl IntoPy for char {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        self.encode_utf8(&mut [0; 4]).into_py(rt)
    }
}

impl FromPy<'_> for String {
    fn from_py(value: &Value<'_>) -> Result<Self> {
        let rt = value.runtime();
        let mut n = 0;
        let data = unsafe { ffi::spy_as_string(rt.ctx(), value.as_ptr(), &mut n) };
        if data.is_null() {
            return Err(unsafe { Error::take(rt.ctx()) });
        }
        let bytes = unsafe { std::slice::from_raw_parts(data.cast::<u8>(), n) };
        // The engine keeps lone surrogates, which Rust strings cannot hold.
        String::from_utf8(bytes.to_vec())
            .map_err(|_| Error::new("UnicodeEncodeError", "'utf-8' codec can't encode surrogates"))
    }
}

impl<T: IntoPy> IntoPy for Option<T> {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        match self {
            Some(value) => value.into_py(rt),
            None => ().into_py(rt),
        }
    }
}

impl<'rt, T: FromPy<'rt>> FromPy<'rt> for Option<T> {
    fn from_py(value: &Value<'rt>) -> Result<Self> {
        if value.is_none() {
            Ok(None)
        } else {
            T::from_py(value).map(Some)
        }
    }
}

/// A list of converted items.
fn list<T: IntoPy>(rt: &Runtime, items: impl IntoIterator<Item = T>) -> Result<Value<'_>> {
    let list = rt.wrap(unsafe { ffi::spy_list(rt.ctx()) })?;
    for item in items {
        let item = item.into_py(rt)?;
        rt.check(unsafe { ffi::spy_list_append(rt.ctx(), list.as_ptr(), item.as_ptr()) })?;
    }
    Ok(list)
}

/// A dict of converted pairs.
fn dict<K: IntoPy, V: IntoPy>(rt: &Runtime, pairs: impl IntoIterator<Item = (K, V)>) -> Result<Value<'_>> {
    let dict = rt.wrap(unsafe { ffi::spy_dict(rt.ctx()) })?;
    for (key, value) in pairs {
        dict.set_item(key, value)?;
    }
    Ok(dict)
}

/// The converted pairs of a mapping, by iterating its keys.
fn pairs<'rt, K: FromPy<'rt>, V: FromPy<'rt>, C: FromIterator<(K, V)>>(value: &Value<'rt>) -> Result<C> {
    value
        .iter()?
        .map(|key| {
            let key = key?;
            Ok((key.extract()?, value.get_item(&key)?.extract()?))
        })
        .collect()
}

impl<T: IntoPy> IntoPy for Vec<T> {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        list(rt, self)
    }
}

impl<T: IntoPy + Clone> IntoPy for &[T] {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        list(rt, self.iter().cloned())
    }
}

impl<'rt, T: FromPy<'rt>> FromPy<'rt> for Vec<T> {
    fn from_py(value: &Value<'rt>) -> Result<Self> {
        value.iter()?.map(|item| item?.extract()).collect()
    }
}

impl<K: IntoPy, V: IntoPy, S> IntoPy for HashMap<K, V, S> {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        dict(rt, self)
    }
}

impl<'rt, K: FromPy<'rt> + Eq + Hash, V: FromPy<'rt>, S: BuildHasher + Default> FromPy<'rt> for HashMap<K, V, S> {
    fn from_py(value: &Value<'rt>) -> Result<Self> {
        pairs(value)
    }
}

impl<K: IntoPy, V: IntoPy> IntoPy for BTreeMap<K, V> {
    fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
        dict(rt, self)
    }
}

impl<'rt, K: FromPy<'rt> + Ord, V: FromPy<'rt>> FromPy<'rt> for BTreeMap<K, V> {
    fn from_py(value: &Value<'rt>) -> Result<Self> {
        pairs(value)
    }
}

fn arity(expected: usize, got: usize) -> Error {
    let s = if expected == 1 { "" } else { "s" };
    Error::type_error(format!("expected {expected} argument{s}, got {got}"))
}

impl IntoArgs for () {
    fn into_args(self, _: &Runtime) -> Result<Vec<Value<'_>>> {
        Ok(Vec::new())
    }
}

impl FromArgs<'_> for () {
    fn from_args(args: &[Value<'_>]) -> Result<Self> {
        if args.is_empty() {
            Ok(())
        } else {
            Err(arity(0, args.len()))
        }
    }
}

impl<T: IntoPy> IntoArgs for Vec<T> {
    fn into_args(self, rt: &Runtime) -> Result<Vec<Value<'_>>> {
        self.into_iter().map(|item| item.into_py(rt)).collect()
    }
}

impl<'rt, T: FromPy<'rt>> FromArgs<'rt> for Vec<T> {
    fn from_args(args: &[Value<'rt>]) -> Result<Self> {
        args.iter().map(Value::extract).collect()
    }
}

macro_rules! tuple {
    ($n:literal: $($t:ident $v:ident),+) => {
        impl<$($t: IntoPy),+> IntoPy for ($($t,)+) {
            fn into_py(self, rt: &Runtime) -> Result<Value<'_>> {
                let items = self.into_args(rt)?;
                let argv: Vec<_> = items.iter().map(Value::as_ptr).collect();
                rt.wrap(unsafe { ffi::spy_tuple(rt.ctx(), argv.len(), argv.as_ptr()) })
            }
        }

        impl<'rt, $($t: FromPy<'rt>),+> FromPy<'rt> for ($($t,)+) {
            fn from_py(value: &Value<'rt>) -> Result<Self> {
                let items = value.iter()?.collect::<Result<Vec<_>>>()?;
                if items.len() != $n {
                    return Err(Error::new("ValueError", format!("expected {} items, got {}", $n, items.len())));
                }
                Self::from_args(&items)
            }
        }

        impl<$($t: IntoPy),+> IntoArgs for ($($t,)+) {
            fn into_args(self, rt: &Runtime) -> Result<Vec<Value<'_>>> {
                let ($($v,)+) = self;
                Ok(vec![$($v.into_py(rt)?),+])
            }
        }

        impl<'rt, $($t: FromPy<'rt>),+> FromArgs<'rt> for ($($t,)+) {
            fn from_args(args: &[Value<'rt>]) -> Result<Self> {
                let [$($v),+] = args else { return Err(arity($n, args.len())) };
                Ok(($($v.extract()?,)+))
            }
        }
    };
}

tuple!(1: A a);
tuple!(2: A a, B b);
tuple!(3: A a, B b, C c);
tuple!(4: A a, B b, C c, D d);
tuple!(5: A a, B b, C c, D d, E e);
tuple!(6: A a, B b, C c, D d, E e, F f);
tuple!(7: A a, B b, C c, D d, E e, F f, G g);
tuple!(8: A a, B b, C c, D d, E e, F f, G g, H h);
