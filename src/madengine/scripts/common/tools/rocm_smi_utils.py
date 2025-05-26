#!/usr/bin/env python3
"""Module to get GPU information using rocm_smi

This module contains the class ProfUtils to get GPU information using rocm_smi.
This script should keep the API of pynvml_utils with rocm_smi_utils

Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""
import sys

sys.path.append("/opt/rocm/libexec/rocm_smi/")
try:
    import rocm_smi
    from rsmiBindings import *
except ImportError:
    raise ImportError("Could not import /opt/rocm/libexec/rocm_smi/rocm_smi.py")


class prof_utils:
    """Class to get GPU information using rocm_smi"""
    def __init__(self, mode) -> None:
        self.rocm6 = False
        try:
            self.rocmsmi = initRsmiBindings(silent=False)
            if rocm_smi.driverInitialized() is True:
                ret_init = self.rocmsmi.rsmi_init(0)
                if ret_init != 0:
                    raise ValueError('ROCm SMI returned %s (the expected value is 0)', ret_init)
                    exit(ret_init)
            else:
                raise ImportError('Driver not initialized (amdgpu not found in modules)')
                exit(0)
            self.rocm6 = True
        except:
            rocm_smi.initializeRsmi()

    def getPower(self, device):
        if self.rocm6:
            """ Return the current (also known as instant)
            socket power of a given device

            @param device: DRM device identifier
            @param silent=Turn on to silence error output
            (you plan to handle manually). Default is off.
            """
            power = c_uint32()
            ret = self.rocmsmi.rsmi_dev_power_ave_get(device, 0, byref(power))
            if rocm_smi.rsmi_ret_ok(ret, device, 'get_socket_power', False):
                return str(power.value / 1000000)
            return 'N/A'
        else:
            return rocm_smi.getPower(device)

    def listDevices(self):
        if self.rocm6:
            """ Returns a list of GPU devices """
            numberOfDevices = c_uint32(0)
            ret = self.rocmsmi.rsmi_num_monitor_devices(byref(numberOfDevices))
            if rocm_smi.rsmi_ret_ok(ret, metric='get_num_monitbyrefor_devices'):
                deviceList = list(range(numberOfDevices.value))
                return deviceList
            else:
                exit(ret)
        else:
            return rocm_smi.listDevices()

    def getMemInfo(self, device):
        if self.rocm6:
            memoryUse = c_uint64()
            ret = self.rocmsmi.rsmi_dev_memory_busy_percent_get(device, byref(memoryUse))
            if rocm_smi.rsmi_ret_ok(ret, device, '% memory use'):
                return memoryUse.value
        else:
            (memUsed, memTotal) = rocm_smi.getMemInfo(device, "vram")
            return round(float(memUsed)/float(memTotal) * 100, 2)

    def checkIfSecondaryDie(self, device):
        if self.rocm6:
            """ Checks if GCD(die) is the secondary die in a MCM.
            MI200 device specific feature check.
            The secondary dies lacks power management features.

            @param device: The device to check
            """
            energy_count = c_uint64()
            counter_resoution = c_float()
            timestamp = c_uint64()

            # secondary die can be determined by checking if energy counter == 0
            ret = self.rocmsmi.rsmi_dev_energy_count_get(device, byref(energy_count), byref(counter_resoution), byref(timestamp))
            if (rocm_smi.rsmi_ret_ok(ret, None, 'energy_count_secondary_die_check', silent=False)) and (energy_count.value == 0):
                return True
            return False
        else:
            return rocm_smi.checkIfSecondaryDie(device)
