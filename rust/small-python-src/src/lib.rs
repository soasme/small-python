//! The C sources of Small Python, for build scripts.
//!
//! The engine stays plain C11 with no knowledge of Rust: this crate only
//! locates the sources and configures a [`cc::Build`] for them, as `lua-src`
//! does for `mlua`. In the repository it reads the sources from the checkout
//! itself; a published crate carries a copy in `csrc/`.

use std::path::PathBuf;

/// The directory holding `spy.h`, `spy.c`, `spy-std.c`, `spy-worker.c`, and
/// the headers they include.
pub fn source_dir() -> PathBuf {
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let checkout = manifest.join("../..");
    if checkout.join("spy.c").is_file() {
        checkout
    } else {
        manifest.join("csrc")
    }
}

/// A C11 build with the sources' directory on the include path. Each source
/// file names what it depends on, so callers add files and compile.
pub fn build() -> cc::Build {
    let dir = source_dir();
    for file in [
        "spy.c",
        "spy.h",
        "spy-std.c",
        "spy-std.h",
        "spy-std-modules.h",
        "spy-intrinsics.h",
        "spy-unicode.h",
        "spy-worker.c",
    ] {
        println!("cargo:rerun-if-changed={}", dir.join(file).display());
    }
    let mut build = cc::Build::new();
    build.include(&dir).std("c11").warnings(false);
    if build.get_compiler().is_like_msvc() {
        panic!(
            "Small Python needs C11 complex numbers, which MSVC lacks; \
                build for a GNU target such as x86_64-pc-windows-gnu"
        );
    }
    build
}
