#!/bin/bash -xe
#
# Creates a self contained Python zip.
#

ROOT=$(dirname $0)
PYBOT=$(basename $(dirname $(realpath $0)))
TIME=$(date +%s)
CWD=$(realpath $ROOT/..)
ZIP="$CWD/$PYBOT.zip"

# Create Zip
cd $ROOT
zip -x '.*' -x '*.pyc' -r - . > $ZIP.$TIME

# Add interpreter
echo '#!/usr/bin/env python2' | cat - $ZIP.$TIME > $ZIP

# Make executable
chmod u+x $ZIP

# Cleanup
rm -f $ZIP.$TIME
