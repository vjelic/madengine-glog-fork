"""Test the Docker builder module.

This module tests the Docker image building functionality for distributed execution.

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
from madengine.tools.docker_builder import DockerBuilder
from madengine.core.context import Context
from madengine.core.console import Console
from .fixtures.utils import BASE_DIR, MODEL_DIR


class TestDockerBuilder:
    """Test the Docker builder module."""

    def test_docker_builder_initialization(self):
        """Test DockerBuilder initialization."""
        context = Context()
        console = Console()
        
        builder = DockerBuilder(context, console)
        
        assert builder.context == context
        assert builder.console == console
        assert builder.built_images == {}

    def test_docker_builder_initialization_without_console(self):
        """Test DockerBuilder initialization without console."""
        context = Context()
        
        builder = DockerBuilder(context)
        
        assert builder.context == context
        assert isinstance(builder.console, Console)
        assert builder.built_images == {}

    def test_get_context_path_with_dockercontext(self):
        """Test get_context_path when dockercontext is specified."""
        context = Context()
        builder = DockerBuilder(context)
        
        info = {"dockercontext": "/custom/context"}
        result = builder.get_context_path(info)
        
        assert result == "/custom/context"

    def test_get_context_path_without_dockercontext(self):
        """Test get_context_path when dockercontext is not specified."""
        context = Context()
        builder = DockerBuilder(context)
        
        info = {}
        result = builder.get_context_path(info)
        
        assert result == "./docker"

    def test_get_context_path_with_empty_dockercontext(self):
        """Test get_context_path when dockercontext is empty."""
        context = Context()
        builder = DockerBuilder(context)
        
        info = {"dockercontext": ""}
        result = builder.get_context_path(info)
        
        assert result == "./docker"

    def test_get_build_arg_no_args(self):
        """Test get_build_arg with no build arguments."""
        context = Context()
        builder = DockerBuilder(context)
        
        result = builder.get_build_arg()
        
        assert result == ""

    def test_get_build_arg_with_context_args(self):
        """Test get_build_arg with context build arguments."""
        context = Context()
        context.ctx = {
            "docker_build_arg": {
                "ARG1": "value1",
                "ARG2": "value2"
            }
        }
        builder = DockerBuilder(context)
        
        result = builder.get_build_arg()
        
        assert "--build-arg ARG1='value1'" in result
        assert "--build-arg ARG2='value2'" in result

    def test_get_build_arg_with_run_args(self):
        """Test get_build_arg with runtime build arguments."""
        context = Context()
        builder = DockerBuilder(context)
        
        run_build_arg = {"RUNTIME_ARG": "runtime_value"}
        result = builder.get_build_arg(run_build_arg)
        
        assert "--build-arg RUNTIME_ARG='runtime_value'" in result

    def test_get_build_arg_with_both_args(self):
        """Test get_build_arg with both context and runtime arguments."""
        context = Context()
        context.ctx = {
            "docker_build_arg": {
                "CONTEXT_ARG": "context_value"
            }
        }
        builder = DockerBuilder(context)
        
        run_build_arg = {"RUNTIME_ARG": "runtime_value"}
        result = builder.get_build_arg(run_build_arg)
        
        assert "--build-arg CONTEXT_ARG='context_value'" in result
        assert "--build-arg RUNTIME_ARG='runtime_value'" in result

    @patch.object(Console, 'sh')
    def test_build_image_success(self, mock_sh):
        """Test successful Docker image build."""
        context = Context()
        console = Console()
        builder = DockerBuilder(context, console)
        
        # Mock the console.sh calls
        mock_sh.return_value = "Build successful"
        
        model_info = {
            "name": "test/model",
            "dockercontext": "./docker"
        }
        dockerfile = "./docker/Dockerfile"
        
        with patch.object(builder, 'get_build_arg', return_value=""):
            result = builder.build_image(model_info, dockerfile)
        
        # Verify the image name generation
        expected_image_name = "ci-test_model_dockerfile"
        assert result["image_name"] == expected_image_name
        assert result["status"] == "success"
        assert "build_duration" in result

    @patch.object(Console, 'sh')
    def test_build_image_with_registry_push(self, mock_sh):
        """Test Docker image build with registry push."""
        context = Context()
        console = Console()
        builder = DockerBuilder(context, console)
        
        # Mock successful build and push
        mock_sh.return_value = "Success"
        
        model_info = {"name": "test_model"}
        dockerfile = "./docker/Dockerfile"
        registry = "localhost:5000"
        
        with patch.object(builder, 'get_build_arg', return_value=""):
            with patch.object(builder, 'get_context_path', return_value="./docker"):
                result = builder.build_image(model_info, dockerfile, registry=registry)
        
        # Should have called docker build and docker push
        build_calls = [call for call in mock_sh.call_args_list if 'docker build' in str(call)]
        push_calls = [call for call in mock_sh.call_args_list if 'docker push' in str(call)]
        
        assert len(build_calls) >= 1
        assert len(push_calls) >= 1
        assert result["registry_image"] is not None

    @patch.object(Console, 'sh')
    def test_build_image_failure(self, mock_sh):
        """Test Docker image build failure."""
        context = Context()
        console = Console()
        builder = DockerBuilder(context, console)
        
        # Mock build failure
        mock_sh.side_effect = RuntimeError("Build failed")
        
        model_info = {"name": "test_model"}
        dockerfile = "./docker/Dockerfile"
        
        with patch.object(builder, 'get_build_arg', return_value=""):
            with patch.object(builder, 'get_context_path', return_value="./docker"):
                result = builder.build_image(model_info, dockerfile)
        
        assert result["status"] == "failed"
        assert "error" in result

    def test_build_all_models(self):
        """Test building all models."""
        context = Context()
        builder = DockerBuilder(context)
        
        models = [
            {"name": "model1", "dockerfile": ["./docker/Dockerfile1"]},
            {"name": "model2", "dockerfile": ["./docker/Dockerfile2"]}
        ]
        
        # Mock successful builds
        with patch.object(builder, 'build_image') as mock_build:
            mock_build.return_value = {
                "status": "success",
                "image_name": "test_image",
                "build_duration": 30.0
            }
            
            result = builder.build_all_models(models)
        
        assert len(result["successful_builds"]) == 2
        assert len(result["failed_builds"]) == 0
        assert mock_build.call_count == 2

    def test_build_all_models_with_failures(self):
        """Test building all models with some failures."""
        context = Context()
        builder = DockerBuilder(context)
        
        models = [
            {"name": "model1", "dockerfile": ["./docker/Dockerfile1"]},
            {"name": "model2", "dockerfile": ["./docker/Dockerfile2"]}
        ]
        
        # Mock one success, one failure
        def mock_build_side_effect(*args, **kwargs):
            if "model1" in str(args):
                return {"status": "success", "image_name": "model1_image"}
            else:
                return {"status": "failed", "error": "Build failed"}
        
        with patch.object(builder, 'build_image', side_effect=mock_build_side_effect):
            result = builder.build_all_models(models)
        
        assert len(result["successful_builds"]) == 1
        assert len(result["failed_builds"]) == 1

    def test_export_build_manifest(self):
        """Test exporting build manifest."""
        context = Context()
        builder = DockerBuilder(context)
        
        # Set up some built images
        builder.built_images = {
            "model1": {
                "image_name": "ci-model1",
                "registry_image": "localhost:5000/ci-model1:latest",
                "dockerfile": "./docker/Dockerfile"
            }
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                builder.export_build_manifest("manifest.json")
        
        # Verify file was opened and JSON was written
        mock_file.assert_called_once_with("manifest.json", 'w')
        mock_json_dump.assert_called_once()

    def test_get_build_manifest(self):
        """Test getting build manifest."""
        context = Context()
        builder = DockerBuilder(context)
        
        # Set up some built images
        builder.built_images = {
            "model1": {"image_name": "ci-model1"},
            "model2": {"image_name": "ci-model2"}
        }
        
        manifest = builder.get_build_manifest()
        
        assert "images" in manifest
        assert "metadata" in manifest
        assert len(manifest["images"]) == 2
        assert "model1" in manifest["images"]
        assert "model2" in manifest["images"]

    @patch.object(Console, 'sh')
    def test_build_image_with_credentials(self, mock_sh):
        """Test Docker image build with credentials."""
        context = Context()
        builder = DockerBuilder(context)
        
        mock_sh.return_value = "Success"
        
        model_info = {"name": "test_model"}
        dockerfile = "./docker/Dockerfile"
        credentials = {
            "registry": "myregistry.com",
            "username": "testuser",
            "password": "testpass"
        }
        
        with patch.object(builder, 'get_build_arg', return_value=""):
            with patch.object(builder, 'get_context_path', return_value="./docker"):
                result = builder.build_image(model_info, dockerfile, credentials=credentials)
        
        # Should have called docker login
        login_calls = [call for call in mock_sh.call_args_list if 'docker login' in str(call)]
        assert len(login_calls) >= 1

    def test_clean_cache_option(self):
        """Test clean cache option in build."""
        context = Context()
        builder = DockerBuilder(context)
        
        model_info = {"name": "test_model"}
        dockerfile = "./docker/Dockerfile"
        
        with patch.object(builder.console, 'sh') as mock_sh:
            with patch.object(builder, 'get_build_arg', return_value=""):
                with patch.object(builder, 'get_context_path', return_value="./docker"):
                    builder.build_image(model_info, dockerfile, clean_cache=True)
        
        # Verify --no-cache was used
        build_calls = [call for call in mock_sh.call_args_list if 'docker build' in str(call)]
        assert any('--no-cache' in str(call) for call in build_calls)
