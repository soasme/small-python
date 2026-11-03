#!/bin/sh
# Stage a release archive's contents in DIR and check them (tests/archive.py):
# the tools, and the headers and libraries spyc builds executables with.
# usage: tools/archive.sh DIR [.exe]   (after make spy spyc spy-worker libspy.a libspy-std.a)
set -e
dir=$1 exe=$2
mkdir -p "$dir/licenses"
cp "spy$exe" "spyc$exe" "spy-worker$exe" spy.h spy-std.h libspy.a libspy-std.a LICENSE README.md "$dir/"
cp docs/licenses/python.txt docs/licenses/unicode.txt docs/licenses/quickjs.txt "$dir/licenses/"
python=$(command -v python || command -v python3)
"$python" tests/archive.py "$dir"
