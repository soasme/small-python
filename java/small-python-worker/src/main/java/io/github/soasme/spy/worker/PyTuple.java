package io.github.soasme.spy.worker;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** A Python tuple's items. */
public record PyTuple(List<Object> items) {
    public PyTuple {
        items = Collections.unmodifiableList(new ArrayList<>(items));
    }

    public static PyTuple of(Object... items) {
        return new PyTuple(Arrays.asList(items));
    }
}
