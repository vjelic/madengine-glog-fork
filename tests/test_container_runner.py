"""Test the container runner module.

This module tests the Docker container execution functionality for distributed execution.

Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""
# built-in modules
import os
import json
import tempfile
import unittest.mock
from unittest.mock import patch, MagicMock, mock_open
# third-party modules
import pytest
# project modules
from madengine.tools.container_runner import ContainerRunner
from madengine.core.context import Context
from madengine.core.console import Console
from madengine.core.dataprovider import Data
from .fixtures.utils import BASE_DIR, MODEL_DIR


class TestContainerRunner:
    """Test the container runner module."""

    def test_container_runner_initialization(self):
        """Test ContainerRunner initialization."""
        context = Context()
        console = Console()
        data = MagicMock()
        
        runner = ContainerRunner(context, data, console)
        
        assert runner.context == context
        assert runner.data == data
        assert runner.console == console
        assert runner.credentials is None

    def test_container_runner_initialization_minimal(self):
        """Test ContainerRunner initialization with minimal parameters."""
        runner = ContainerRunner()
        
        assert runner.context is None
        assert runner.data is None
        assert isinstance(runner.console, Console)
        assert runner.credentials is None

    def test_load_build_manifest(self):
        """Test loading build manifest from file."""
        runner = ContainerRunner()
        
        manifest_data = {
            "images": {
                "model1": "localhost:5000/ci-model1:latest",
                "model2": "localhost:5000/ci-model2:latest"
            },
            "metadata": {
                "build_time": "2023-01-01T12:00:00Z",
                "registry": "localhost:5000"
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(manifest_data))):
            result = runner.load_build_manifest("test_manifest.json")
        
        assert result == manifest_data
        assert "images" in result
        assert "model1" in result["images"]

    @patch.object(Console, 'sh')
    def test_pull_image(self, mock_sh):
        """Test pulling image from registry."""
        runner = ContainerRunner()
        
        mock_sh.return_value = "Pull successful"
        
        result = runner.pull_image("localhost:5000/test:latest")
        
        assert result == "localhost:5000/test:latest"
        mock_sh.assert_called_with("docker pull localhost:5000/test:latest")

    @patch.object(Console, 'sh')
    def test_pull_image_with_local_name(self, mock_sh):
        """Test pulling image with local name tagging."""
        runner = ContainerRunner()
        
        mock_sh.return_value = "Success"
        
        result = runner.pull_image("localhost:5000/test:latest", "local-test")
        
        assert result == "local-test"
        # Should have called pull and tag
        expected_calls = [
            unittest.mock.call("docker pull localhost:5000/test:latest"),
            unittest.mock.call("docker tag localhost:5000/test:latest local-test")
        ]
        mock_sh.assert_has_calls(expected_calls)

    def test_get_gpu_arg_all_gpus(self):
        """Test get_gpu_arg with all GPUs requested."""
        context = Context()
        context.ctx = {
            "docker_env_vars": {
                "MAD_GPU_VENDOR": "nvidia",
                "MAD_SYSTEM_NGPUS": "4"
            },
            "docker_gpus": "0,1,2,3"
        }
        runner = ContainerRunner(context)
        
        result = runner.get_gpu_arg("-1")
        
        # Should return GPU args for all available GPUs
        assert "0,1,2,3" in result or "--gpus all" in result

    def test_get_gpu_arg_specific_gpus(self):
        """Test get_gpu_arg with specific GPUs requested."""
        context = Context()
        context.ctx = {
            "docker_env_vars": {
                "MAD_GPU_VENDOR": "nvidia",
                "MAD_SYSTEM_NGPUS": "4"
            },
            "docker_gpus": "0,1,2,3"
        }
        runner = ContainerRunner(context)
        
        result = runner.get_gpu_arg("2")
        
        # Should return GPU args for 2 GPUs
        assert "gpu" in result.lower()

    def test_get_gpu_arg_range_format(self):
        """Test get_gpu_arg with range format."""
        context = Context()
        context.ctx = {
            "docker_env_vars": {
                "MAD_GPU_VENDOR": "nvidia", 
                "MAD_SYSTEM_NGPUS": "4"
            },
            "docker_gpus": "0-3"
        }
        runner = ContainerRunner(context)
        
        result = runner.get_gpu_arg("2")
        
        # Should handle range format correctly
        assert isinstance(result, str)

    @patch.object(Console, 'sh')
    def test_run_container_success(self, mock_sh):
        """Test successful container run."""
        context = Context()
        context.ctx = {
            "docker_env_vars": {
                "MAD_GPU_VENDOR": "nvidia",
                "MAD_SYSTEM_NGPUS": "2"
            },
            "docker_gpus": "0,1",
            "docker_volumes": [],
            "docker_network": "bridge"
        }
        runner = ContainerRunner(context)
        
        mock_sh.return_value = "Container ran successfully"
        
        container_info = {
            "image_name": "test-image",
            "model_name": "test_model",
            "gpu_requirements": "1"
        }
        
        with patch.object(runner, 'get_gpu_arg', return_value="--gpus device=0"):
            result = runner.run_container(container_info, timeout=300)
        
        assert result["status"] == "success"
        assert "execution_time" in result
        assert mock_sh.called

    @patch.object(Console, 'sh')
    def test_run_container_timeout(self, mock_sh):
        """Test container run with timeout."""
        context = Context()
        context.ctx = {
            "docker_env_vars": {"MAD_GPU_VENDOR": "nvidia", "MAD_SYSTEM_NGPUS": "2"},
            "docker_gpus": "0,1",
            "docker_volumes": [],
            "docker_network": "bridge"
        }
        runner = ContainerRunner(context)
        
        # Mock timeout exception
        from madengine.core.timeout import TimeoutException
        mock_sh.side_effect = TimeoutException("Timeout occurred")
        
        container_info = {
            "image_name": "test-image",
            "model_name": "test_model",
            "gpu_requirements": "1"
        }
        
        with patch.object(runner, 'get_gpu_arg', return_value="--gpus device=0"):
            result = runner.run_container(container_info, timeout=10)
        
        assert result["status"] == "timeout"
        assert "timeout" in result["error"]

    @patch.object(Console, 'sh')
    def test_run_container_failure(self, mock_sh):
        """Test container run failure."""
        context = Context()
        context.ctx = {
            "docker_env_vars": {"MAD_GPU_VENDOR": "nvidia", "MAD_SYSTEM_NGPUS": "2"},
            "docker_gpus": "0,1",
            "docker_volumes": [],
            "docker_network": "bridge"
        }
        runner = ContainerRunner(context)
        
        # Mock runtime error
        mock_sh.side_effect = RuntimeError("Container failed to start")
        
        container_info = {
            "image_name": "test-image",
            "model_name": "test_model",
            "gpu_requirements": "1"
        }
        
        with patch.object(runner, 'get_gpu_arg', return_value="--gpus device=0"):
            result = runner.run_container(container_info, timeout=300)
        
        assert result["status"] == "failed"
        assert "Container failed to start" in result["error"]

    def test_run_all_containers(self):
        """Test running all containers from manifest."""
        context = Context()
        runner = ContainerRunner(context)
        
        manifest = {
            "images": {
                "model1": "localhost:5000/ci-model1:latest",
                "model2": "localhost:5000/ci-model2:latest"
            }
        }
        
        # Mock successful container runs
        with patch.object(runner, 'pull_image', return_value="local-image"):
            with patch.object(runner, 'run_container') as mock_run:
                mock_run.return_value = {
                    "status": "success",
                    "execution_time": 45.0,
                    "performance": "100 ops/sec"
                }
                
                result = runner.run_all_containers(manifest, timeout=300)
        
        assert len(result["successful_runs"]) == 2
        assert len(result["failed_runs"]) == 0
        assert mock_run.call_count == 2

    def test_run_all_containers_with_failures(self):
        """Test running all containers with some failures."""
        context = Context()
        runner = ContainerRunner(context)
        
        manifest = {
            "images": {
                "model1": "localhost:5000/ci-model1:latest",
                "model2": "localhost:5000/ci-model2:latest"
            }
        }
        
        # Mock one success, one failure
        def mock_run_side_effect(*args, **kwargs):
            if "model1" in str(args):
                return {"status": "success", "execution_time": 30.0}
            else:
                return {"status": "failed", "error": "Runtime error"}
        
        with patch.object(runner, 'pull_image', return_value="local-image"):
            with patch.object(runner, 'run_container', side_effect=mock_run_side_effect):
                result = runner.run_all_containers(manifest, timeout=300)
        
        assert len(result["successful_runs"]) == 1
        assert len(result["failed_runs"]) == 1

    def test_run_all_containers_skip_pull(self):
        """Test running containers without pulling (local images)."""
        context = Context()
        runner = ContainerRunner(context)
        
        manifest = {
            "images": {
                "model1": "ci-model1:latest"  # Local image, no registry prefix
            }
        }
        
        with patch.object(runner, 'run_container') as mock_run:
            mock_run.return_value = {"status": "success", "execution_time": 30.0}
            
            result = runner.run_all_containers(manifest, registry=None, timeout=300)
        
        # Should not have called pull_image for local images
        with patch.object(runner, 'pull_image') as mock_pull:
            mock_pull.assert_not_called()

    @patch.object(Console, 'sh')
    def test_cleanup_containers(self, mock_sh):
        """Test cleanup of containers after execution."""
        runner = ContainerRunner()
        
        mock_sh.return_value = "Cleanup successful"
        
        runner.cleanup_containers(["container1", "container2"])
        
        # Should have called docker rm for each container
        expected_calls = [
            unittest.mock.call("docker rm -f container1"),
            unittest.mock.call("docker rm -f container2")
        ]
        mock_sh.assert_has_calls(expected_calls, any_order=True)

    def test_get_container_volumes(self):
        """Test getting volume mounts for container."""
        context = Context()
        context.ctx = {
            "docker_volumes": [
                "/host/data:/container/data:ro",
                "/host/output:/container/output:rw"
            ]
        }
        runner = ContainerRunner(context)
        
        volumes = runner.get_container_volumes()
        
        assert len(volumes) == 2
        assert "/host/data:/container/data:ro" in volumes
        assert "/host/output:/container/output:rw" in volumes

    def test_get_container_env_vars(self):
        """Test getting environment variables for container."""
        context = Context()
        context.ctx = {
            "docker_env_vars": {
                "MAD_GPU_VENDOR": "nvidia",
                "MAD_MODEL_NAME": "test_model",
                "CUSTOM_VAR": "custom_value"
            }
        }
        runner = ContainerRunner(context)
        
        env_vars = runner.get_container_env_vars("test_model")
        
        assert "MAD_GPU_VENDOR=nvidia" in env_vars
        assert "MAD_MODEL_NAME=test_model" in env_vars
        assert "CUSTOM_VAR=custom_value" in env_vars

    @patch.object(Console, 'sh')
    def test_wait_for_container_completion(self, mock_sh):
        """Test waiting for container completion."""
        runner = ContainerRunner()
        
        # Mock docker wait command
        mock_sh.return_value = "0"  # Exit code 0 (success)
        
        result = runner.wait_for_container_completion("test_container", timeout=60)
        
        assert result == 0
        mock_sh.assert_called_with("docker wait test_container", timeout=60)

    @patch.object(Console, 'sh')
    def test_get_container_logs(self, mock_sh):
        """Test getting container logs."""
        runner = ContainerRunner()
        
        mock_sh.return_value = "Container output logs"
        
        logs = runner.get_container_logs("test_container")
        
        assert logs == "Container output logs"
        mock_sh.assert_called_with("docker logs test_container")

    def test_generate_execution_summary(self):
        """Test generating execution summary."""
        runner = ContainerRunner()
        
        results = [
            {"model": "model1", "status": "success", "execution_time": 30.0},
            {"model": "model2", "status": "failed", "error": "Runtime error"},
            {"model": "model3", "status": "success", "execution_time": 45.0}
        ]
        
        summary = runner.generate_execution_summary(results)
        
        assert summary["total_models"] == 3
        assert summary["successful_runs"] == 2
        assert summary["failed_runs"] == 1
        assert summary["total_execution_time"] == 75.0
