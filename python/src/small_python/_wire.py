"""Values and messages of the worker protocol (docs/packaging/protocol.md).

Encoding trusts the parent's values; decoding trusts nothing and raises
Violation for any message that breaks the protocol.
"""
import struct

MAX_DEPTH = 200

INIT, EVAL, EXEC, CALL, GET, SET, DELETE, MODULE, MOUNT, COLLECT, OP, RELEASE = range(0x01, 0x0D)
HOST, LOAD, OUTPUT = 0x21, 0x22, 0x23
RESULT, RAISE = 0x40, 0x41

_I64 = struct.Struct("<q")
_U32 = struct.Struct("<I")
_U64 = struct.Struct("<Q")
_F64 = struct.Struct("<d")
_C128 = struct.Struct("<dd")


class Violation(Exception):
    """The worker sent something the protocol does not allow."""


def message(kind, fields, reference):
    """A framed message. reference(value) encodes any value that is not plain
    data as 'h' or 'p', or raises TypeError."""
    out = bytearray(4)
    out.append(kind)
    for field in fields:
        _encode(out, field, reference, 0)
    _U32.pack_into(out, 0, len(out) - 4)
    return out


def _encode(out, value, reference, depth):
    # type() rather than isinstance(), which would ask a proxy for __class__.
    if depth > MAX_DEPTH:
        raise RecursionError("value is too deeply nested to convert")
    cls = type(value)
    if value is None:
        out += b"N"
    elif cls is bool:
        out += b"T" if value else b"F"
    elif issubclass(cls, int):
        value = int(value)
        if -(1 << 63) <= value < 1 << 63:
            out += b"i" + _I64.pack(value)
        else:
            _text(out, b"I", hex(value).encode("ascii"))
    elif issubclass(cls, float):
        out += b"f" + _F64.pack(value)
    elif issubclass(cls, complex):
        out += b"c" + _C128.pack(value.real, value.imag)
    elif issubclass(cls, str):
        _text(out, b"s", str.encode(value, "utf-8", "surrogatepass"))
    elif issubclass(cls, (bytes, bytearray)):
        _text(out, b"B" if issubclass(cls, bytearray) else b"b", value)
    elif issubclass(cls, dict):
        out += b"d" + _U32.pack(len(value))
        for key, item in dict.items(value):
            _encode(out, key, reference, depth + 1)
            _encode(out, item, reference, depth + 1)
    elif issubclass(cls, (list, tuple, set, frozenset)):
        tag = b"l" if issubclass(cls, list) else b"t" if issubclass(cls, tuple) else \
            b"z" if issubclass(cls, frozenset) else b"S"
        out += tag + _U32.pack(len(value))
        for item in value:
            _encode(out, item, reference, depth + 1)
    else:
        out += reference(value)


def _text(out, tag, data):
    out += tag + _U32.pack(len(data))
    out += data


def handle(id):
    return b"h" + _U64.pack(id)


def function(id, name):
    data = name.encode("utf-8", "surrogatepass")
    return b"p" + _U64.pack(id) + b"s" + _U32.pack(len(data)) + data


class Reader:
    """Decodes one message's values. obtain(id) turns a handle id into the
    parent's object for it. A value that decodes but cannot be built (an
    unhashable key) does not stop decoding: the rest is read so every handle
    is obtained, and the first such error is raised by finish()."""

    def __init__(self, data, obtain):
        self.data = memoryview(data)
        self.at = 1
        self.obtain = obtain
        self.error = None

    def take(self, n):
        at = self.at
        if n > len(self.data) - at:
            raise Violation("truncated message")
        self.at = at + n
        return self.data[at:at + n]

    def count(self, minimum):
        n = _U32.unpack(self.take(4))[0]
        if n * minimum > len(self.data) - self.at:
            raise Violation("count exceeds the message")
        return n

    def value(self, depth=0):
        if depth > MAX_DEPTH:
            raise Violation("value nested too deeply")
        tag = self.take(1)[0]
        if tag == 0x4E:  # N
            return None
        if tag == 0x46 or tag == 0x54:  # F T
            return tag == 0x54
        if tag == 0x69:  # i
            return _I64.unpack(self.take(8))[0]
        if tag == 0x49:  # I
            return self._big()
        if tag == 0x66:  # f
            return _F64.unpack(self.take(8))[0]
        if tag == 0x63:  # c
            return complex(*_C128.unpack(self.take(16)))
        if tag == 0x73:  # s
            try:
                return str(self.take(self.count(1)), "utf-8", "surrogatepass")
            except UnicodeDecodeError:
                raise Violation("invalid UTF-8") from None
        if tag == 0x62:  # b
            return bytes(self.take(self.count(1)))
        if tag == 0x42:  # B
            return bytearray(self.take(self.count(1)))
        if tag in b"ltSz":
            items = [self.value(depth + 1) for _ in range(self.count(1))]
            if tag == 0x6C:
                return items
            if tag == 0x74:
                return tuple(items)
            return self._build(set if tag == 0x53 else frozenset, items)
        if tag == 0x64:  # d
            pairs = [(self.value(depth + 1), self.value(depth + 1)) for _ in range(self.count(2))]
            return self._build(dict, pairs)
        if tag == 0x68:  # h
            return self.obtain(_U64.unpack(self.take(8))[0])
        raise Violation(f"unknown value tag {tag:#x}")

    def _big(self):
        try:
            text = str(self.take(self.count(1)), "ascii")
        except UnicodeDecodeError:
            raise Violation("invalid integer") from None
        digits = text[3:] if text.startswith("-0x") else text[2:] if text.startswith("0x") else ""
        if not digits or digits.strip("0123456789abcdef") or digits[0] == "0":
            raise Violation("invalid integer")
        n = int(text, 16)
        if -(1 << 63) <= n < 1 << 63:
            raise Violation("integer should have been sent as 'i'")
        return n

    def _build(self, kind, items):
        try:
            return kind(items)
        except Exception as e:
            if self.error is None:
                self.error = e
            return None

    def finish(self):
        if self.at != len(self.data):
            raise Violation("trailing bytes in message")
        if self.error is not None:
            error, self.error = self.error, None
            raise error
