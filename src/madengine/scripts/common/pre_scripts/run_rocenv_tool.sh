#!/usr/bin/env bash
# 
# Copyright (c) Advanced Micro Devices, Inc.
# All rights reserved.
# 

OUTPUT_FILE_NAME=${1:-"sys_config_info"}
cp -r ../scripts/common/pre_scripts/rocEnvTool .
cd rocEnvTool
python3 rocenv_tool.py --lite --dump-csv --print-csv --output-name $OUTPUT_FILE_NAME
out_dir="."$OUTPUT_FILE_NAME
out_csv=$OUTPUT_FILE_NAME".csv"
cp -r $out_dir ../../
cp $out_csv ../../
cd ..
