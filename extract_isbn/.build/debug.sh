#!/usr/bin/env bash
#
# Build and install the plugin, then start calibre in debug mode.
#
# Optional environment variables:
#   CALIBRE_DIRECTORY: Path to the Calibre installation

set -euo pipefail

CALIBRE_DIRECTORY="${CALIBRE_DIRECTORY:-}"
CALIBRE_DEBUG=calibre-debug
if [ -n "$CALIBRE_DIRECTORY" ]; then
    CALIBRE_DEBUG=$CALIBRE_DIRECTORY/$CALIBRE_DEBUG
fi

./build.sh

export CALIBRE_DEVELOP_FROM=
export CALIBRE_OVERRIDE_LANG=

echo 'Starting calibre in debug mode'
$CALIBRE_DEBUG -g
