#!/usr/bin/env bash

set -euo pipefail

./build.sh

cd ..
python ../common/release.py "$CALIBRE_GITHUB_TOKEN"
cd .build
