package io.github.soasme.spy;

import java.io.ByteArrayOutputStream;
import java.lang.reflect.Array;
import java.lang.reflect.Constructor;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.RecordComponent;
import java.lang.reflect.Type;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiConsumer;
import java.util.function.LongConsumer;

/** The conversions of Interpreter.toValue and PyObject.as, run while the runtime is entered. */
final class Convert {
    private Convert() {}

    /** x as an owned engine reference. */
    static long ref(Interpreter rt, long ctx, Object x) {
        if (x == null) {
            return rt.made(Native.none(ctx));
        } else if (x instanceof PyObject v) {
            if (v.runtime() != rt) {
                throw new PythonException("ValueError", "the value belongs to another runtime");
            }
            return Native.retain(v.ptr);
        } else if (x instanceof HostFunction f) {
            return rt.made(Native.function(ctx, "function", f));
        } else if (x instanceof Boolean b) {
            return rt.made(Native.bool(ctx, b));
        } else if (x instanceof Long || x instanceof Integer || x instanceof Short || x instanceof Byte) {
            return rt.made(Native.integer(ctx, ((Number) x).longValue()));
        } else if (x instanceof BigInteger n) {
            if (n.bitLength() > 63) {
                throw overflow();
            }
            return rt.made(Native.integer(ctx, n.longValue()));
        } else if (x instanceof Double || x instanceof Float) {
            return rt.made(Native.real(ctx, ((Number) x).doubleValue()));
        } else if (x instanceof String || x instanceof Character) {
            return rt.made(Native.string(ctx, x.toString()));
        } else if (x instanceof byte[] b) {
            return rt.made(Native.bytes(ctx, b));
        } else if (x instanceof PyTuple t) {
            long[] items = new long[t.items().size()];
            try {
                for (int i = 0; i < items.length; i++) {
                    items[i] = ref(rt, ctx, t.items().get(i));
                }
                return rt.made(Native.tuple(ctx, items));
            } finally {
                for (long item : items) {
                    Native.release(item);
                }
            }
        } else if (x instanceof List<?> || x instanceof Object[]) {
            List<?> items = x instanceof List<?> l ? l : List.of((Object[]) x);
            long list = rt.made(Native.list(ctx));
            try {
                for (Object item : items) {
                    long i = ref(rt, ctx, item);
                    try {
                        rt.check(Native.listAppend(ctx, list, i));
                    } finally {
                        Native.release(i);
                    }
                }
            } catch (RuntimeException e) {
                Native.release(list);
                throw e;
            }
            return list;
        } else if (x instanceof Map<?, ?> m) {
            return dict(rt, ctx, m);
        } else if (x.getClass().isRecord()) {
            Map<String, Object> fields = new LinkedHashMap<>();
            for (RecordComponent c : x.getClass().getRecordComponents()) {
                try {
                    c.getAccessor().setAccessible(true);
                    fields.put(c.getName(), c.getAccessor().invoke(x));
                } catch (ReflectiveOperationException | RuntimeException e) {
                    throw new PythonException("TypeError", "cannot read " + x.getClass().getName() + "." + c.getName());
                }
            }
            return dict(rt, ctx, fields);
        }
        throw new PythonException("TypeError", "cannot convert " + x.getClass().getName() + " to a Python value");
    }

    private static long dict(Interpreter rt, long ctx, Map<?, ?> m) {
        long dict = rt.made(Native.dict(ctx));
        try {
            for (Map.Entry<?, ?> e : m.entrySet()) {
                long k = ref(rt, ctx, e.getKey());
                try {
                    long i = ref(rt, ctx, e.getValue());
                    try {
                        rt.check(Native.setItem(ctx, dict, k, i));
                    } finally {
                        Native.release(i);
                    }
                } finally {
                    Native.release(k);
                }
            }
        } catch (RuntimeException e) {
            Native.release(dict);
            throw e;
        }
        return dict;
    }

    private static final Map<Class<?>, Class<?>> BOXES = Map.of(boolean.class, Boolean.class, long.class, Long.class,
            int.class, Integer.class, short.class, Short.class, byte.class, Byte.class, double.class, Double.class,
            float.class, Float.class);

    /** The borrowed value v decoded into type. */
    static Object decode(Interpreter rt, long v, Type type) {
        Class<?> raw = type instanceof ParameterizedType p ? (Class<?>) p.getRawType() : (Class<?>) type;
        long ctx = rt.context();
        int kind = Native.type(v);
        if (kind == Native.NONE && !raw.isPrimitive() && raw != PyObject.class) {
            return null;
        }
        raw = BOXES.getOrDefault(raw, raw);
        if (raw == PyObject.class) {
            return new PyObject(rt, Native.retain(v));
        } else if (raw == Object.class) {
            return natural(rt, v);
        } else if (raw == Boolean.class) {
            if (kind != Native.BOOL) {
                throw new PythonException("TypeError", "expected bool");
            }
            return Native.truth(ctx, v) != 0;
        } else if (raw == Long.class || raw == Integer.class || raw == Short.class || raw == Byte.class) {
            long n = Native.asInt(ctx, v);
            pending(ctx);
            long min = raw == Long.class ? Long.MIN_VALUE : raw == Integer.class ? Integer.MIN_VALUE
                    : raw == Short.class ? Short.MIN_VALUE : Byte.MIN_VALUE;
            if (n < min || n > -(min + 1)) {
                throw overflow();
            }
            return raw == Long.class ? (Object) n : raw == Integer.class ? (Object) (int) n
                    : raw == Short.class ? (Object) (short) n : (Object) (byte) n;
        } else if (raw == BigInteger.class) {
            if (kind == Native.INT) {
                return new BigInteger(rt.wrap(Native.repr(ctx, v)).as(String.class));
            }
            long n = Native.asInt(ctx, v);
            pending(ctx);
            return BigInteger.valueOf(n);
        } else if (raw == Double.class || raw == Float.class) {
            double x = Native.asFloat(ctx, v);
            pending(ctx);
            return raw == Double.class ? (Object) x : (Object) (float) x;
        } else if (raw == String.class) {
            String s = Native.asString(ctx, v);
            pending(ctx);
            return s;
        } else if (raw == byte[].class && kind == Native.BYTES) {
            return Native.asBytes(ctx, v);
        } else if (raw == byte[].class) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            each(rt, v, item -> {
                long n = (Long) decode(rt, item, Long.class);
                if (n < 0 || n > 255) {
                    throw new PythonException("ValueError", "byte must be in range(0, 256)");
                }
                out.write((int) n);
            });
            return out.toByteArray();
        } else if (raw == PyTuple.class) {
            List<Object> items = new ArrayList<>();
            each(rt, v, item -> items.add(natural(rt, item)));
            return new PyTuple(items);
        } else if (raw.isAssignableFrom(ArrayList.class)) {
            Type element = argument(type, 0);
            List<Object> items = new ArrayList<>();
            each(rt, v, item -> items.add(decode(rt, item, element)));
            return items;
        } else if (raw.isAssignableFrom(LinkedHashMap.class)) {
            Type key = argument(type, 0), item = argument(type, 1);
            Map<Object, Object> map = new LinkedHashMap<>();
            pairs(rt, v, (k, i) -> map.put(decode(rt, k, key), decode(rt, i, item)));
            return map;
        } else if (raw.isRecord()) {
            return record(rt, v, raw);
        }
        throw new PythonException("TypeError", "cannot decode into " + type.getTypeName());
    }

    /** A record from the mapping v, by component name; missing components are null, zero or false. */
    private static Object record(Interpreter rt, long v, Class<?> type) {
        RecordComponent[] components = type.getRecordComponents();
        Map<String, Integer> index = new HashMap<>();
        Class<?>[] types = new Class<?>[components.length];
        Object[] values = new Object[components.length];
        for (int i = 0; i < components.length; i++) {
            index.put(components[i].getName(), i);
            types[i] = components[i].getType();
            values[i] = types[i].isPrimitive() ? Array.get(Array.newInstance(types[i], 1), 0) : null;
        }
        pairs(rt, v, (key, item) -> {
            Integer i = index.get(decode(rt, key, String.class));
            if (i != null) {
                values[i] = decode(rt, item, components[i].getGenericType());
            }
        });
        try {
            Constructor<?> constructor = type.getDeclaredConstructor(types);
            constructor.setAccessible(true);
            return constructor.newInstance(values);
        } catch (ReflectiveOperationException | RuntimeException e) {
            throw new PythonException("TypeError", "cannot construct " + type.getName() + ": " + e);
        }
    }

    /** v as an Object receives it. */
    private static Object natural(Interpreter rt, long v) {
        long ctx = rt.context();
        switch (Native.type(v)) {
            case Native.NONE:
                return null;
            case Native.BOOL:
                return Native.truth(ctx, v) != 0;
            case Native.INT:
                long n = Native.asInt(ctx, v);
                if (!Native.errorPending(ctx)) {
                    return n;
                }
                Native.takeError(ctx);
                return decode(rt, v, BigInteger.class);
            case Native.FLOAT:
                return decode(rt, v, Double.class);
            case Native.STRING:
                return decode(rt, v, String.class);
            case Native.BYTES:
                return decode(rt, v, byte[].class);
            case Native.LIST:
                return decode(rt, v, List.class);
            case Native.TUPLE:
                return decode(rt, v, PyTuple.class);
            case Native.DICT:
                return decode(rt, v, Map.class);
            default:
                return new PyObject(rt, Native.retain(v));
        }
    }

    private static Type argument(Type type, int i) {
        return type instanceof ParameterizedType p ? p.getActualTypeArguments()[i] : Object.class;
    }

    /** Calls f with each item of the iterable v, borrowed. */
    private static void each(Interpreter rt, long v, LongConsumer f) {
        long ctx = rt.context();
        long it = rt.made(Native.iter(ctx, v));
        try {
            for (long item; (item = Native.next(ctx, it)) != 0; ) {
                try {
                    f.accept(item);
                } finally {
                    Native.release(item);
                }
            }
            pending(ctx);
        } finally {
            Native.release(it);
        }
    }

    /** Calls f with each key of the mapping v and its item, borrowed. */
    private static void pairs(Interpreter rt, long v, BiConsumer<Long, Long> f) {
        each(rt, v, key -> {
            long item = rt.made(Native.getItem(rt.context(), v, key));
            try {
                f.accept(key, item);
            } finally {
                Native.release(item);
            }
        });
    }

    private static void pending(long ctx) {
        if (Native.errorPending(ctx)) {
            throw Native.takeError(ctx);
        }
    }

    private static PythonException overflow() {
        return new PythonException("OverflowError", "int out of range for the Java type");
    }
}
