"""Test the mad module.

Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""
# built-in modules
import os
import sys
import subprocess
import typing
# third-party modules
import pytest
# project modules
from madengine import mad


class TestMad:
    """Test the mad module.
    
    test_run_model: run python3 mad.py --help
    """
    def test_mad_cli(self):
        # Construct the path to the script
        script_path = os.path.join(os.path.dirname(__file__), "../src/madengine", "mad.py")
        # Run the script with arguments using subprocess.run
        result = subprocess.run([sys.executable, script_path, "--help"], stdout=subprocess.PIPE)
        print(result.stdout.decode("utf-8"))
        assert result.returncode == 0

    def test_mad_run_cli(self):
        # Construct the path to the script
        script_path = os.path.join(os.path.dirname(__file__), "../src/madengine", "mad.py")
        # Run the script with arguments using subprocess.run
        result = subprocess.run([sys.executable, script_path, "run", "--help"], stdout=subprocess.PIPE)
        print(result.stdout.decode("utf-8"))
        assert result.returncode == 0

    def test_mad_report_cli(self):
        # Construct the path to the script
        script_path = os.path.join(os.path.dirname(__file__), "../src/madengine", "mad.py")
        # Run the script with arguments using subprocess.run
        result = subprocess.run([sys.executable, script_path, "report", "--help"], stdout=subprocess.PIPE)
        print(result.stdout.decode("utf-8"))
        assert result.returncode == 0

    def test_mad_database_cli(self):
        # Construct the path to the script
        script_path = os.path.join(os.path.dirname(__file__), "../src/madengine", "mad.py")
        # Run the script with arguments using subprocess.run
        result = subprocess.run([sys.executable, script_path, "database", "--help"], stdout=subprocess.PIPE)
        print(result.stdout.decode("utf-8"))
        assert result.returncode == 0

    def test_mad_discover_cli(self):
        # Construct the path to the script
        script_path = os.path.join(os.path.dirname(__file__), "../src/madengine", "mad.py")
        # Run the script with arguments using subprocess.run
        result = subprocess.run([sys.executable, script_path, "discover", "--help"], stdout=subprocess.PIPE)
        print(result.stdout.decode("utf-8"))
        assert result.returncode == 0        

    def test_mad_version_cli(self):
        # Construct the path to the script
        script_path = os.path.join(os.path.dirname(__file__), "../src/madengine", "mad.py")
        # Run the script with arguments using subprocess.run
        result = subprocess.run([sys.executable, script_path, "--version"], stdout=subprocess.PIPE)
        print(result.stdout.decode("utf-8"))
        assert result.returncode == 0
