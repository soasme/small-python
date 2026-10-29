# build:
# negative: guard_scope.py:8: error: No module named 'nosuch'
# oracle: passes
# description: only a try around the import itself guards it; a handler in the caller does not, though the program would run.


def load():
    import nosuch


try:
    load()
except ImportError:
    pass
