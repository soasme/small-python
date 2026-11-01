# spec: PLS-315 23.1.6
# description: lower() maps capital sigma to final sigma after a cased letter and before none, skipping case-ignorable characters.
from harness import *

assert_eq("ΑΣ".lower(), "ας")
assert_eq("ΑΣ Σ".lower(), "ας σ")
assert_eq("Σ".lower(), "σ")
assert_eq("ΑΣΑ".lower(), "ασα")
assert_eq("\u0391\u0301\u03a3\u0301".lower(), "\u03b1\u0301\u03c2\u0301")
assert_eq("ΑΣ́Α".lower(), "ασ́α")
assert_eq(b"\xa3".lower(), b"\xa3")
