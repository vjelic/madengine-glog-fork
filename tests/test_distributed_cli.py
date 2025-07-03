"""Test the distributed CLI module.

This module tests the distributed command-line interface functionality.

Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""
# built-in modules
import os
import sys
import json
import tempfile
import subprocess
import unittest.mock
from unittest.mock import patch, MagicMock
# third-party modules
import pytest
# project modules
from madengine.tools import distributed_cli
from madengine.tools.distributed_orchestrator import DistributedOrchestrator
from .fixtures.utils import BASE_DIR, MODEL_DIR


class TestDistributedCLI:
    """Test the distributed CLI module."""

    def test_distributed_cli_help(self):
        """Test the distributed CLI --help command."""
        script_path = os.path.join(BASE_DIR, "src/madengine/tools", "distributed_cli.py")
        result = subprocess.run([sys.executable, script_path, "--help"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode == 0
        assert b"MADEngine Distributed" in result.stdout

    def test_build_command_help(self):
        """Test the build command --help."""
        script_path = os.path.join(BASE_DIR, "src/madengine/tools", "distributed_cli.py")
        result = subprocess.run([sys.executable, script_path, "build", "--help"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode == 0
        assert b"build" in result.stdout

    def test_run_command_help(self):
        """Test the run command --help."""
        script_path = os.path.join(BASE_DIR, "src/madengine/tools", "distributed_cli.py")
        result = subprocess.run([sys.executable, script_path, "run", "--help"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode == 0
        assert b"run" in result.stdout

    def test_full_command_help(self):
        """Test the full command --help."""
        script_path = os.path.join(BASE_DIR, "src/madengine/tools", "distributed_cli.py")
        result = subprocess.run([sys.executable, script_path, "full", "--help"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode == 0
        assert b"full" in result.stdout

    @patch('madengine.tools.distributed_cli.DistributedOrchestrator')
    def test_build_command_function(self, mock_orchestrator):
        """Test the build_command function."""
        # Mock args
        mock_args = MagicMock()
        mock_args.registry = "localhost:5000"
        mock_args.clean_cache = True
        mock_args.manifest_output = "test_manifest.json"
        mock_args.summary_output = "test_summary.json"

        # Mock orchestrator instance and build phase
        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance
        mock_instance.build_phase.return_value = {
            "successful_builds": ["model1", "model2"],
            "failed_builds": []
        }

        # Test build command
        result = distributed_cli.build_command(mock_args)
        
        # Verify orchestrator was called correctly
        mock_orchestrator.assert_called_once_with(mock_args)
        mock_instance.build_phase.assert_called_once_with(
            registry="localhost:5000",
            clean_cache=True,
            manifest_output="test_manifest.json"
        )
        
        # Should return True for successful builds
        assert result is True

    @patch('madengine.tools.distributed_cli.DistributedOrchestrator')
    def test_build_command_with_failures(self, mock_orchestrator):
        """Test the build_command function with build failures."""
        mock_args = MagicMock()
        mock_args.registry = None
        mock_args.clean_cache = False
        mock_args.manifest_output = "manifest.json"
        mock_args.summary_output = None

        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance
        mock_instance.build_phase.return_value = {
            "successful_builds": ["model1"],
            "failed_builds": ["model2"]
        }

        result = distributed_cli.build_command(mock_args)
        
        # Should return False due to failures
        assert result is False

    @patch('madengine.tools.distributed_cli.DistributedOrchestrator')
    def test_run_command_function(self, mock_orchestrator):
        """Test the run_command function."""
        mock_args = MagicMock()
        mock_args.manifest_file = "manifest.json"
        mock_args.registry = "localhost:5000"
        mock_args.timeout = 3600
        mock_args.keep_alive = False
        mock_args.summary_output = None

        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance
        mock_instance.run_phase.return_value = {
            "successful_runs": ["model1", "model2"],
            "failed_runs": []
        }

        result = distributed_cli.run_command(mock_args)
        
        mock_orchestrator.assert_called_once_with(mock_args)
        mock_instance.run_phase.assert_called_once_with(
            manifest_file="manifest.json",
            registry="localhost:5000",
            timeout=3600,
            keep_alive=False
        )
        
        assert result is True

    @patch('madengine.tools.distributed_cli.DistributedOrchestrator')
    def test_full_command_function(self, mock_orchestrator):
        """Test the full_command function."""
        mock_args = MagicMock()
        mock_args.registry = "localhost:5000"
        mock_args.clean_cache = True
        mock_args.timeout = 1800
        mock_args.keep_alive = True
        mock_args.summary_output = None

        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance
        mock_instance.full_workflow.return_value = {
            "overall_success": True,
            "build_summary": {"successful_builds": ["model1"], "failed_builds": []},
            "execution_summary": {"successful_runs": ["model1"], "failed_runs": []}
        }

        result = distributed_cli.full_command(mock_args)
        
        mock_orchestrator.assert_called_once_with(mock_args)
        mock_instance.full_workflow.assert_called_once_with(
            registry="localhost:5000",
            clean_cache=True,
            timeout=1800,
            keep_alive=True
        )
        
        assert result is True

    @patch('madengine.tools.distributed_cli.create_ansible_playbook')
    def test_generate_ansible_command(self, mock_create_ansible):
        """Test the generate_ansible_command function."""
        mock_args = MagicMock()
        mock_args.manifest_file = "manifest.json"
        mock_args.execution_config = "config.json"
        mock_args.output = "playbook.yml"

        result = distributed_cli.generate_ansible_command(mock_args)
        
        mock_create_ansible.assert_called_once_with(
            manifest_file="manifest.json",
            execution_config="config.json",
            playbook_file="playbook.yml"
        )
        
        assert result is True

    @patch('madengine.tools.distributed_cli.create_kubernetes_manifests')
    def test_generate_k8s_command(self, mock_create_k8s):
        """Test the generate_k8s_command function."""
        mock_args = MagicMock()
        mock_args.manifest_file = "manifest.json"
        mock_args.execution_config = "config.json"
        mock_args.namespace = "madengine-test"

        result = distributed_cli.generate_k8s_command(mock_args)
        
        mock_create_k8s.assert_called_once_with(
            manifest_file="manifest.json",
            execution_config="config.json",
            namespace="madengine-test"
        )
        
        assert result is True

    @patch('madengine.tools.distributed_cli.DistributedOrchestrator')
    def test_export_config_command(self, mock_orchestrator):
        """Test the export_config_command function."""
        mock_args = MagicMock()
        mock_args.output = "config.json"

        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance

        result = distributed_cli.export_config_command(mock_args)
        
        mock_orchestrator.assert_called_once_with(mock_args)
        # Note: The actual implementation would need to call export_config method
        assert result is True
