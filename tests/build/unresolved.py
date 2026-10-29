# build:
# negative: unresolved.py:7: error: No module named 'nosuch'
# description: an unguarded import of a missing module fails the build at its line.
try:
    import optional_but_missing
except ImportError:
    import nosuch
