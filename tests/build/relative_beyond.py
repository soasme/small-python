# build:
# negative: pkg/mod.py:1: error: attempted relative import beyond top-level package
# description: a relative import past the top-level package fails the build.
import pkg.mod
