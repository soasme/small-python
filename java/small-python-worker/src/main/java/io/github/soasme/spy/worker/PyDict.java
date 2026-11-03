package io.github.soasme.spy.worker;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/** A Python dict's items, in order; kept as a sequence, so Java never hashes the keys. */
public record PyDict(List<Item> items) {
    /** One key and its value. */
    public record Item(Object key, Object value) {}

    public PyDict {
        items = Collections.unmodifiableList(new ArrayList<>(items));
    }

    /** A dict of alternating keys and values. */
    public static PyDict of(Object... keysAndValues) {
        if (keysAndValues.length % 2 != 0) {
            throw new IllegalArgumentException("a key without a value");
        }
        List<Item> items = new ArrayList<>();
        for (int i = 0; i < keysAndValues.length; i += 2) {
            items.add(new Item(keysAndValues[i], keysAndValues[i + 1]));
        }
        return new PyDict(items);
    }

    /** The value of the last item whose key equals key in Java, or null. */
    public Object get(Object key) {
        Object value = null;
        for (Item item : items) {
            if (Objects.equals(item.key(), key)) {
                value = item.value();
            }
        }
        return value;
    }
}
