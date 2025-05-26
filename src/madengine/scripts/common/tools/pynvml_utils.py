#!/usr/bin/env python3
"""Module to get GPU information using pynvml

This module contains the class ProfUtils to get GPU information using pynvml.
This script should keep the API of pynvml_utils with rocm_smi_utils

Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""
# built-in modules
import typing

# third-party modules
import pynvml


class prof_utils:
    """Class to get GPU information using pynvml"""

    def __init__(self, mode) -> None:
        pynvml.nvmlInit()
        self.deviceCount = pynvml.nvmlDeviceGetCount()
        self.handles = []
        self.deviceList = []
        for i in range(self.deviceCount):
            self.deviceList.append(i)
            self.handles.append(pynvml.nvmlDeviceGetHandleByIndex(i))

    def getPower(self, device):
        return round(
            float(pynvml.nvmlDeviceGetPowerUsage(self.handles[device])) / 1000, 2
        )

    def listDevices(self):
        return self.deviceList

    def getMemInfo(self, device):
        info = pynvml.nvmlDeviceGetMemoryInfo(self.handles[device])
        return round(float(info.used) / float(info.total) * 100, 2)


# class prof_utils:
#     def __init__(self, mode) -> None:
#         self.handles = []
#         self.deviceList = []

#     def getPower(self, device):
#         return 0
    
#     def listDevices(self):
#         return self.deviceList 

#     def getMemInfo(self, device):
#         return 0
