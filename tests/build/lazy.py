# build:
# bundles: lazy.py heavy.py log.py
# description: a lazy import (PEP 810) is bundled, and its module still runs only when the name is first used.
lazy import heavy
import log
assert log.events == []
assert heavy.VALUE == 42
assert log.events == ["heavy"]
