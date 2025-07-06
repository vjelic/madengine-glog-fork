"""Utility functions for tests.

Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""

# built-in modules
import os
import sys
import json
import subprocess
import shutil
import re
import pytest
from unittest.mock import MagicMock
import re
import json

# project modules
from madengine.core.console import Console
from madengine.core.context import Context


MODEL_DIR = "tests/fixtures/dummy"
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(1, BASE_DIR)
print(f'BASE DIR:: {BASE_DIR}')


def detect_gpu_availability() -> dict:
    """Detect GPU availability and type on the current machine.
    
    Returns:
        dict: GPU detection results with keys:
            - has_gpu: bool - True if any GPU is detected
            - gpu_vendor: str - "AMD", "NVIDIA", "INTEL", or "NONE"
            - gpu_count: int - Number of GPUs detected
            - is_cpu_only: bool - True if no GPU is detected
            - detection_error: str or None - Error message if detection fails
    """
    detection_result = {
        "has_gpu": False,
        "gpu_vendor": "NONE",
        "gpu_count": 0,
        "is_cpu_only": True,
        "detection_error": None
    }
    
    try:
        console = Console(live_output=False)  # Disable live output for detection
        
        # Try to detect GPU vendor using the same logic as Context.get_gpu_vendor()
        gpu_vendor_cmd = ('bash -c \'if [[ -f /usr/bin/nvidia-smi ]] && $(/usr/bin/nvidia-smi > /dev/null 2>&1); '
                         'then echo "NVIDIA"; elif [[ -f /opt/rocm/bin/rocm-smi ]]; then echo "AMD"; '
                         'elif [[ -f /usr/local/bin/rocm-smi ]]; then echo "AMD"; '
                         'else echo "Unable to detect GPU vendor"; fi || true\'')
        
        gpu_vendor_result = console.sh(gpu_vendor_cmd)
        
        if "Unable to detect GPU vendor" not in gpu_vendor_result:
            detection_result["has_gpu"] = True
            detection_result["is_cpu_only"] = False
            detection_result["gpu_vendor"] = gpu_vendor_result.strip()
            
            # Try to get GPU count
            try:
                gpu_count = get_num_gpus()
                detection_result["gpu_count"] = gpu_count
            except Exception as e:
                # If we can't get the count, assume at least 1 GPU if vendor is detected
                detection_result["gpu_count"] = 1 if detection_result["has_gpu"] else 0
                detection_result["detection_error"] = f"GPU count detection failed: {str(e)}"
        
    except Exception as e:
        detection_result["detection_error"] = f"GPU detection failed: {str(e)}"
    
    return detection_result


def is_gpu_available() -> bool:
    """Check if any GPU is available on the current machine.
    
    Returns:
        bool: True if GPU is available, False if CPU-only machine
    """
    return detect_gpu_availability()["has_gpu"]


def is_cpu_only_machine() -> bool:
    """Check if this is a CPU-only machine (no GPU detected).
    
    Returns:
        bool: True if no GPU is detected, False if GPU is available
    """
    return detect_gpu_availability()["is_cpu_only"]


def get_detected_gpu_vendor() -> str:
    """Get the detected GPU vendor or 'NONE' if no GPU.
    
    Returns:
        str: "AMD", "NVIDIA", "INTEL", or "NONE"
    """
    return detect_gpu_availability()["gpu_vendor"]


def requires_gpu(gpu_count: int = 1, gpu_vendor: str = None):
    """Pytest decorator to skip tests that require GPU on CPU-only machines.
    
    Args:
        gpu_count: Minimum number of GPUs required (default: 1)
        gpu_vendor: Required GPU vendor ("AMD", "NVIDIA", "INTEL") or None for any
    
    Returns:
        pytest.mark.skipif decorator
    """
    detection = detect_gpu_availability()
    
    skip_conditions = []
    reasons = []
    
    # Check if GPU is available
    if detection["is_cpu_only"]:
        skip_conditions.append(True)
        reasons.append("test requires GPU but running on CPU-only machine")
    
    # Check GPU count requirement
    elif detection["gpu_count"] < gpu_count:
        skip_conditions.append(True)
        reasons.append(f"test requires {gpu_count} GPUs but only {detection['gpu_count']} detected")
    
    # Check GPU vendor requirement
    elif gpu_vendor and detection["gpu_vendor"] != gpu_vendor:
        skip_conditions.append(True)
        reasons.append(f"test requires {gpu_vendor} GPU but {detection['gpu_vendor']} detected")
    
    # If no skip conditions, don't skip
    if not skip_conditions:
        skip_conditions.append(False)
        reasons.append("GPU requirements satisfied")
    
    return pytest.mark.skipif(
        any(skip_conditions), 
        reason="; ".join(reasons)
    )


def skip_on_cpu_only(reason: str = "test requires GPU functionality"):
    """Simple decorator to skip tests on CPU-only machines.
    
    Args:
        reason: Custom reason for skipping
    
    Returns:
        pytest.mark.skipif decorator
    """
    return pytest.mark.skipif(
        is_cpu_only_machine(),
        reason=reason
    )


@pytest.fixture
def global_data():
    return {"console": Console(live_output=True)}


@pytest.fixture()
def clean_test_temp_files(request):

    yield

    for filename in request.param:
        file_path = os.path.join(BASE_DIR, filename)
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)


def is_nvidia() -> bool:
    """Check if the GPU is NVIDIA or not.

    Returns:
        bool: True if NVIDIA GPU is present, False otherwise.
    """
    context = Context()
    if context.ctx["gpu_vendor"] == "NVIDIA":
        return True
    else:
        return False


def get_gpu_nodeid_map() -> dict:
    """Get the GPU node id map.

    Returns:
        dict: GPU node id map.
    """
    gpu_map = {}
    nvidia = is_nvidia()
    console = Console(live_output=True)
    command = "nvidia-smi --list-gpus"
    if not nvidia:
        rocm_version = console.sh("hipconfig --version")
        rocm_version = float(".".join(rocm_version.split(".")[:2]))
        command = (
            "rocm-smi --showuniqueid" if rocm_version < 6.1 else "rocm-smi --showhw"
        )
    output = console.sh(command)
    lines = output.split("\n")

    for line in lines:
        if nvidia:
            gpu_id = int(line.split(":")[0].split()[1])
            unique_id = line.split(":")[2].split(")")[0].strip()
            gpu_map[unique_id] = gpu_id
        else:
            if rocm_version < 6.1:
                if "Unique ID:" in line:
                    gpu_id = int(line.split(":")[0].split("[")[1].split("]")[0])
                    unique_id = line.split(":")[2].strip()
                    gpu_map[unique_id] = gpu_id
            else:
                if re.match(r"\d+\s+\d+", line):
                    gpu_id = int(line.split()[0])
                    node_id = line.split()[1]
                    gpu_map[node_id] = gpu_id
    return gpu_map


def get_num_gpus() -> int:
    """Get the number of GPUs present.

    Returns:
        int: Number of GPUs present.
    """
    gpu_map = get_gpu_nodeid_map()
    return len(gpu_map)


def get_num_cpus() -> int:
    """Get the number of CPUs present.

    Returns:
        int: Number of CPUs present.
    """
    console = Console(live_output=True)
    return int(console.sh("lscpu | grep \"^CPU(s):\" | awk '{print $2}'"))


def generate_additional_context_for_machine() -> dict:
    """Generate appropriate additional context based on detected machine capabilities.
    
    Returns:
        dict: Additional context with gpu_vendor and guest_os suitable for current machine
    """
    detection = detect_gpu_availability()
    
    if detection["is_cpu_only"]:
        # On CPU-only machines, use defaults suitable for build-only operations
        return {
            "gpu_vendor": "AMD",  # Default for build-only nodes
            "guest_os": "UBUNTU"  # Default OS
        }
    else:
        # On GPU machines, use detected GPU vendor
        return {
            "gpu_vendor": detection["gpu_vendor"],
            "guest_os": "UBUNTU"  # We could detect this too if needed
        }


def generate_additional_context_json() -> str:
    """Generate JSON string of additional context for current machine.
    
    Returns:
        str: JSON string representation of additional context
    """
    return json.dumps(generate_additional_context_for_machine())


def create_mock_args_with_auto_context(**kwargs) -> MagicMock:
    """Create mock args with automatically generated additional context.
    
    Args:
        **kwargs: Additional attributes to set on the mock args
        
    Returns:
        MagicMock: Mock args object with auto-generated additional context
    """
    mock_args = MagicMock()
    
    # Set auto-generated context
    mock_args.additional_context = generate_additional_context_json()
    mock_args.additional_context_file = None
    
    # Set any additional attributes
    for key, value in kwargs.items():
        setattr(mock_args, key, value)
    
    return mock_args
