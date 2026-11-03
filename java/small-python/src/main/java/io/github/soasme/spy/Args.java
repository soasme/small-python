package io.github.soasme.spy;

import java.util.List;
import java.util.Map;

/** The arguments of a call to a host function. */
public record Args(List<PyObject> positional, Map<String, PyObject> keywords) {
    public Args {
        positional = List.copyOf(positional);
        keywords = Map.copyOf(keywords);
    }

    /** The positional argument at index, decoded; TypeError when there are fewer. */
    public <T> T get(int index, Class<T> type) {
        if (index >= positional.size()) {
            throw new PythonException("TypeError", "expected at least " + (index + 1) + " argument"
                    + (index == 0 ? "" : "s") + ", got " + positional.size());
        }
        return positional.get(index).as(type);
    }

    /** The keyword argument name, decoded, or otherwise when it was not given. */
    public <T> T keyword(String name, Class<T> type, T otherwise) {
        PyObject v = keywords.get(name);
        return v == null ? otherwise : v.as(type);
    }
}
