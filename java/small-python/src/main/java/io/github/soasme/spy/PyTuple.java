package io.github.soasme.spy;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** A Python tuple's items; a tuple decodes to it, and it converts to a tuple. */
public record PyTuple(List<Object> items) {
    public PyTuple {
        items = Collections.unmodifiableList(new ArrayList<>(items));
    }

    public static PyTuple of(Object... items) {
        return new PyTuple(Arrays.asList(items));
    }
}
