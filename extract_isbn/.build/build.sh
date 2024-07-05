#!/usr/bin/env bash
#
# Constructs the plugin zip file and installs it in Calibre.
#
# Optional environment variables:
#   CALIBRE_DIRECTORY: Path to the Calibre installation
#   DEBUG: Print every command, if set to 1
#
# This script is a 1-1 copy of build.cmd in terms of functionality.
# Likewise, this script assumes that it's being executed from within
# .build/

set -euo pipefail

if [ "${DEBUG:-0}" -eq 1 ]; then
    set -x
fi

CALIBRE_DIRECTORY="${CALIBRE_DIRECTORY:-}"
CALIBRE_CUSTOMIZE=calibre-customize
CALIBRE_DEBUG=calibre-debug
if [ -n "$CALIBRE_DIRECTORY" ]; then
    CALIBRE_CUSTOMIZE=$CALIBRE_DIRECTORY/$CALIBRE_CUSTOMIZE
    CALIBRE_DEBUG=$CALIBRE_DIRECTORY/$CALIBRE_DEBUG
fi

function build_plugin {
    python ../common/build.py
}

function cleanup_common_files {
    echo 'Deleting common files after zip'
    rm ./common_*.py
}

function compile_translations {
    cd ..
    if [ -d translations ]; then
        cd translations
        export PYTHONIOENCODING=UTF-8
        for file in *.po; do
            $CALIBRE_DEBUG -c 'from calibre.translations.msgfmt import main; main()' "$file"
        done
        cd ..
    else
        echo 'No translations subfolder found'
    fi
}

function copy_common_files {
    echo 'Copying common files for zip'
    for file in ../common/common_*.py; do
        cp -r "$file" . > /dev/null
    done
}

function install_plugin {
    echo "Installing plugin \"$1\" into calibre..."
    $CALIBRE_CUSTOMIZE -a "$1"
}

compile_translations
copy_common_files
build_plugin
cleanup_common_files
# Install the most recently created zip file
install_plugin "$(find ./*.zip -printf "%T+\t%p\n" | sort | tail -n1 | cut -f 2)"
echo 'Build completed successfully'
