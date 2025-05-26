#!/usr/bin/env bash
# 
# Copyright (c) Advanced Micro Devices, Inc.
# All rights reserved.
# 

set -e
set -x

os=''
if [ -n "$(command -v apt)" ]; then
	os=ubuntu
elif [ -n "$(command -v yum)" ]; then
	os=centos
else
	echo 'Unable to detect Host OS in pre_script'
	exit 1
fi

tool=$1

case "$tool" in

rpd)
	if [ "$os" == 'ubuntu' ]; then
		sudo apt update
		sudo apt install -y sqlite3 libsqlite3-dev libfmt-dev
	elif [ "$os" == 'centos' ]; then
		sudo yum install -y libsqlite3x-devel.x86_64 fmt-devel
	else
		echo "Unable to detect Host OS in trace pre-script"
	fi
	git clone https://streamhsa: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@github.com/ROCmSoftwarePlatform/rocmProfileData
	cd ./rocmProfileData
	make && make install
	cd ..
	;;

esac
