//! Serde support (feature `serde`), with serde_json's data model: structs
//! and maps are dicts, sequences are lists, unit is `None`, and an enum
//! variant with data is a one-entry dict naming the variant.

use serde::de::{self, DeserializeOwned, IntoDeserializer, Visitor};
use serde::ser::{self, Serialize};

use crate::{ffi, Error, IntoPy, Result, Runtime, Value};

impl ser::Error for Error {
    fn custom<T: std::fmt::Display>(msg: T) -> Self {
        Error::new("ValueError", msg.to_string())
    }
}

impl de::Error for Error {
    fn custom<T: std::fmt::Display>(msg: T) -> Self {
        Error::new("ValueError", msg.to_string())
    }
}

impl Runtime {
    /// Serializes a Rust value into an engine value.
    pub fn to_value<T: Serialize + ?Sized>(&self, value: &T) -> Result<Value<'_>> {
        value.serialize(Serializer { rt: self })
    }

    /// Deserializes a Rust value from an engine value.
    pub fn from_value<T: DeserializeOwned>(&self, value: &Value<'_>) -> Result<T> {
        T::deserialize(value)
    }
}

#[derive(Clone, Copy)]
struct Serializer<'rt> {
    rt: &'rt Runtime,
}

impl<'rt> Serializer<'rt> {
    fn list(self) -> Result<Value<'rt>> {
        self.rt.wrap(unsafe { ffi::spy_list(self.rt.ctx()) })
    }

    fn dict(self) -> Result<Value<'rt>> {
        self.rt.wrap(unsafe { ffi::spy_dict(self.rt.ctx()) })
    }

    /// `{variant: value}`
    fn variant(self, variant: &str, value: Value<'rt>) -> Result<Value<'rt>> {
        let dict = self.dict()?;
        dict.set_item(variant, value)?;
        Ok(dict)
    }
}

impl<'rt> ser::Serializer for Serializer<'rt> {
    type Ok = Value<'rt>;
    type Error = Error;
    type SerializeSeq = Seq<'rt>;
    type SerializeTuple = Seq<'rt>;
    type SerializeTupleStruct = Seq<'rt>;
    type SerializeTupleVariant = Seq<'rt>;
    type SerializeMap = Map<'rt>;
    type SerializeStruct = Map<'rt>;
    type SerializeStructVariant = Map<'rt>;

    fn serialize_bool(self, v: bool) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_i8(self, v: i8) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_i16(self, v: i16) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_i32(self, v: i32) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_i64(self, v: i64) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_u8(self, v: u8) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_u16(self, v: u16) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_u32(self, v: u32) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_u64(self, v: u64) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_f32(self, v: f32) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_f64(self, v: f64) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_char(self, v: char) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_str(self, v: &str) -> Result<Value<'rt>> {
        v.into_py(self.rt)
    }
    fn serialize_bytes(self, v: &[u8]) -> Result<Value<'rt>> {
        self.rt.wrap(unsafe { ffi::spy_bytes(self.rt.ctx(), v.as_ptr().cast(), v.len()) })
    }
    fn serialize_none(self) -> Result<Value<'rt>> {
        ().into_py(self.rt)
    }
    fn serialize_some<T: Serialize + ?Sized>(self, value: &T) -> Result<Value<'rt>> {
        value.serialize(self)
    }
    fn serialize_unit(self) -> Result<Value<'rt>> {
        ().into_py(self.rt)
    }
    fn serialize_unit_struct(self, _: &'static str) -> Result<Value<'rt>> {
        ().into_py(self.rt)
    }
    fn serialize_unit_variant(self, _: &'static str, _: u32, variant: &'static str) -> Result<Value<'rt>> {
        variant.into_py(self.rt)
    }
    fn serialize_newtype_struct<T: Serialize + ?Sized>(self, _: &'static str, value: &T) -> Result<Value<'rt>> {
        value.serialize(self)
    }
    fn serialize_newtype_variant<T: Serialize + ?Sized>(
        self,
        _: &'static str,
        _: u32,
        variant: &'static str,
        value: &T,
    ) -> Result<Value<'rt>> {
        self.variant(variant, value.serialize(self)?)
    }
    fn serialize_seq(self, _: Option<usize>) -> Result<Seq<'rt>> {
        Ok(Seq { to: self, list: self.list()?, variant: None })
    }
    fn serialize_tuple(self, len: usize) -> Result<Seq<'rt>> {
        self.serialize_seq(Some(len))
    }
    fn serialize_tuple_struct(self, _: &'static str, len: usize) -> Result<Seq<'rt>> {
        self.serialize_seq(Some(len))
    }
    fn serialize_tuple_variant(self, _: &'static str, _: u32, variant: &'static str, _: usize) -> Result<Seq<'rt>> {
        Ok(Seq { to: self, list: self.list()?, variant: Some(variant) })
    }
    fn serialize_map(self, _: Option<usize>) -> Result<Map<'rt>> {
        Ok(Map { to: self, dict: self.dict()?, key: None, variant: None })
    }
    fn serialize_struct(self, _: &'static str, len: usize) -> Result<Map<'rt>> {
        self.serialize_map(Some(len))
    }
    fn serialize_struct_variant(self, _: &'static str, _: u32, variant: &'static str, _: usize) -> Result<Map<'rt>> {
        Ok(Map { to: self, dict: self.dict()?, key: None, variant: Some(variant) })
    }
}

struct Seq<'rt> {
    to: Serializer<'rt>,
    list: Value<'rt>,
    variant: Option<&'static str>,
}

impl<'rt> Seq<'rt> {
    fn push<T: Serialize + ?Sized>(&mut self, value: &T) -> Result<()> {
        let item = value.serialize(self.to)?;
        self.to.rt.check(unsafe { ffi::spy_list_append(self.to.rt.ctx(), self.list.as_ptr(), item.as_ptr()) })
    }

    fn finish(self) -> Result<Value<'rt>> {
        match self.variant {
            Some(variant) => self.to.variant(variant, self.list),
            None => Ok(self.list),
        }
    }
}

macro_rules! seq {
    ($($trait:ident $method:ident),*) => {$(
        impl<'rt> ser::$trait for Seq<'rt> {
            type Ok = Value<'rt>;
            type Error = Error;
            fn $method<T: Serialize + ?Sized>(&mut self, value: &T) -> Result<()> {
                self.push(value)
            }
            fn end(self) -> Result<Value<'rt>> {
                self.finish()
            }
        }
    )*};
}

seq!(SerializeSeq serialize_element, SerializeTuple serialize_element,
     SerializeTupleStruct serialize_field, SerializeTupleVariant serialize_field);

struct Map<'rt> {
    to: Serializer<'rt>,
    dict: Value<'rt>,
    key: Option<Value<'rt>>,
    variant: Option<&'static str>,
}

impl<'rt> Map<'rt> {
    fn finish(self) -> Result<Value<'rt>> {
        match self.variant {
            Some(variant) => self.to.variant(variant, self.dict),
            None => Ok(self.dict),
        }
    }
}

impl<'rt> ser::SerializeMap for Map<'rt> {
    type Ok = Value<'rt>;
    type Error = Error;
    fn serialize_key<T: Serialize + ?Sized>(&mut self, key: &T) -> Result<()> {
        self.key = Some(key.serialize(self.to)?);
        Ok(())
    }
    fn serialize_value<T: Serialize + ?Sized>(&mut self, value: &T) -> Result<()> {
        let key = self.key.take().ok_or_else(|| <Error as ser::Error>::custom("value without a key"))?;
        self.dict.set_item(key, value.serialize(self.to)?)
    }
    fn end(self) -> Result<Value<'rt>> {
        self.finish()
    }
}

macro_rules! fields {
    ($($trait:ident),*) => {$(
        impl<'rt> ser::$trait for Map<'rt> {
            type Ok = Value<'rt>;
            type Error = Error;
            fn serialize_field<T: Serialize + ?Sized>(&mut self, key: &'static str, value: &T) -> Result<()> {
                self.dict.set_item(key, value.serialize(self.to)?)
            }
            fn end(self) -> Result<Value<'rt>> {
                self.finish()
            }
        }
    )*};
}

fields!(SerializeStruct, SerializeStructVariant);

impl<'de, 'rt> de::Deserializer<'de> for &Value<'rt> {
    type Error = Error;

    fn deserialize_any<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value> {
        match self.kind() {
            ffi::SPY_NONE => visitor.visit_unit(),
            ffi::SPY_BOOL => visitor.visit_bool(self.truth()),
            ffi::SPY_INT => visitor.visit_i64(self.extract()?),
            ffi::SPY_FLOAT => visitor.visit_f64(self.extract()?),
            ffi::SPY_STRING => visitor.visit_string(self.extract()?),
            ffi::SPY_BYTES | ffi::SPY_BYTEARRAY => {
                let bytes: Vec<u8> = self.extract()?;
                visitor.visit_byte_buf(bytes)
            }
            ffi::SPY_LIST | ffi::SPY_TUPLE | ffi::SPY_SET | ffi::SPY_FROZENSET => {
                let items = self.iter()?.collect::<Result<Vec<_>>>()?;
                visitor.visit_seq(de::value::SeqDeserializer::new(items.iter()))
            }
            ffi::SPY_DICT | ffi::SPY_FROZENDICT | ffi::SPY_MAPPINGPROXY => {
                let mut pairs = Vec::new();
                for key in self.iter()? {
                    let key = key?;
                    let value = self.get_item(&key)?;
                    pairs.push((key, value));
                }
                visitor.visit_map(de::value::MapDeserializer::new(pairs.iter().map(|(k, v)| (k, v))))
            }
            _ => Err(Error::type_error(format!("cannot deserialize {}", self.repr()?))),
        }
    }

    fn deserialize_option<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value> {
        if self.is_none() {
            visitor.visit_none()
        } else {
            visitor.visit_some(self)
        }
    }

    fn deserialize_newtype_struct<V: Visitor<'de>>(self, _: &'static str, visitor: V) -> Result<V::Value> {
        visitor.visit_newtype_struct(self)
    }

    fn deserialize_enum<V: Visitor<'de>>(
        self,
        _: &'static str,
        _: &'static [&'static str],
        visitor: V,
    ) -> Result<V::Value> {
        if self.kind() == ffi::SPY_STRING {
            let variant: String = self.extract()?;
            return visitor.visit_enum(variant.into_deserializer());
        }
        let mut keys = self.iter()?;
        let (Some(key), None) = (keys.next(), keys.next()) else {
            return Err(Error::type_error("an enum variant with data is a dict with one key"));
        };
        let key = key?;
        let value = self.get_item(&key)?;
        visitor.visit_enum(Enum { variant: key.extract()?, value })
    }

    serde::forward_to_deserialize_any! {
        bool i8 i16 i32 i64 i128 u8 u16 u32 u64 u128 f32 f64 char str string
        bytes byte_buf unit unit_struct seq tuple tuple_struct map struct identifier ignored_any
    }
}

impl<'de, 'a, 'rt> IntoDeserializer<'de, Error> for &'a Value<'rt> {
    type Deserializer = Self;
    fn into_deserializer(self) -> Self {
        self
    }
}

struct Enum<'rt> {
    variant: String,
    value: Value<'rt>,
}

impl<'de, 'rt> de::EnumAccess<'de> for Enum<'rt> {
    type Error = Error;
    type Variant = Value<'rt>;
    fn variant_seed<S: de::DeserializeSeed<'de>>(self, seed: S) -> Result<(S::Value, Value<'rt>)> {
        let variant = seed.deserialize(self.variant.into_deserializer())?;
        Ok((variant, self.value))
    }
}

impl<'de, 'rt> de::VariantAccess<'de> for Value<'rt> {
    type Error = Error;
    fn unit_variant(self) -> Result<()> {
        de::Deserialize::deserialize(&self)
    }
    fn newtype_variant_seed<S: de::DeserializeSeed<'de>>(self, seed: S) -> Result<S::Value> {
        seed.deserialize(&self)
    }
    fn tuple_variant<V: Visitor<'de>>(self, _: usize, visitor: V) -> Result<V::Value> {
        de::Deserializer::deserialize_seq(&self, visitor)
    }
    fn struct_variant<V: Visitor<'de>>(self, _: &'static [&'static str], visitor: V) -> Result<V::Value> {
        de::Deserializer::deserialize_map(&self, visitor)
    }
}
