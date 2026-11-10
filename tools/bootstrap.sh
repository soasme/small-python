#!/bin/sh
# Fetch the previous release's spyc into DIR (default .obj/bootstrap): the
# spyc that builds this tree's spyc, which never builds itself
# (docs/build.md 9.1). Each release moves VERSION and the checksums to the
# release before it (Workflow, AGENTS.md).
#
#   tools/bootstrap.sh [DIR]
set -eu
VERSION=0.9.0
DIR=${1:-.obj/bootstrap}
case "$(uname -s)-$(uname -m)" in
    Linux-x86_64) platform=linux-x86_64 archive=tar.gz
        sum=bfcef981d7dff9bdae8d3c84dcec78c9b0a0c032798e08e6d6efa702e090e647 ;;
    Linux-aarch64 | Linux-arm64) platform=linux-arm64 archive=tar.gz
        sum=e555b9b05c177a34c9335a0919d278387399d051853863ab0670fd6a02501153 ;;
    Darwin-arm64) platform=macos-arm64 archive=tar.gz
        sum=debac6f4ac3afce9190eb4cb12564d06b78c3b11f593ede20c32de7d89300fc2 ;;
    Darwin-x86_64) platform=macos-x86_64 archive=tar.gz
        sum=2fdbdf8d89be69944663623b13e46ed5be7653ebde49e49e1c84d1597f3d4538 ;;
    MINGW*-x86_64 | MSYS*-x86_64 | CYGWIN*-x86_64) platform=windows-x86_64 archive=zip
        sum=6a18af91a926054ae4b98dcddac5f964d438116b9adc000233398916089f887b ;;
    *) echo "bootstrap: spyc $VERSION has no release for $(uname -sm); build spyc with SPYC_BOOTSTRAP=path/to/spyc" >&2
       exit 1 ;;
esac
if [ "$(cat "$DIR/VERSION" 2>/dev/null)" = "$VERSION" ]; then exit 0; fi
name=small-python-$VERSION-$platform
mkdir -p "$DIR"
curl -sSfL -o "$DIR/$name.$archive" "https://github.com/soasme/small-python/releases/download/v$VERSION/$name.$archive"
if command -v sha256sum >/dev/null; then actual=$(sha256sum "$DIR/$name.$archive"); else actual=$(shasum -a 256 "$DIR/$name.$archive"); fi
if [ "${actual%% *}" != "$sum" ]; then
    echo "bootstrap: $name.$archive does not match its checksum" >&2
    rm -f "$DIR/$name.$archive"
    exit 1
fi
tar -xf "$DIR/$name.$archive" -C "$DIR"
for file in "$DIR/$name"/spyc*; do cp "$file" "$DIR/"; done
rm -rf "$DIR/$name" "$DIR/$name.$archive"
echo "$VERSION" > "$DIR/VERSION"
