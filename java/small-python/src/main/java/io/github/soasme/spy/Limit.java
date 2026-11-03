package io.github.soasme.spy;

/** The bounds {@link Interpreter#setLimit} sets, in the order of spy.h's SPY_LIMIT_ constants. */
public enum Limit {
    /** Steps of each top-level operation; 0 is unlimited. */
    STEPS,
    /** Bytes the engine holds; 0 is unlimited. */
    MEMORY,
    /** Bytes each top-level operation prints; 0 is unlimited. */
    OUTPUT,
    /** Python call depth. */
    RECURSION,
    /** Digits of int-str conversions; 0 is unlimited, otherwise at least 640. */
    INT_DIGITS,
    /** Bytes of C stack the engine may use. */
    STACK,
}
