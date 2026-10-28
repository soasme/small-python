// Values and messages of the worker protocol (docs/packaging/protocol.md).
// Encoding trusts the embedder's values; decoding trusts nothing and throws
// Violation for any message that breaks the protocol.

export const MAX_DEPTH = 200;

export const INIT = 0x01, EVAL = 0x02, EXEC = 0x03, CALL = 0x04, GET = 0x05, SET = 0x06, DELETE = 0x07,
  MODULE = 0x08, MOUNT = 0x09, COLLECT = 0x0a, OP = 0x0b, RELEASE = 0x0c;
export const HOST = 0x21, LOAD = 0x22, OUTPUT = 0x23;
export const RESULT = 0x40, RAISE = 0x41;

export class Violation extends Error {}

/** A complex number, as the engine's complex. */
export class Complex {
  constructor(real, imag) {
    this.real = real;
    this.imag = imag;
    Object.freeze(this);
  }
}

const I64_MIN = -(1n << 63n), I64_MAX = (1n << 63n) - 1n;

class Writer {
  constructor() {
    this.bytes = new Uint8Array(256);
    this.view = new DataView(this.bytes.buffer);
    this.length = 0;
  }
  reserve(n) {
    if (this.length + n <= this.bytes.length) return;
    let size = this.bytes.length * 2;
    while (size < this.length + n) size *= 2;
    const grown = new Uint8Array(size);
    grown.set(this.bytes.subarray(0, this.length));
    this.bytes = grown;
    this.view = new DataView(grown.buffer);
  }
  byte(b) { this.reserve(1); this.bytes[this.length++] = b; }
  u32(n) { this.reserve(4); this.view.setUint32(this.length, n, true); this.length += 4; }
  u64(n) { this.reserve(8); this.view.setBigUint64(this.length, BigInt(n), true); this.length += 8; }
  i64(n) { this.reserve(8); this.view.setBigInt64(this.length, n, true); this.length += 8; }
  f64(d) { this.reserve(8); this.view.setFloat64(this.length, d, true); this.length += 8; }
  raw(bytes) { this.reserve(bytes.length); this.bytes.set(bytes, this.length); this.length += bytes.length; }
  text(tag, bytes) { this.byte(tag); this.u32(bytes.length); this.raw(bytes); }
}

/**
 * A framed message. reference(value) returns {handle} or {fn, name} for a
 * value that is not plain data, or throws TypeError.
 */
export function message(kind, fields, reference) {
  const w = new Writer();
  w.u32(0);
  w.byte(kind);
  for (const field of fields) encode(w, field, reference, 0);
  w.view.setUint32(0, w.length - 4, true);
  return w.bytes.subarray(0, w.length);
}

/** A field that must be sent as a Python tuple rather than a list. */
export class Tuple {
  constructor(items) { this.items = items; }
}

function encode(w, value, reference, depth) {
  if (depth > MAX_DEPTH) throw new TypeError("value is too deeply nested to convert");
  if (value === null || value === undefined) w.byte(0x4e);
  else if (typeof value === "boolean") w.byte(value ? 0x54 : 0x46);
  else if (typeof value === "number") {
    if (Number.isInteger(value) && !Object.is(value, -0)) integer(w, BigInt(value));
    else { w.byte(0x66); w.f64(value); }
  } else if (typeof value === "bigint") integer(w, value);
  else if (typeof value === "string") w.text(0x73, encodeString(value));
  else if (value instanceof Uint8Array) w.text(0x62, value);
  else if (value instanceof Complex) { w.byte(0x63); w.f64(value.real); w.f64(value.imag); }
  else if (Array.isArray(value) || value instanceof Tuple || value instanceof Set) {
    const items = value instanceof Tuple ? value.items : [...value];
    w.byte(value instanceof Tuple ? 0x74 : value instanceof Set ? 0x53 : 0x6c);
    w.u32(items.length);
    for (const item of items) encode(w, item, reference, depth + 1);
  } else if (value instanceof Map || isPlainObject(value)) {
    const entries = value instanceof Map ? [...value] : Object.entries(value);
    w.byte(0x64);
    w.u32(entries.length);
    for (const [key, item] of entries) {
      encode(w, key, reference, depth + 1);
      encode(w, item, reference, depth + 1);
    }
  } else {
    const ref = reference(value);
    if (ref.handle !== undefined) { w.byte(0x68); w.u64(ref.handle); }
    else { w.byte(0x70); w.u64(ref.fn); w.text(0x73, encodeString(ref.name)); }
  }
}

function isPlainObject(value) {
  if (typeof value !== "object") return false;
  const proto = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
}

function integer(w, n) {
  if (n >= I64_MIN && n <= I64_MAX) { w.byte(0x69); w.i64(n); return; }
  const text = n < 0n ? "-0x" + (-n).toString(16) : "0x" + n.toString(16);
  w.text(0x49, new TextEncoder().encode(text));
}

// Strings are UTF-8 with lone surrogates as three-byte sequences.
const utf8 = new TextEncoder(), strict = new TextDecoder("utf-8", { fatal: true }), latin1 = new TextDecoder("latin1");

export function encodeString(s) {
  if (s.isWellFormed()) return utf8.encode(s);
  const out = [];
  for (let i = 0; i < s.length; i++) {
    let c = s.charCodeAt(i);
    if (c >= 0xd800 && c < 0xdc00 && i + 1 < s.length) {
      const d = s.charCodeAt(i + 1);
      if (d >= 0xdc00 && d < 0xe000) { c = 0x10000 + ((c - 0xd800) << 10) + (d - 0xdc00); i++; }
    }
    if (c < 0x80) out.push(c);
    else if (c < 0x800) out.push(0xc0 | c >> 6, 0x80 | c & 63);
    else if (c < 0x10000) out.push(0xe0 | c >> 12, 0x80 | c >> 6 & 63, 0x80 | c & 63);
    else out.push(0xf0 | c >> 18, 0x80 | c >> 12 & 63, 0x80 | c >> 6 & 63, 0x80 | c & 63);
  }
  return new Uint8Array(out);
}

function decodeString(bytes) {
  try {
    return strict.decode(bytes);
  } catch {
    // Not plain UTF-8: lone surrogates, or a violation.
  }
  let s = "";
  for (let i = 0; i < bytes.length;) {
    const c = bytes[i];
    const n = c < 0x80 ? 1 : c >= 0xc2 && c < 0xe0 ? 2 : c >= 0xe0 && c < 0xf0 ? 3 : c >= 0xf0 && c < 0xf5 ? 4 : 0;
    if (!n || i + n > bytes.length) throw new Violation("invalid UTF-8");
    let code = n === 1 ? c : c & (0xff >> (n + 1));
    for (let k = 1; k < n; k++) {
      if ((bytes[i + k] & 0xc0) !== 0x80) throw new Violation("invalid UTF-8");
      code = code << 6 | bytes[i + k] & 63;
    }
    if ((n === 3 && code < 0x800) || (n === 4 && (code < 0x10000 || code > 0x10ffff)))
      throw new Violation("invalid UTF-8");
    s += String.fromCodePoint(code);
    i += n;
  }
  return s;
}

/**
 * Decodes one message's values; obtain(id) turns a handle id into the
 * embedder's object for it.
 */
export class Reader {
  constructor(bytes, obtain) {
    this.bytes = bytes;
    this.view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    this.at = 1;
    this.obtain = obtain;
  }
  get kind() { return this.bytes[0]; }
  take(n) {
    if (n > this.bytes.length - this.at) throw new Violation("truncated message");
    const at = this.at;
    this.at += n;
    return at;
  }
  count(minimum) {
    const n = this.view.getUint32(this.take(4), true);
    if (n * minimum > this.bytes.length - this.at) throw new Violation("count exceeds the message");
    return n;
  }
  value(depth = 0) {
    if (depth > MAX_DEPTH) throw new Violation("value nested too deeply");
    const tag = this.bytes[this.take(1)];
    switch (tag) {
      case 0x4e: return null;
      case 0x46: case 0x54: return tag === 0x54;
      case 0x69: {
        const n = this.view.getBigInt64(this.take(8), true);
        return n >= BigInt(Number.MIN_SAFE_INTEGER) && n <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(n) : n;
      }
      case 0x49: return this.big();
      case 0x66: return this.view.getFloat64(this.take(8), true);
      case 0x63: {
        const at = this.take(16);
        return new Complex(this.view.getFloat64(at, true), this.view.getFloat64(at + 8, true));
      }
      case 0x73: {
        const n = this.count(1), at = this.take(n);
        return decodeString(this.bytes.subarray(at, at + n));
      }
      case 0x62: case 0x42: {
        const n = this.count(1), at = this.take(n);
        return this.bytes.slice(at, at + n);
      }
      case 0x6c: case 0x74: case 0x53: case 0x7a: {
        const n = this.count(1), items = [];
        for (let i = 0; i < n; i++) items.push(this.value(depth + 1));
        return tag === 0x6c || tag === 0x74 ? items : new Set(items);
      }
      case 0x64: {
        const n = this.count(2), map = new Map();
        for (let i = 0; i < n; i++) {
          const key = this.value(depth + 1);
          map.set(key, this.value(depth + 1));
        }
        return map;
      }
      case 0x68: return this.obtain(this.view.getBigUint64(this.take(8), true));
      default: throw new Violation(`unknown value tag 0x${tag.toString(16)}`);
    }
  }
  big() {
    const n = this.count(1), at = this.take(n);
    const text = latin1.decode(this.bytes.subarray(at, at + n));
    const digits = text.startsWith("-0x") ? text.slice(3) : text.startsWith("0x") ? text.slice(2) : "";
    if (!/^[1-9a-f][0-9a-f]*$/.test(digits)) throw new Violation("invalid integer");
    const value = text[0] === "-" ? -BigInt("0x" + digits) : BigInt("0x" + digits);
    if (value >= I64_MIN && value <= I64_MAX) throw new Violation("integer should have been sent as 'i'");
    return value;
  }
  finish() {
    if (this.at !== this.bytes.length) throw new Violation("trailing bytes in message");
  }
}
