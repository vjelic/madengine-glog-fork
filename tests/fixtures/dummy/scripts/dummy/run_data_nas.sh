#!/bin/bash
# 
# Copyright (c) Advanced Micro Devices, Inc.
# All rights reserved.
# 

if [ -z ${MAD_DATAHOME+x} ]; then
    echo "MAD_DATAHOME is NOT set"
    exit 1
else
    echo "MAD_DATAHOME is set"
fi

mountCode=`mount | grep "${MAD_DATAHOME}"`

if [ -z "$mountCode" ]; then
    echo "${MAD_DATAHOME} is NOT mounted"
    exit 1
else
    echo "${MAD_DATAHOME} is mounted"
    echo "performance: $RANDOM samples_per_second"
fi


