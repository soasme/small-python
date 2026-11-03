package io.github.soasme.spy.worker;

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
 * The spy-worker the jar carries for this platform, written once to the
 * user's cache directory, executable by the user alone, and named by its
 * hash; it is used from there only while its bytes equal the jar's.
 */
final class WorkerExecutable {
    private WorkerExecutable() {}

    private static Path path;

    static synchronized Path path() {
        if (path == null) {
            path = extract();
        }
        return path;
    }

    /** The platform name of the jar's native directories, as the release archives name them. */
    static String platform() {
        String os = System.getProperty("os.name").toLowerCase(Locale.ROOT);
        String arch = System.getProperty("os.arch").toLowerCase(Locale.ROOT);
        os = os.startsWith("mac") ? "macos" : os.startsWith("windows") ? "windows" : os;
        arch = arch.equals("aarch64") ? "arm64" : arch.equals("amd64") ? "x86_64" : arch;
        return os + "-" + arch;
    }

    private static Path extract() {
        boolean windows = platform().startsWith("windows-");
        String name = windows ? "spy-worker.exe" : "spy-worker";
        byte[] bytes;
        try (InputStream in = WorkerExecutable.class.getResourceAsStream("native/" + platform() + "/" + name)) {
            if (in == null) {
                throw new WorkerException("small-python-worker has no worker for " + platform()
                        + "; build spy-worker and name it with Interpreter.Builder.worker", java.util.OptionalInt.empty());
            }
            bytes = in.readAllBytes();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        Path file = cacheDirectory().resolve("spy-worker-" + hash(bytes) + (windows ? ".exe" : ""));
        try {
            if (!Files.isRegularFile(file) || !Arrays.equals(Files.readAllBytes(file), bytes)) {
                Files.createDirectories(file.getParent());
                Path temporary = Files.createTempFile(file.getParent(), "spy-worker", ".tmp");
                Files.write(temporary, bytes);
                if (!temporary.toFile().setExecutable(true, true)) {
                    throw new IOException("cannot make " + temporary + " executable");
                }
                Files.move(temporary, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            }
        } catch (IOException e) {
            throw new UncheckedIOException("cannot write the worker to " + file, e);
        }
        return file;
    }

    /** The cache directory as rust.md 4.1 chooses it, with small-python appended. */
    private static Path cacheDirectory() {
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
