#!/usr/bin/env bash
# 
# Copyright (c) Advanced Micro Devices, Inc.
# All rights reserved.
# 

set -e
set -x

tool=$1

OUTPUT=${tool}_output.csv
SAVESPACE=/myworkspace/

cd $SAVESPACE
if [ -d "$OUTPUT" ]; then
	mkdir "$OUTPUT"
fi

mv prof.csv "$OUTPUT"

chmod -R a+rw "${SAVESPACE}/${OUTPUT}"
