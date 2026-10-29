# build:
# negative: relative_entry.py:4: error: attempted relative import with no known parent package
# description: a file entry has no package, so a relative import in it fails the build.
from . import sibling
