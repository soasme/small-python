package io.github.soasme.spy.worker;

import java.util.Arrays;

/** A Python bytearray's contents; a bytes is a {@code byte[]}. */
public record PyByteArray(byte[] bytes) {
    public PyByteArray {
        bytes = bytes.clone();
    }

    @Override
    public byte[] bytes() {
        return bytes.clone();
    }

    @Override
    public boolean equals(Object o) {
        return o instanceof PyByteArray b && Arrays.equals(bytes, b.bytes);
    }

    @Override
    public int hashCode() {
        return Arrays.hashCode(bytes);
    }

    @Override
    public String toString() {
        return "PyByteArray" + Arrays.toString(bytes);
    }
}
