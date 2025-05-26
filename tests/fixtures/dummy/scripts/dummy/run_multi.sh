#!/bin/bash
# 
# Copyright (c) Advanced Micro Devices, Inc.
# All rights reserved.
# 

echo "model,performance,latency,metric,temperature
1,$RANDOM,$RANDOM,samples_per_sec,$RANDOM
2,$RANDOM,$RANDOM,samples_per_sec,$RANDOM
3,$RANDOM,$RANDOM,samples_per_sec,$RANDOM
4,$RANDOM,$RANDOM,samples_per_sec,$RANDOM" >>perf_dummy.csv

cp perf_dummy.csv ../
