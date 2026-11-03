package io.github.soasme.spy.worker;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** A Python frozenset's items, in the worker's order; kept as a sequence, so Java never hashes them. */
public record PyFrozenSet(List<Object> items) {
    public PyFrozenSet {
        items = Collections.unmodifiableList(new ArrayList<>(items));
    }

    public static PyFrozenSet of(Object... items) {
        return new PyFrozenSet(Arrays.asList(items));
    }
}
