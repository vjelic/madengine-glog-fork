#!/usr/bin/env bash
# 
# Copyright (c) Advanced Micro Devices, Inc.
# All rights reserved.
# 

set -e
set -x

tool=$1

OUTPUT=${tool}_output
SAVESPACE=/myworkspace/

mkdir "$OUTPUT"

case "$tool" in

rpd)
	python3 ./rocmProfileData/tools/rpd2tracing.py trace.rpd trace.json
	mv trace.rpd trace.json "$OUTPUT"
	cp -vLR --preserve=all "$OUTPUT" "$SAVESPACE"
	;;

rocprof)
	mv results* "$OUTPUT"
	cp -vLR --preserve=all "$OUTPUT" "$SAVESPACE"
	;;

esac

chmod -R a+rw "${SAVESPACE}/${OUTPUT}"
