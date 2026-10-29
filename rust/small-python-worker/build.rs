//! Builds the spy-worker executable, which the crate embeds: spy-worker.c
//! compiled once as the engine with counted allocations, once as the worker
//! (docs/packaging/protocol.md), and linked with the target's C compiler.

use std::path::PathBuf;

fn main() {
    let dir = small_python_src::source_dir();
    let out = PathBuf::from(std::env::var_os("OUT_DIR").unwrap());
    let mut objects = Vec::new();
    for part in ["engine", "worker"] {
        let mut build = small_python_src::build();
        build.file(dir.join("spy-worker.c")).out_dir(out.join(part));
        if part == "engine" {
            build.define("SPY_WORKER_ENGINE", None);
        }
        objects.extend(build.compile_intermediates());
    }
    let mut link = small_python_src::build().get_compiler().to_command();
    link.args(&objects).arg("-o").arg(out.join("spy-worker")).arg("-lm");
    if std::env::var("CARGO_CFG_WINDOWS").is_ok() {
        link.arg("-static");
    }
    let status = link.status().expect("cannot run the C compiler to link spy-worker");
    assert!(status.success(), "linking spy-worker failed: {status}");
}
