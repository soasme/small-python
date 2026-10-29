fn main() {
    let dir = small_python_src::source_dir();
    small_python_src::build().file(dir.join("spy.c")).file(dir.join("spy-std.c")).compile("spy");
    if std::env::var("CARGO_CFG_UNIX").is_ok() {
        println!("cargo:rustc-link-lib=m");
    }
    let header = std::fs::read_to_string(dir.join("spy.h")).expect("spy.h");
    let version = header
        .lines()
        .find_map(|line| line.strip_prefix("#define SPY_VERSION \""))
        .and_then(|rest| rest.strip_suffix('"'))
        .expect("SPY_VERSION in spy.h");
    println!("cargo:rustc-env=SPY_VERSION={version}");
    // Dependents' build scripts read this as DEP_SPY_INCLUDE.
    println!("cargo:include={}", dir.display());
}
