package io.github.soasme.spy;

/** Returns a module's source, or null when there is none; what it throws fails the import. */
@FunctionalInterface
public interface ModuleLoader {
    String load(String name) throws Exception;
}
