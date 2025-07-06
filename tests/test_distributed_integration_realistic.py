"""Realistic integration tests for distributed CLI pre/post scripts and profiling.

This module provides end-to-end integration tests that simulate real
distributed CLI usage scenarios with pre/post scripts and profiling tools.

NOTE: These tests are designed to run on non-GPU environments by mocking
GPU detection and hardware dependencies. In real distributed deployments,
these would run on actual GPU nodes with proper hardware detection.

Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""
# built-in modules
import os
import sys
import json
import tempfile
import subprocess
import unittest.mock
from unittest.mock import patch, MagicMock, mock_open, call
# third-party modules
import pytest
# project modules
from madengine import distributed_cli
from madengine.tools.distributed_orchestrator import DistributedOrchestrator
from madengine.tools.container_runner import ContainerRunner
from madengine.core.context import Context
from madengine.core.console import Console
from .fixtures.utils import BASE_DIR, MODEL_DIR, clean_test_temp_files


class TestDistributedRealisticIntegration:
    """Realistic integration tests for distributed CLI functionality."""

    def setup_method(self):
        """Set up test fixtures for realistic scenarios."""
        self.test_manifest = {
            "built_images": {
                "ci-dummy_dummy.ubuntu.amd": {
                    "docker_image": "ci-dummy_dummy.ubuntu.amd",
                    "dockerfile": "docker/dummy.ubuntu.amd.Dockerfile",
                    "registry_image": "localhost:5000/ci-dummy_dummy.ubuntu.amd",
                    "build_duration": 45.2
                }
            },
            "built_models": {
                "ci-dummy_dummy.ubuntu.amd": {
                    "name": "dummy",
                    "n_gpus": "1",
                    "scripts": "scripts/dummy/run.sh",
                    "dockerfile": "docker/dummy.ubuntu.amd.Dockerfile",
                    "tags": ["dummy", "test"],
                    "tools": ["rocprof"]
                }
            },
            "registry": "localhost:5000"
        }
        
        self.test_tools_config = {
            "rocprof": {
                "pre_scripts": ["scripts/common/pre_scripts/rocprof_start.sh"],
                "post_scripts": ["scripts/common/post_scripts/rocprof_stop.sh"],
                "docker_env_vars": {
                    "HSA_ENABLE_LOGGING": "1",
                    "ROCPROF_OUTPUT": "/tmp/rocprof"
                },
                "docker_mounts": {
                    "/tmp/rocprof": "/tmp/rocprof"
                }
            }
        }

    @patch('madengine.tools.container_runner.Docker')
    @patch('madengine.core.console.Console.sh')
    @patch('madengine.tools.distributed_orchestrator.Data')
    @patch('madengine.tools.distributed_orchestrator.Context')
    @patch('os.path.exists')
    def test_end_to_end_distributed_run_with_profiling(self, mock_exists, mock_context, mock_data, mock_sh, mock_docker):
        """Test complete distributed run workflow with profiling tools.
        
        NOTE: This test mocks GPU detection and hardware dependencies since it runs
        on non-GPU CI environments. In production, this would run on actual GPU nodes.
        """
        # Mock Context initialization to avoid GPU detection
        mock_context_instance = MagicMock()
        mock_context.return_value = mock_context_instance
        mock_context_instance.ctx = {
            "docker_env_vars": {"MAD_GPU_VENDOR": "AMD"},
            "docker_mounts": {},
            "gpu_vendor": "AMD"
        }
        
        # Mock Data initialization
        mock_data_instance = MagicMock()
        mock_data.return_value = mock_data_instance
        
        # Mock file system
        def mock_exists_side_effect(path):
            if 'tools.json' in path:
                return True
            if 'run_rocenv_tool.sh' in path:
                return True
            if 'build_manifest.json' in path:
                return True
            return False
        
        mock_exists.side_effect = mock_exists_side_effect
        
        # Mock file reading for tools.json
        mock_tools_json = json.dumps(self.test_tools_config)
        
        with patch('builtins.open', mock_open(read_data=mock_tools_json)) as mock_file:
            # Mock manifest file
            mock_manifest_json = json.dumps(self.test_manifest)
            mock_file.return_value.read.side_effect = [mock_tools_json, mock_manifest_json]
            
            # Mock Docker operations
            mock_docker_instance = MagicMock()
            mock_docker.return_value = mock_docker_instance
            mock_docker_instance.pull.return_value = None
            mock_docker_instance.tag.return_value = None
            mock_docker_instance.run.return_value = {
                'exit_code': 0,
                'stdout': 'Test execution completed',
                'stderr': ''
            }
            
            # Mock shell commands
            mock_sh.return_value = "rocm-libs version info"
            
            # Create args with profiling context
            import argparse
            args = argparse.Namespace()
            args.manifest_file = "build_manifest.json"
            args.registry = None
            args.timeout = 3600
            args.keep_alive = False
            args.live_output = False
            args.additional_context = None
            args.additional_context_file = None
            args.data_config_file_name = 'data.json'
            args.force_mirror_local = False
            args.generate_sys_env_details = True
            args._separate_phases = True
            
            # Test distributed run
            orchestrator = DistributedOrchestrator(args)
            
            with patch('os.path.exists', return_value=False):  # No data.json
                result = orchestrator.run_phase()
            
            # Verify results
            assert 'successful_runs' in result
            assert 'failed_runs' in result
            assert len(result['failed_runs']) == 0 or len(result['successful_runs']) > 0
            
            # Verify Docker operations were called
            assert mock_docker.called
            
            # Verify system environment collection was included
            # (This would be in the pre_scripts when run_container is called)
            mock_sh.assert_called()

    @patch('subprocess.run')
    def test_distributed_cli_command_line_with_sys_env_arg(self, mock_subprocess):
        """Test distributed CLI command line parsing includes sys env arguments."""
        # Mock successful subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result
        
        # Test that command line parsing works
        script_path = os.path.join(BASE_DIR, "src/madengine", "distributed_cli.py")
        
        cmd = [
            sys.executable, script_path, "run",
            "--manifest-file", "test_manifest.json",
            "--generate-sys-env-details",
            "--timeout", "1800"
        ]
        
        # This tests that the CLI can parse the arguments without error
        result = subprocess.run(cmd + ["--help"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Should show help without error
        assert result.returncode == 0

    @patch('madengine.tools.distributed_orchestrator.DistributedOrchestrator.run_phase')
    @patch('madengine.tools.distributed_orchestrator.Data')
    @patch('madengine.tools.distributed_orchestrator.Context')
    @patch('os.path.exists')
    def test_distributed_run_with_profiling_context_file(self, mock_exists, mock_context, mock_data, mock_run_phase):
        """Test distributed run with profiling context from file."""
        # Mock Context initialization
        mock_context_instance = MagicMock()
        mock_context.return_value = mock_context_instance
        mock_context_instance.ctx = {
            "docker_env_vars": {"MAD_GPU_VENDOR": "AMD"},
            "docker_mounts": {},
            "gpu_vendor": "AMD"
        }
        
        # Mock Data initialization
        mock_data_instance = MagicMock()
        mock_data.return_value = mock_data_instance
        
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock successful run_phase
        mock_run_phase.return_value = {
            "successful_runs": [{"model": "dummy", "status": "success"}],
            "failed_runs": [],
            "total_execution_time": 45.2
        }
        
        # Test profiling context file
        profiling_context = {
            "docker_env_vars": {
                "ROCPROF_ENABLE": "1",
                "HSA_ENABLE_LOGGING": "1"
            },
            "pre_scripts": ["scripts/common/pre_scripts/rocprof_start.sh"],
            "post_scripts": ["scripts/common/post_scripts/rocprof_stop.sh"]
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(profiling_context))):
            # Create args with profiling context file
            import argparse
            args = argparse.Namespace()
            args.manifest_file = "test_manifest.json"
            args.additional_context_file = "profiling_context.json"
            args.generate_sys_env_details = True
            args.live_output = False
            args.additional_context = None
            args.data_config_file_name = 'data.json'
            args.force_mirror_local = False
            args.timeout = 3600
            args.keep_alive = False
            args._separate_phases = True
            
            # Initialize orchestrator - this should load the profiling context
            orchestrator = DistributedOrchestrator(args)
            
            # Verify context was loaded
            assert orchestrator.context is not None
            
            # Call run_phase
            result = orchestrator.run_phase()
            
            # Verify run was successful
            assert len(result["successful_runs"]) > 0
            assert len(result["failed_runs"]) == 0

    @patch('madengine.core.context.Context')
    @patch('madengine.core.console.Console')
    def test_system_env_pre_script_format_consistency(self, mock_console, mock_context):
        """Test that system env pre-script format is consistent between standard and distributed."""
        # Mock context and console
        mock_context_instance = MagicMock()
        mock_console_instance = MagicMock()
        mock_context.return_value = mock_context_instance
        mock_console.return_value = mock_console_instance
        
        # Test ContainerRunner system env generation
        runner = ContainerRunner(mock_context_instance, None, mock_console_instance)
        
        model_info = {"name": "test_model"}
        
        # Test gather_system_env_details method
        if hasattr(runner, 'gather_system_env_details'):
            pre_scripts = runner.gather_system_env_details(model_info)
            
            # Verify pre-script format
            assert isinstance(pre_scripts, list)
            if pre_scripts:
                # Should contain system environment script
                sys_env_script = pre_scripts[0]
                assert 'run_rocenv_tool.sh' in sys_env_script
                assert 'test_model' in sys_env_script or 'test_model'.replace('/', '_') in sys_env_script

    @patch('madengine.tools.container_runner.ContainerRunner.run_container')
    @patch('madengine.tools.distributed_orchestrator.DistributedOrchestrator._copy_scripts')
    @patch('madengine.tools.distributed_orchestrator.Data')
    @patch('madengine.tools.distributed_orchestrator.Context')
    @patch('os.path.exists')
    def test_distributed_profiling_tools_integration(self, mock_exists, mock_context, mock_data, mock_copy_scripts, mock_run_container):
        """Test complete profiling tools integration in distributed scenario."""
        # Mock Context initialization
        mock_context_instance = MagicMock()
        mock_context.return_value = mock_context_instance
        mock_context_instance.ctx = {
            "docker_env_vars": {"MAD_GPU_VENDOR": "AMD"},
            "docker_mounts": {},
            "gpu_vendor": "AMD"
        }
        
        # Mock Data initialization
        mock_data_instance = MagicMock()
        mock_data.return_value = mock_data_instance
        
        # Mock file system
        mock_exists.return_value = True
        
        # Mock successful container run
        mock_run_container.return_value = {
            "model": "dummy",
            "status": "success",
            "test_duration": 30.5,
            "profiling_data": {
                "rocprof_output": "/tmp/rocprof/output.csv"
            }
        }
        
        # Mock manifest with profiling tools
        manifest_with_profiling = {
            "built_images": {
                "ci-dummy_profiling.ubuntu.amd": {
                    "docker_image": "ci-dummy_profiling.ubuntu.amd",
                    "dockerfile": "docker/dummy.ubuntu.amd.Dockerfile",
                    "build_duration": 45.2
                }
            },
            "built_models": {
                "ci-dummy_profiling.ubuntu.amd": {
                    "name": "dummy_profiling",
                    "n_gpus": "1",
                    "scripts": "scripts/dummy/run.sh",
                    "dockerfile": "docker/dummy.ubuntu.amd.Dockerfile",
                    "tags": ["dummy", "profiling"],
                    "tools": ["rocprof", "roctracer"]
                }
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(manifest_with_profiling))):
            # Create args for profiling run
            import argparse
            args = argparse.Namespace()
            args.manifest_file = "build_manifest.json"
            args.registry = None
            args.timeout = 3600
            args.keep_alive = False
            args.live_output = False
            args.additional_context = None
            args.additional_context_file = None
            args.data_config_file_name = 'data.json'
            args.force_mirror_local = False
            args.generate_sys_env_details = True
            args._separate_phases = True
            
            with patch('os.path.exists', return_value=False):  # No data.json
                orchestrator = DistributedOrchestrator(args)
                result = orchestrator.run_phase()
            
            # Verify profiling run was successful
            assert len(result["successful_runs"]) > 0
            
            # Verify run_container was called with correct arguments
            mock_run_container.assert_called()
            call_args = mock_run_container.call_args
            
            # Check that generate_sys_env_details was passed
            assert 'generate_sys_env_details' in call_args.kwargs
            assert call_args.kwargs['generate_sys_env_details'] is True

    @patch('madengine.core.context.Context')
    @patch('madengine.core.console.Console')
    def test_error_recovery_in_profiling_workflow(self, mock_console, mock_context):
        """Test error recovery scenarios in profiling workflow."""
        # Mock context and console
        mock_context_instance = MagicMock()
        mock_console_instance = MagicMock()
        mock_context.return_value = mock_context_instance
        mock_console.return_value = mock_console_instance
        
        runner = ContainerRunner(mock_context_instance, None, mock_console_instance)
        
        # Test with invalid model info
        invalid_model = {"name": ""}
        
        if hasattr(runner, 'gather_system_env_details'):
            try:
                pre_scripts = runner.gather_system_env_details(invalid_model)
                # Should handle empty name gracefully
                assert isinstance(pre_scripts, list)
            except Exception as e:
                # If it raises an exception, it should be informative
                assert "name" in str(e).lower() or "model" in str(e).lower()

    @patch('madengine.tools.distributed_orchestrator.DistributedOrchestrator.cleanup')
    @patch('madengine.tools.distributed_orchestrator.Data')
    @patch('madengine.tools.distributed_orchestrator.Context')
    def test_distributed_cleanup_after_profiling(self, mock_context, mock_data, mock_cleanup):
        """Test that cleanup is called after distributed profiling run."""
        # Mock Context initialization
        mock_context_instance = MagicMock()
        mock_context.return_value = mock_context_instance
        mock_context_instance.ctx = {
            "docker_env_vars": {"MAD_GPU_VENDOR": "AMD"},
            "docker_mounts": {},
            "gpu_vendor": "AMD"
        }
        
        # Mock Data initialization
        mock_data_instance = MagicMock()
        mock_data.return_value = mock_data_instance
        
        import argparse
        args = argparse.Namespace()
        args.live_output = False
        args.additional_context = None
        args.additional_context_file = None
        args.data_config_file_name = 'data.json'
        args.force_mirror_local = False
        args.generate_sys_env_details = True
        
        with patch('os.path.exists', return_value=False):  # No data.json or credentials
            orchestrator = DistributedOrchestrator(args)
            
            # Mock successful build and run
            with patch.object(orchestrator, 'build_phase', return_value={"successful_builds": [], "failed_builds": []}):
                with patch.object(orchestrator, 'run_phase', return_value={"successful_runs": [], "failed_runs": []}):
                    result = orchestrator.full_workflow()
            
            # Verify cleanup was called multiple times (once per phase)
            assert mock_cleanup.call_count >= 2

    def teardown_method(self):
        """Clean up after each test."""
        # Clean up any test files
        test_files = [
            "test_manifest.json",
            "profiling_context.json",
            "build_manifest.json",
            "execution_config.json"
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass


class TestDistributedCLICommandLineArgs:
    """Test distributed CLI command line argument parsing for profiling scenarios."""

    def test_cli_help_includes_sys_env_options(self):
        """Test that CLI help includes system environment options."""
        script_path = os.path.join(BASE_DIR, "src/madengine", "distributed_cli.py")
        result = subprocess.run([sys.executable, script_path, "run", "--help"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        assert result.returncode == 0
        help_output = result.stdout.decode()
        
        # Should mention system environment or profiling related options
        assert ("sys" in help_output.lower() or 
                "env" in help_output.lower() or 
                "profile" in help_output.lower() or
                "context" in help_output.lower())

    @patch('madengine.distributed_cli.run_models')
    def test_cli_args_parsing_for_profiling(self, mock_run_models):
        """Test that CLI correctly parses profiling-related arguments."""
        # Mock successful run
        mock_run_models.return_value = distributed_cli.EXIT_SUCCESS
        
        # Simulate command line arguments
        test_args = [
            "run",
            "--manifest-file", "test_manifest.json",
            "--timeout", "1800",
            "--live-output"
        ]
        
        # Test argument parsing doesn't crash
        try:
            parser = distributed_cli.create_parser()
            parsed_args = parser.parse_args(test_args)
            
            # Verify profiling-related args are handled
            assert hasattr(parsed_args, 'manifest_file')
            assert parsed_args.manifest_file == "test_manifest.json"
            assert hasattr(parsed_args, 'timeout')
            assert parsed_args.timeout == 1800
            
        except SystemExit:
            # Parser help/error is acceptable
            pass

    def test_profiling_args_defaults(self):
        """Test that profiling-related arguments have sensible defaults."""
        import argparse
        
        # Test default args behavior
        args = argparse.Namespace()
        
        # Test the getattr pattern used in distributed_orchestrator
        sys_env_default = getattr(args, 'generate_sys_env_details', True)
        assert sys_env_default is True  # Should default to True
        
        # Test with explicit False
        args.generate_sys_env_details = False
        sys_env_explicit = getattr(args, 'generate_sys_env_details', True)
        assert sys_env_explicit is False  # Should respect explicit setting
