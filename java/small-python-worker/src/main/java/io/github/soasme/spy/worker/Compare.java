package io.github.soasme.spy.worker;

/** The rich comparisons of {@link PyObject#compare}, with their operation numbers (protocol.md 7.3). */
public enum Compare {
    LT(11), LE(12), EQ(13), NE(14), GT(15), GE(16);

    final int op;

    Compare(int op) {
        this.op = op;
    }
}
