package io.github.soasme.spy;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Locale;

/**
 * Loads the engine library the jar carries for this platform. It is written
 * once to the user's cache directory, named by its hash, and used from there
 * only while its bytes equal the jar's; the system property
 * {@code io.github.soasme.spy.library} names a library to load instead.
 */
final class NativeLibrary {
    private NativeLibrary() {}

    static void load() {
        String path = System.getProperty("io.github.soasme.spy.library");
        System.load(path != null ? path : extract(System.mapLibraryName("spyjni")).toString());
    }

    /** The platform name of the jar's native directories, as the release archives name them. */
    static String platform() {
        String os = System.getProperty("os.name").toLowerCase(Locale.ROOT);
        String arch = System.getProperty("os.arch").toLowerCase(Locale.ROOT);
        os = os.startsWith("mac") ? "macos" : os.startsWith("windows") ? "windows" : os;
        arch = arch.equals("aarch64") ? "arm64" : arch.equals("amd64") ? "x86_64" : arch;
        return os + "-" + arch;
    }

    private static Path extract(String name) {
        String resource = "native/" + platform() + "/" + name;
        byte[] bytes;
        try (InputStream in = NativeLibrary.class.getResourceAsStream(resource)) {
            if (in == null) {
                throw new UnsatisfiedLinkError("small-python has no engine library for " + platform()
                        + "; build one and name it with -Dio.github.soasme.spy.library");
            }
            bytes = in.readAllBytes();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        int dot = name.lastIndexOf('.');
        Path file = cacheDirectory().resolve(name.substring(0, dot) + "-" + hash(bytes) + name.substring(dot));
        try {
            if (!Files.isRegularFile(file) || !Arrays.equals(Files.readAllBytes(file), bytes)) {
                Files.createDirectories(file.getParent());
                Path temporary = Files.createTempFile(file.getParent(), name, ".tmp");
                Files.write(temporary, bytes);
                Files.move(temporary, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            }
        } catch (IOException e) {
            throw new UncheckedIOException("cannot write the engine library to " + file, e);
        }
        return file;
    }

    /** The cache directory as rust.md 4.1 chooses it, with small-python appended. */
    static Path cacheDirectory() {
        String home = System.getProperty("user.home");
        String base = switch (platform().substring(0, platform().indexOf('-'))) {
            case "macos" -> home + "/Library/Caches";
            case "windows" -> System.getenv("LOCALAPPDATA");
            default -> System.getenv("XDG_CACHE_HOME") != null ? System.getenv("XDG_CACHE_HOME") : home + "/.cache";
        };
        return Paths.get(base != null ? base : System.getProperty("java.io.tmpdir"), "small-python");
    }

    private static String hash(byte[] bytes) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes), 0, 8);
        } catch (NoSuchAlgorithmException e) {
            throw new AssertionError(e);
        }
    }
}
