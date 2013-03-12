#!/bin/bash -xe

PYBOT="pybot"

cd $(dirname $0)
zip -x '.*' -x '*.pyc' -r - $PYBOT > $PYBOT.zip
