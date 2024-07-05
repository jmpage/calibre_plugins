#!/usr/bin/env bash
#
# Generates translation files (with Windows path separators)
#
# NOTE: This script requires pygettext.py:
#   https://github.com/python/cpython/blob/main/Tools/i18n/pygettext.py
#
# Optional environment variables:
#   PYGETTEXT_DIRECTORY: Path to the location of pygettext.py
#
# This script is a 1-1 copy of generate-pot.cmd in terms of functionality.
# Likewise, this script assumes that it's being executed from within
# .build/

set -euo pipefail

cd ..

PYGETTEXT="pygettext.py"
PYGETTEXT_DIRECTORY="${PYGETTEXT_DIRECTORY:-}"
if [ -n "$PYGETTEXT_DIRECTORY" ]; then
    PYGETTEXT="$PYGETTEXT_DIRECTORY/pygettext.py"
fi

echo 'Regenerating translations .pot file'

python "$PYGETTEXT" -d extract-isbn -p translations \
                 action.py config.py dialogs.py jobs.py ../common/common_*.py
sed -i '/^#/s/\//\\/g' translations/extract-isbn.pot

cd .build
