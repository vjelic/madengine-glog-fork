#!/usr/bin/env python3
"""
Docker Image Builder Module for MADEngine

This module handles the Docker image building phase separately from execution,
enabling distributed workflows where images are built on a central host
and then distributed to remote nodes for execution.
"""

import os
import time
import json
import typing
from contextlib import redirect_stdout, redirect_stderr
from madengine.core.console import Console
from madengine.core.context import Context
from madengine.utils.ops import PythonicTee


class DockerBuilder:
    """Class responsible for building Docker images for models."""
    
    def __init__(self, context: Context, console: Console = None, live_output: bool = False):
        """Initialize the Docker Builder.
        
        Args:
            context: The MADEngine context
            console: Optional console instance
            live_output: Whether to show live output
        """
        self.context = context
        self.console = console or Console(live_output=live_output)
        self.live_output = live_output
        self.built_images = {}  # Track built images
        self.built_models = {}  # Track built models
        
    def get_context_path(self, info: typing.Dict) -> str:
        """Get the context path for Docker build.
        
        Args:
            info: The model info dict.
            
        Returns:
            str: The context path.
        """
        if "dockercontext" in info and info["dockercontext"] != "":
            return info["dockercontext"]
        else:
            return "./docker"
    
    def get_build_arg(self, run_build_arg: typing.Dict = {}) -> str:
        """Get the build arguments.
        
        Args:
            run_build_arg: The run build arguments.
            
        Returns:
            str: The build arguments.
        """
        if not run_build_arg and "docker_build_arg" not in self.context.ctx:
            return ""

        build_args = ""
        for build_arg in self.context.ctx["docker_build_arg"].keys():
            build_args += (
                "--build-arg "
                + build_arg
                + "='"
                + self.context.ctx["docker_build_arg"][build_arg]
                + "' "
            )

        if run_build_arg:
            for key, value in run_build_arg.items():
                build_args += "--build-arg " + key + "='" + value + "' "

        return build_args
    
    def build_image(self, model_info: typing.Dict, dockerfile: str, 
                   credentials: typing.Dict = None, clean_cache: bool = False,
                   phase_suffix: str = "") -> typing.Dict:
        """Build a Docker image for the given model.
        
        Args:
            model_info: The model information dictionary
            dockerfile: Path to the Dockerfile
            credentials: Optional credentials dictionary
            clean_cache: Whether to use --no-cache
            phase_suffix: Suffix for log file name (e.g., ".build" or "")
            
        Returns:
            dict: Build information including image name, build duration, etc.
        """
        print(f"Building Docker image for model {model_info['name']} from {dockerfile}")
        print(f"Building Docker image...")
        
        # Generate image name
        image_docker_name = (
            model_info["name"].replace("/", "_").lower()
            + "_"
            + os.path.basename(dockerfile).replace(".Dockerfile", "")
        )
        
        docker_image = "ci-" + image_docker_name
        
        # Create log file for this build
        cur_docker_file_basename = os.path.basename(dockerfile).replace(".Dockerfile", "")
        log_file_path = (
            model_info["name"].replace("/", "_")
            + "_"
            + cur_docker_file_basename
            + phase_suffix
            + ".live.log"
        )
        # Replace / with _ in log file path (already done above, but keeping for safety)
        log_file_path = log_file_path.replace("/", "_")
        
        print(f"Processing Dockerfile: {dockerfile}")
        print(f"Build log will be written to: {log_file_path}")
        
        # Get docker context
        docker_context = self.get_context_path(model_info)
        
        # Prepare build args
        run_build_arg = {}
        if "cred" in model_info and model_info["cred"] != "" and credentials:
            if model_info["cred"] not in credentials:
                raise RuntimeError(
                    f"Credentials({model_info['cred']}) not found for model {model_info['name']}"
                )
            # Add cred to build args
            for key_cred, value_cred in credentials[model_info["cred"]].items():
                run_build_arg[model_info["cred"] + "_" + key_cred.upper()] = value_cred
        
        build_args = self.get_build_arg(run_build_arg)
        
        use_cache_str = "--no-cache" if clean_cache else ""
        
        # Build the image with logging
        build_start_time = time.time()
        
        build_command = (
            f"docker build {use_cache_str} --network=host "
            f"-t {docker_image} --pull -f {dockerfile} "
            f"{build_args} {docker_context}"
        )
        
        # Execute build with log redirection
        with open(log_file_path, mode="w", buffering=1) as outlog:
            with redirect_stdout(PythonicTee(outlog, self.live_output)), redirect_stderr(PythonicTee(outlog, self.live_output)):
                print(f"Executing: {build_command}")
                self.console.sh(build_command, timeout=None)
                
                build_duration = time.time() - build_start_time
                
                print(f"Build Duration: {build_duration} seconds")
                print(f"MAD_CONTAINER_IMAGE is {docker_image}")
                
                # Get base docker info
                base_docker = ""
                if (
                    "docker_build_arg" in self.context.ctx
                    and "BASE_DOCKER" in self.context.ctx["docker_build_arg"]
                ):
                    base_docker = self.context.ctx["docker_build_arg"]["BASE_DOCKER"]
                else:
                    base_docker = self.console.sh(
                        f"grep '^ARG BASE_DOCKER=' {dockerfile} | sed -E 's/ARG BASE_DOCKER=//g'"
                    )
                
                print(f"BASE DOCKER is {base_docker}")
                
                # Get docker SHA
                docker_sha = ""
                try:
                    docker_sha = self.console.sh(
                        f"docker manifest inspect {base_docker} | grep digest | head -n 1 | cut -d \\\" -f 4"
                    )
                    print(f"BASE DOCKER SHA is {docker_sha}")
                except Exception as e:
                    print(f"Warning: Could not get docker SHA: {e}")
        
        build_info = {
            "docker_image": docker_image,
            "dockerfile": dockerfile,
            "base_docker": base_docker,
            "docker_sha": docker_sha,
            "build_duration": build_duration,
            "build_command": build_command,
            "log_file": log_file_path
        }
        
        # Store built image info
        self.built_images[docker_image] = build_info
        
        # Store model info linked to the built image
        self.built_models[docker_image] = model_info
        
        print(f"Successfully built image: {docker_image}")
        
        return build_info
    
    def login_to_registry(self, registry: str, credentials: typing.Dict = None) -> None:
        """Login to a Docker registry.
        
        Args:
            registry: Registry URL (e.g., "localhost:5000", "docker.io", or empty for DockerHub)
            credentials: Optional credentials dictionary containing username/password
        """
        if not credentials:
            print("No credentials provided for registry login")
            return
            
        # Check if registry credentials are available
        registry_key = registry if registry else "dockerhub"
        
        if registry_key not in credentials:
            print(f"No credentials found for registry: {registry_key}")
            return
            
        creds = credentials[registry_key]
        
        if "username" not in creds or "password" not in creds:
            print(f"Invalid credentials format for registry: {registry_key}")
            return
            
        # Perform docker login
        login_command = f"echo '{creds['password']}' | docker login"
        
        if registry and registry != "docker.io":
            login_command += f" {registry}"
            
        login_command += f" --username {creds['username']} --password-stdin"
        
        try:
            self.console.sh(login_command, secret=True)
            print(f"Successfully logged in to registry: {registry or 'DockerHub'}")
        except Exception as e:
            print(f"Failed to login to registry {registry}: {e}")
            raise

    def push_image(self, docker_image: str, registry: str = None, credentials: typing.Dict = None) -> str:
        """Push the built image to a registry.
        
        Args:
            docker_image: The local docker image name
            registry: Optional registry URL (e.g., "localhost:5000", "docker.io", or empty for DockerHub)
            credentials: Optional credentials dictionary for registry authentication
            
        Returns:
            str: The full registry image name
        """
        if not registry:
            print(f"No registry specified, image remains local: {docker_image}")
            return docker_image
            
        # Login to registry if credentials are provided
        if credentials:
            self.login_to_registry(registry, credentials)
        
        # Determine registry image name based on registry type
        if registry.lower() in ["docker.io", "dockerhub"]:
            # For DockerHub, use format: username/imagename or just imagename
            # If credentials provided, prepend username
            if credentials and "dockerhub" in credentials and "username" in credentials["dockerhub"]:
                registry_image = f"{credentials['dockerhub']['username']}/{docker_image}"
            else:
                registry_image = docker_image
        else:
            # For other registries (local, AWS ECR, etc.), use format: registry/imagename
            registry_image = f"{registry}/{docker_image}"
        
        try:
            # Tag the image if different from local name
            if registry_image != docker_image:
                tag_command = f"docker tag {docker_image} {registry_image}"
                print(f"Tagging image: {tag_command}")
                self.console.sh(tag_command)
            
            # Push the image
            push_command = f"docker push {registry_image}"
            print(f"Pushing image: {push_command}")
            self.console.sh(push_command)
            
            print(f"Successfully pushed image to registry: {registry_image}")
            return registry_image
            
        except Exception as e:
            print(f"Failed to push image {docker_image} to registry {registry}: {e}")
            raise
    
    def export_build_manifest(self, output_file: str = "build_manifest.json", registry: str = None) -> None:
        """Export build information to a manifest file.
        
        Args:
            output_file: Path to output manifest file
            registry: Registry used for building (added to manifest metadata)
        """
        manifest = {
            "built_images": self.built_images,
            "built_models": self.built_models,  # Include model information
            "context": {
                "docker_env_vars": self.context.ctx.get("docker_env_vars", {}),
                "docker_mounts": self.context.ctx.get("docker_mounts", {}),
                "docker_build_arg": self.context.ctx.get("docker_build_arg", {})
            }
        }
        
        # Add registry information to manifest metadata if provided
        if registry:
            manifest["registry"] = registry
        
        with open(output_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"Build manifest exported to: {output_file}")
    
    def build_all_models(self, models: typing.List[typing.Dict], 
                        credentials: typing.Dict = None, 
                        clean_cache: bool = False,
                        registry: str = None,
                        phase_suffix: str = "") -> typing.Dict:
        """Build images for all models.
        
        Args:
            models: List of model information dictionaries
            credentials: Optional credentials dictionary
            clean_cache: Whether to use --no-cache
            registry: Optional registry to push images to
            phase_suffix: Suffix for log file name (e.g., ".build" or "")
            
        Returns:
            dict: Summary of all built images
        """
        print(f"Building Docker images for {len(models)} models...")
        
        build_summary = {
            "successful_builds": [],
            "failed_builds": [],
            "total_build_time": 0
        }
        
        for model_info in models:
            try:
                # Find dockerfiles for this model
                all_dockerfiles = self.console.sh(
                    f"ls {model_info['dockerfile']}.*"
                ).split("\n")
                
                dockerfiles = {}
                for cur_docker_file in all_dockerfiles:
                    # Get context of dockerfile
                    dockerfiles[cur_docker_file] = self.console.sh(
                        f"head -n5 {cur_docker_file} | grep '# CONTEXT ' | sed 's/# CONTEXT //g'"
                    )
                
                # Filter dockerfiles based on context
                dockerfiles = self.context.filter(dockerfiles)
                
                if not dockerfiles:
                    print(f"No matching dockerfiles found for model {model_info['name']}")
                    continue
                
                # Build each dockerfile
                for dockerfile in dockerfiles.keys():
                    try:
                        build_info = self.build_image(
                            model_info, dockerfile, credentials, clean_cache, phase_suffix
                        )
                        
                        # Push to registry if specified
                        if registry:
                            registry_image = self.push_image(
                                build_info["docker_image"], registry, credentials
                            )
                            build_info["registry_image"] = registry_image
                        
                        build_summary["successful_builds"].append({
                            "model": model_info["name"],
                            "dockerfile": dockerfile,
                            "build_info": build_info
                        })
                        
                        build_summary["total_build_time"] += build_info["build_duration"]
                        
                    except Exception as e:
                        print(f"Failed to build {dockerfile} for model {model_info['name']}: {e}")
                        build_summary["failed_builds"].append({
                            "model": model_info["name"],
                            "dockerfile": dockerfile,
                            "error": str(e)
                        })
                        
            except Exception as e:
                print(f"Error processing model {model_info['name']}: {e}")
                build_summary["failed_builds"].append({
                    "model": model_info["name"],
                    "error": str(e)
                })
        
        print(f"\nBuild Summary:")
        print(f"  Successful builds: {len(build_summary['successful_builds'])}")
        print(f"  Failed builds: {len(build_summary['failed_builds'])}")
        print(f"  Total build time: {build_summary['total_build_time']:.2f} seconds")
        
        return build_summary
