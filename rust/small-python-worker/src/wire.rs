//! Values and messages of the worker protocol (docs/packaging/protocol.md).
//!
//! Encoding trusts the parent's values; decoding trusts nothing and returns
//! a violation for any message that breaks the protocol.

use std::sync::Arc;

use crate::{Error, Object, Shared, Value};

pub const MAX_DEPTH: usize = 200;

pub const INIT: u8 = 0x01;
pub const EVAL: u8 = 0x02;
pub const EXEC: u8 = 0x03;
pub const CALL: u8 = 0x04;
pub const GET: u8 = 0x05;
pub const SET: u8 = 0x06;
pub const DELETE: u8 = 0x07;
pub const MODULE: u8 = 0x08;
pub const MOUNT: u8 = 0x09;
pub const COLLECT: u8 = 0x0a;
pub const OP: u8 = 0x0b;
pub const RELEASE: u8 = 0x0c;
pub const HOST: u8 = 0x21;
pub const LOAD: u8 = 0x22;
pub const OUTPUT: u8 = 0x23;
pub const RESULT: u8 = 0x40;
pub const RAISE: u8 = 0x41;

/// A framed message of `kind` with `fields`, whose objects and functions
/// must belong to the runtime of `shared`.
pub fn message(kind: u8, fields: &[&Value], shared: &Arc<Shared>) -> Result<Vec<u8>, Error> {
    let mut out = vec![0, 0, 0, 0, kind];
    for field in fields {
        encode(&mut out, field, shared, 0)?;
    }
    let n = u32::try_from(out.len() - 4).map_err(|_| Error::Invalid("message exceeds the limit".into()))?;
    out[..4].copy_from_slice(&n.to_le_bytes());
    Ok(out)
}

fn encode(out: &mut Vec<u8>, value: &Value, shared: &Arc<Shared>, depth: usize) -> Result<(), Error> {
    if depth > MAX_DEPTH {
        return Err(Error::Invalid("value is too deeply nested to convert".into()));
    }
    let own = |owner: &Arc<Shared>| {
        if Arc::ptr_eq(owner, shared) {
            Ok(())
        } else {
            Err(Error::Invalid("the value belongs to another runtime".into()))
        }
    };
    match value {
        Value::None => out.push(b'N'),
        Value::Bool(b) => out.push(if *b { b'T' } else { b'F' }),
        Value::Int(n) => {
            out.push(b'i');
            out.extend(n.to_le_bytes());
        }
        Value::BigInt(text) => text_field(out, b'I', text.as_bytes())?,
        Value::Float(x) => {
            out.push(b'f');
            out.extend(x.to_le_bytes());
        }
        Value::Complex(re, im) => {
            out.push(b'c');
            out.extend(re.to_le_bytes());
            out.extend(im.to_le_bytes());
        }
        Value::Str(s) => text_field(out, b's', s.as_bytes())?,
        Value::Bytes(b) => text_field(out, b'b', b)?,
        Value::ByteArray(b) => text_field(out, b'B', b)?,
        Value::List(items) | Value::Tuple(items) | Value::Set(items) | Value::FrozenSet(items) => {
            let tag = match value {
                Value::List(_) => b'l',
                Value::Tuple(_) => b't',
                Value::Set(_) => b'S',
                _ => b'z',
            };
            out.push(tag);
            out.extend(count(items.len())?.to_le_bytes());
            for item in items {
                encode(out, item, shared, depth + 1)?;
            }
        }
        Value::Dict(pairs) => {
            out.push(b'd');
            out.extend(count(pairs.len())?.to_le_bytes());
            for (key, item) in pairs {
                encode(out, key, shared, depth + 1)?;
                encode(out, item, shared, depth + 1)?;
            }
        }
        Value::Object(object) => {
            own(&object.0.shared)?;
            out.push(b'h');
            out.extend(object.0.id.to_le_bytes());
        }
        Value::Function(function) => {
            own(&function.shared)?;
            out.push(b'p');
            out.extend(function.id.to_le_bytes());
            text_field(out, b's', function.name.as_bytes())?;
        }
    }
    Ok(())
}

fn count(n: usize) -> Result<u32, Error> {
    u32::try_from(n).map_err(|_| Error::Invalid("message exceeds the limit".into()))
}

fn text_field(out: &mut Vec<u8>, tag: u8, data: &[u8]) -> Result<(), Error> {
    out.push(tag);
    out.extend(count(data.len())?.to_le_bytes());
    out.extend_from_slice(data);
    Ok(())
}

/// Decodes the values of one message (without its length), after the kind.
pub struct Reader<'a> {
    data: &'a [u8],
    at: usize,
    shared: &'a Arc<Shared>,
}

/// What the worker broke.
pub type Violation = String;

impl<'a> Reader<'a> {
    pub fn new(data: &'a [u8], shared: &'a Arc<Shared>) -> Reader<'a> {
        Reader { data, at: 1, shared }
    }

    /// Decodes exactly `N` values, which must use up the message.
    pub fn values<const N: usize>(mut self) -> Result<[Value; N], Violation> {
        let mut values = std::array::from_fn(|_| Value::None);
        for value in &mut values {
            *value = self.value(0)?;
        }
        if self.at != self.data.len() {
            return Err("trailing bytes in message".into());
        }
        Ok(values)
    }

    fn take(&mut self, n: usize) -> Result<&'a [u8], Violation> {
        if n > self.data.len() - self.at {
            return Err("truncated message".into());
        }
        self.at += n;
        Ok(&self.data[self.at - n..self.at])
    }

    fn take_array<const N: usize>(&mut self) -> Result<[u8; N], Violation> {
        Ok(self.take(N)?.try_into().expect("N bytes"))
    }

    fn count(&mut self, minimum: usize) -> Result<usize, Violation> {
        let n = u32::from_le_bytes(self.take_array()?) as usize;
        if n.saturating_mul(minimum) > self.data.len() - self.at {
            return Err("count exceeds the message".into());
        }
        Ok(n)
    }

    fn value(&mut self, depth: usize) -> Result<Value, Violation> {
        if depth > MAX_DEPTH {
            return Err("value nested too deeply".into());
        }
        let tag = self.take(1)?[0];
        Ok(match tag {
            b'N' => Value::None,
            b'F' | b'T' => Value::Bool(tag == b'T'),
            b'i' => Value::Int(i64::from_le_bytes(self.take_array()?)),
            b'I' => self.big()?,
            b'f' => Value::Float(f64::from_le_bytes(self.take_array()?)),
            b'c' => {
                let re = f64::from_le_bytes(self.take_array()?);
                Value::Complex(re, f64::from_le_bytes(self.take_array()?))
            }
            b's' => {
                let n = self.count(1)?;
                Value::Str(surrogatepass(self.take(n)?)?)
            }
            b'b' | b'B' => {
                let n = self.count(1)?;
                let bytes = self.take(n)?.to_vec();
                if tag == b'b' {
                    Value::Bytes(bytes)
                } else {
                    Value::ByteArray(bytes)
                }
            }
            b'l' | b't' | b'S' | b'z' => {
                let n = self.count(1)?;
                let items = (0..n).map(|_| self.value(depth + 1)).collect::<Result<_, _>>()?;
                match tag {
                    b'l' => Value::List(items),
                    b't' => Value::Tuple(items),
                    b'S' => Value::Set(items),
                    _ => Value::FrozenSet(items),
                }
            }
            b'd' => {
                let n = self.count(2)?;
                let pairs = (0..n)
                    .map(|_| Ok((self.value(depth + 1)?, self.value(depth + 1)?)))
                    .collect::<Result<_, Violation>>()?;
                Value::Dict(pairs)
            }
            b'h' => Value::Object(Object::new(u64::from_le_bytes(self.take_array()?), self.shared)),
            _ => return Err(format!("unknown value tag {tag:#x}")),
        })
    }

    fn big(&mut self) -> Result<Value, Violation> {
        let n = self.count(1)?;
        let text = std::str::from_utf8(self.take(n)?).map_err(|_| "invalid integer")?;
        let digits = text.strip_prefix("-0x").or_else(|| text.strip_prefix("0x")).unwrap_or_default();
        if digits.is_empty()
            || digits.starts_with('0')
            || !digits.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
        {
            return Err("invalid integer".into());
        }
        // Up to 16 digits fit in i64 unless they are -0x8000000000000000 or beyond.
        let fits = digits.len() < 16
            || (digits.len() == 16
                && (digits.as_bytes()[0] < b'8' || (text.starts_with('-') && digits == "8000000000000000")));
        if fits {
            return Err("integer should have been sent as 'i'".into());
        }
        Ok(Value::BigInt(text.to_owned()))
    }
}

/// UTF-8 in which lone surrogates are allowed as their three-byte forms
/// (CPython's surrogatepass). A Rust string cannot hold them, so each
/// becomes U+FFFD.
fn surrogatepass(mut bytes: &[u8]) -> Result<String, Violation> {
    let mut text = String::with_capacity(bytes.len());
    loop {
        match std::str::from_utf8(bytes) {
            Ok(rest) => {
                text.push_str(rest);
                return Ok(text);
            }
            Err(error) => {
                let (valid, rest) = bytes.split_at(error.valid_up_to());
                text.push_str(std::str::from_utf8(valid).expect("valid prefix"));
                match rest {
                    [0xed, 0xa0..=0xbf, 0x80..=0xbf, ..] => text.push('\u{fffd}'),
                    _ => return Err("invalid UTF-8".into()),
                }
                bytes = &rest[3..];
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn surrogates_pass_and_overlong_forms_do_not() {
        assert_eq!(surrogatepass(b"a\xed\xb2\x80b").unwrap(), "a\u{fffd}b");
        assert!(surrogatepass(b"\xc0\x80").is_err());
        assert!(surrogatepass(b"\xed\xa0").is_err());
    }

    #[test]
    fn big_integers_are_canonical() {
        let shared = Arc::new(Shared::default());
        let decode = |text: &str| {
            let mut data = vec![RESULT, b'I'];
            data.extend((text.len() as u32).to_le_bytes());
            data.extend(text.as_bytes());
            Reader::new(&data, &shared).values::<1>().map(|[v]| v)
        };
        assert_eq!(decode("0x8000000000000000").unwrap(), Value::BigInt("0x8000000000000000".into()));
        assert_eq!(decode("-0x8000000000000001").unwrap(), Value::BigInt("-0x8000000000000001".into()));
        for bad in ["0x7fffffffffffffff", "-0x8000000000000000", "0x0", "-0x0", "0x01", "0xABC", "12", "0x"] {
            assert!(decode(bad).is_err(), "{bad}");
        }
    }
}
