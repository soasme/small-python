package io.github.soasme.spy.worker;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** A Python set's items, in the worker's order; kept as a sequence, so Java never hashes them. */
public record PySet(List<Object> items) {
    public PySet {
        items = Collections.unmodifiableList(new ArrayList<>(items));
    }

    public static PySet of(Object... items) {
        return new PySet(Arrays.asList(items));
    }
}
