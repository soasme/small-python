package io.github.soasme.spy.worker;

import java.io.ByteArrayOutputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Values and messages of the worker protocol (docs/packaging/protocol.md).
 * Encoding trusts the parent's values; decoding trusts nothing and throws a
 * {@link Violation} for any message that breaks the protocol.
 */
final class Wire {
    private Wire() {}

    static final int MAX_DEPTH = 200;

    static final byte INIT = 0x01, EVAL = 0x02, EXEC = 0x03, CALL = 0x04, GET = 0x05, SET = 0x06, DELETE = 0x07,
            MODULE = 0x08, MOUNT = 0x09, COLLECT = 0x0a, OP = 0x0b, RELEASE = 0x0c, USAGE = 0x0d, HOST = 0x21,
            LOAD = 0x22, OUTPUT = 0x23, POLICY = 0x24, RESULT = 0x40, RAISE = 0x41;

    /** What the worker broke. */
    static final class Violation extends Exception {
        private static final long serialVersionUID = 1;

        Violation(String what) {
            super(what, null, false, false);
        }
    }

    /** A framed message of kind with fields, whose objects and functions must belong to rt. */
    static byte[] message(byte kind, Interpreter rt, Object... fields) {
        Encoder out = new Encoder(rt);
        out.bytes.write(new byte[4], 0, 4);
        out.bytes.write(kind);
        for (Object field : fields) {
            out.value(field, 0);
        }
        byte[] message = out.bytes.toByteArray();
        ByteBuffer.wrap(message).order(ByteOrder.LITTLE_ENDIAN).putInt(0, message.length - 4);
        return message;
    }

    private static final class Encoder {
        final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        final Interpreter rt;

        Encoder(Interpreter rt) {
            this.rt = rt;
        }

        void u32(long n) {
            for (int i = 0; i < 4; i++) {
                bytes.write((int) (n >>> (8 * i)));
            }
        }

        void u64(long n) {
            for (int i = 0; i < 8; i++) {
                bytes.write((int) (n >>> (8 * i)));
            }
        }

        void field(char tag, byte[] data) {
            bytes.write(tag);
            u32(data.length);
            bytes.write(data, 0, data.length);
        }

        void items(char tag, List<?> items, int depth) {
            bytes.write(tag);
            u32(items.size());
            for (Object item : items) {
                value(item, depth + 1);
            }
        }

        void pairs(Iterable<? extends Map.Entry<?, ?>> entries, int size, int depth) {
            bytes.write('d');
            u32(size);
            for (Map.Entry<?, ?> e : entries) {
                value(e.getKey(), depth + 1);
                value(e.getValue(), depth + 1);
            }
        }

        void value(Object x, int depth) {
            if (depth > MAX_DEPTH) {
                throw new PythonException("RecursionError", "value is too deeply nested to convert");
            }
            if (x == null) {
                bytes.write('N');
            } else if (x instanceof Boolean b) {
                bytes.write(b ? 'T' : 'F');
            } else if (x instanceof Long || x instanceof Integer || x instanceof Short || x instanceof Byte) {
                bytes.write('i');
                u64(((Number) x).longValue());
            } else if (x instanceof BigInteger n) {
                if (n.bitLength() < 64) {
                    value(n.longValue(), depth);
                } else {
                    field('I', ((n.signum() < 0 ? "-0x" : "0x") + n.abs().toString(16)).getBytes(
                            java.nio.charset.StandardCharsets.US_ASCII));
                }
            } else if (x instanceof Double || x instanceof Float) {
                bytes.write('f');
                u64(Double.doubleToRawLongBits(((Number) x).doubleValue()));
            } else if (x instanceof PyComplex c) {
                bytes.write('c');
                u64(Double.doubleToRawLongBits(c.real()));
                u64(Double.doubleToRawLongBits(c.imag()));
            } else if (x instanceof String || x instanceof Character) {
                field('s', utf8(x.toString()));
            } else if (x instanceof byte[] b) {
                field('b', b);
            } else if (x instanceof PyByteArray b) {
                field('B', b.bytes());
            } else if (x instanceof PyTuple t) {
                items('t', t.items(), depth);
            } else if (x instanceof PySet s) {
                items('S', s.items(), depth);
            } else if (x instanceof PyFrozenSet s) {
                items('z', s.items(), depth);
            } else if (x instanceof List<?> l) {
                items('l', l, depth);
            } else if (x instanceof Object[] a) {
                items('l', List.of(a), depth);
            } else if (x instanceof PyDict d) {
                List<Map.Entry<?, ?>> entries = new ArrayList<>();
                for (PyDict.Item item : d.items()) {
                    entries.add(new java.util.AbstractMap.SimpleImmutableEntry<>(item.key(), item.value()));
                }
                pairs(entries, entries.size(), depth);
            } else if (x instanceof Map<?, ?> m) {
                pairs(m.entrySet(), m.size(), depth);
            } else if (x instanceof PyObject o) {
                if (o.rt != rt) {
                    throw new IllegalArgumentException("the value belongs to another interpreter");
                }
                bytes.write('h');
                u64(o.id);
            } else if (x instanceof PyFunction f) {
                if (f.rt != rt) {
                    throw new IllegalArgumentException("the value belongs to another interpreter");
                }
                bytes.write('p');
                u64(f.id);
                value(f.name, depth);
            } else {
                throw new PythonException("TypeError", "cannot convert " + x.getClass().getName() + " to a Python value");
            }
        }
    }

    /** s in UTF-8, where a lone surrogate takes its three-byte form (surrogatepass). */
    static byte[] utf8(String s) {
        ByteArrayOutputStream out = new ByteArrayOutputStream(s.length());
        for (int i = 0; i < s.length(); ) {
            int c = s.codePointAt(i);
            i += Character.charCount(c);
            if (c < 0x80) {
                out.write(c);
            } else if (c < 0x800) {
                out.write(0xc0 | c >> 6);
                out.write(0x80 | (c & 0x3f));
            } else if (c < 0x10000) {
                out.write(0xe0 | c >> 12);
                out.write(0x80 | (c >> 6 & 0x3f));
                out.write(0x80 | (c & 0x3f));
            } else {
                out.write(0xf0 | c >> 18);
                out.write(0x80 | (c >> 12 & 0x3f));
                out.write(0x80 | (c >> 6 & 0x3f));
                out.write(0x80 | (c & 0x3f));
            }
        }
        return out.toByteArray();
    }

    /** Decodes exactly n values of message, after its kind, which must use it up. */
    static Object[] decode(byte[] message, Interpreter rt, int n) throws Violation {
        Decoder in = new Decoder(message, rt);
        Object[] values = new Object[n];
        for (int i = 0; i < n; i++) {
            values[i] = in.value(0);
        }
        if (in.at != message.length) {
            throw new Violation("trailing bytes in message");
        }
        return values;
    }

    private static final class Decoder {
        final byte[] data;
        final Interpreter rt;
        int at = 1;

        Decoder(byte[] data, Interpreter rt) {
            this.data = data;
            this.rt = rt;
        }

        int take(int n) throws Violation {
            if (n > data.length - at) {
                throw new Violation("truncated message");
            }
            at += n;
            return at - n;
        }

        long u64() throws Violation {
            int from = take(8);
            return ByteBuffer.wrap(data, from, 8).order(ByteOrder.LITTLE_ENDIAN).getLong();
        }

        /** A count of items, each at least minimum bytes long. */
        int count(int minimum) throws Violation {
            int from = take(4);
            long n = ByteBuffer.wrap(data, from, 4).order(ByteOrder.LITTLE_ENDIAN).getInt() & 0xffffffffL;
            if (n * minimum > data.length - at) {
                throw new Violation("count exceeds the message");
            }
            return (int) n;
        }

        byte[] bytes() throws Violation {
            int n = count(1);
            int from = take(n);
            byte[] out = new byte[n];
            System.arraycopy(data, from, out, 0, n);
            return out;
        }

        List<Object> items(int depth) throws Violation {
            int n = count(1);
            List<Object> items = new ArrayList<>(n);
            for (int i = 0; i < n; i++) {
                items.add(value(depth + 1));
            }
            return items;
        }

        Object value(int depth) throws Violation {
            if (depth > MAX_DEPTH) {
                throw new Violation("value nested too deeply");
            }
            char tag = (char) data[take(1)];
            switch (tag) {
                case 'N':
                    return null;
                case 'F':
                case 'T':
                    return tag == 'T';
                case 'i':
                    return u64();
                case 'I':
                    return big();
                case 'f':
                    return Double.longBitsToDouble(u64());
                case 'c':
                    return new PyComplex(Double.longBitsToDouble(u64()), Double.longBitsToDouble(u64()));
                case 's':
                    return string(bytes());
                case 'b':
                    return bytes();
                case 'B':
                    return new PyByteArray(bytes());
                case 'l':
                    return items(depth);
                case 't':
                    return new PyTuple(items(depth));
                case 'S':
                    return new PySet(items(depth));
                case 'z':
                    return new PyFrozenSet(items(depth));
                case 'd': {
                    int n = count(2);
                    List<PyDict.Item> items = new ArrayList<>(n);
                    for (int i = 0; i < n; i++) {
                        items.add(new PyDict.Item(value(depth + 1), value(depth + 1)));
                    }
                    return new PyDict(items);
                }
                case 'h':
                    return new PyObject(rt, u64());
                default:
                    throw new Violation(String.format("unknown value tag 0x%02x", (int) tag & 0xff));
            }
        }

        /** An int beyond 64 bits, which must be in canonical form. */
        BigInteger big() throws Violation {
            String text = new String(bytes(), java.nio.charset.StandardCharsets.ISO_8859_1);
            boolean negative = text.startsWith("-");
            String digits = negative ? text.substring(1) : text;
            if (!digits.startsWith("0x") || digits.length() == 2 || digits.charAt(2) == '0'
                    || !digits.substring(2).chars().allMatch(c -> c >= '0' && c <= '9' || c >= 'a' && c <= 'f')) {
                throw new Violation("invalid integer");
            }
            BigInteger n = new BigInteger(digits.substring(2), 16);
            if (n.bitLength() < 64 || negative && n.bitLength() == 64 && n.getLowestSetBit() == 63) {
                throw new Violation("integer should have been sent as 'i'");
            }
            return negative ? n.negate() : n;
        }
    }

    /**
     * The string of UTF-8 in which a lone surrogate may take its three-byte
     * form (CPython's surrogatepass); anything else, such as an overlong form,
     * is a violation.
     */
    static String string(byte[] b) throws Violation {
        StringBuilder out = new StringBuilder(b.length);
        for (int i = 0; i < b.length; ) {
            int c = b[i++] & 0xff;
            int more = c < 0x80 ? 0 : c >= 0xc2 && c < 0xe0 ? 1 : c >= 0xe0 && c < 0xf0 ? 2 : c >= 0xf0 && c < 0xf5 ? 3 : -1;
            if (more < 0 || more > b.length - i) {
                throw new Violation("invalid UTF-8");
            }
            c &= 0x7f >> more;
            for (int k = 0; k < more; k++) {
                int t = b[i++] & 0xff;
                if ((t & 0xc0) != 0x80) {
                    throw new Violation("invalid UTF-8");
                }
                c = c << 6 | (t & 0x3f);
            }
            if (more == 2 && c < 0x800 || more == 3 && (c < 0x10000 || c > 0x10ffff)) {
                throw new Violation("invalid UTF-8");
            }
            out.appendCodePoint(c);
        }
        return out.toString();
    }
}
