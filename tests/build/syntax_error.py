# build:
# negative: broken.py:1: error:
# description: a module with a syntax error fails the build, even where its import is guarded.
try:
    import broken
except ImportError:
    broken = None
