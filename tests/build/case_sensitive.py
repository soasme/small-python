# build:
# bundles: case_sensitive.py
# description: module names compare by exact spelling, even on a case-insensitive file system.
try:
    import mod
except ImportError:
    mod = None
assert mod is None
