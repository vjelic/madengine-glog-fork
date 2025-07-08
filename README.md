# madengine

A comprehensive AI model automation and benchmarking toolkit designed to work seamlessly with the [MAD (Model Automation and Dashboarding)](https://github.com/ROCm/MAD) package ecosystem.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://docker.com)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [MAD Model Discovery](#mad-model-discovery)
- [Command Line Interface](#command-line-interface)
- [Distributed Execution](#distributed-execution)
- [Configuration](#configuration)
- [Advanced Usage](#advanced-usage)
- [Deployment Scenarios](#deployment-scenarios)
- [Contributing](#contributing)
- [License](#license)

## Overview

madengine is an enterprise-grade AI model automation and dashboarding command-line tool designed to run Large Language Models (LLMs) and Deep Learning models locally or in distributed environments. It provides a modern, production-ready solution for AI model benchmarking with comprehensive CI/CD integration capabilities.

### Key Capabilities

- **Reliable Model Execution**: Run AI models reliably across supported platforms with quality assurance
- **Distributed Architecture**: Split build and execution phases for optimal resource utilization
- **Comprehensive Automation**: Minimalistic, out-of-the-box solution for hardware and software stack validation
- **Real-time Metrics**: Audience-relevant AI model performance tracking with intuitive presentation
- **Enterprise Integration**: Best practices for internal projects and external open-source model handling
- **MAD Ecosystem Integration**: Seamless integration with the MAD package for model discovery and management

### MAD Package Integration

madengine is designed to work within the **MAD (Model Automation and Dashboarding) package**, which serves as a comprehensive model hub containing:

- Docker configurations and container definitions
- Model scripts and automation workflows  
- Adopted AI models with standardized interfaces
- Data providers and credential management
- Build tools and environment configurations

## Features

🚀 **Modern CLI Interface**: Built with Typer and Rich for excellent user experience  
📊 **Rich Terminal Output**: Progress bars, tables, panels with syntax highlighting  
🎯 **Intelligent Workflows**: Automatic detection of build-only vs. full workflow operations  
🔄 **Distributed Execution**: Separate build and run phases for scalable deployments  
🐳 **Docker Integration**: Containerized model execution with GPU support  
📋 **Model Discovery**: Automatic discovery from MAD package structure  
🏷️ **Flexible Tagging**: Hierarchical model selection with parameterization  
⚡ **Performance Optimized**: Built for speed and resource efficiency  
🔐 **Credential Management**: Centralized authentication for repositories and registries  
📈 **Monitoring & Reporting**: Comprehensive metrics collection and analysis  
🌐 **Multi-Platform**: Support for AMD ROCm, NVIDIA CUDA, and Intel architectures  
🔧 **Extensible**: Plugin architecture for custom tools and integrations

## Architecture

### Traditional vs. Modern Approach

**Legacy Monolithic Workflow:**
```
Model Discovery → Docker Build → Container Run → Performance Collection
```

**Modern Split Architecture:**
```
BUILD PHASE (Central/CI Server):
  Model Discovery → Docker Build → Push to Registry → Export Manifest

RUN PHASE (GPU Nodes):
  Load Manifest → Pull Images → Container Run → Performance Collection
```

### Benefits of Split Architecture

- **Resource Efficiency**: Build on CPU-optimized instances, run on GPU-optimized nodes
- **Parallel Execution**: Multiple nodes can execute different models simultaneously  
- **Reproducibility**: Consistent Docker images ensure identical results across environments
- **Scalability**: Easy horizontal scaling by adding execution nodes
- **Cost Optimization**: Use appropriate instance types for each workflow phase
- **CI/CD Integration**: Seamless integration with existing DevOps pipelines

## Installation

madengine is designed to work within the [MAD (Model Automation and Dashboarding)](https://github.com/ROCm/MAD) package ecosystem. Follow these steps for proper installation and setup.

### Prerequisites

- **Python 3.8 or higher**
- **Git** for repository management
- **Docker** with GPU support (ROCm for AMD, CUDA for NVIDIA)
- **MAD package** cloned and available locally

### Development Installation

```bash
# Clone MAD package first
git clone git@github.com:ROCm/MAD.git
cd MAD

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Clone madengine into MAD directory or install as dependency
git clone git@github.com:ROCm/madengine.git
cd madengine

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks (recommended for contributors)
pre-commit install
```

### Production Installation

```bash
# Navigate to MAD package directory
cd /path/to/MAD

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install madengine
pip install git+https://github.com/ROCm/madengine.git@main

# Or install from local source
git clone git@github.com:ROCm/madengine.git
cd madengine
pip install .
```

### Docker Environment Setup

For GPU-accelerated model execution:

```bash
# AMD ROCm support
docker run --rm --device=/dev/kfd --device=/dev/dri --group-add video

# NVIDIA CUDA support  
docker run --rm --gpus all

# Verify GPU access in container
docker run --rm --device=/dev/kfd --device=/dev/dri rocm/pytorch:latest rocm-smi
```

### Development Environment

For contributors and developers:

```bash
# Install with all development tools
pip install -e ".[dev]"

# Development workflow
pytest              # Run tests
black src/ tests/   # Format code  
isort src/ tests/   # Sort imports
flake8 src/ tests/  # Lint code
mypy src/madengine  # Type checking
```

### Modern Package Management

This project uses modern Python packaging standards:
- **`pyproject.toml`**: Single source of truth for dependencies and configuration
- **Hatchling build backend**: Modern, efficient build system
- **No requirements.txt**: All dependencies managed in pyproject.toml
- **pip ≥ 21.3**: Full pyproject.toml support required

## Quick Start

### Single-Node Workflow

Perfect for development, testing, or single-workstation deployments:

```bash
# Navigate to MAD package directory
cd /path/to/MAD

# Run complete workflow (build + execute)
madengine-cli run --tags dummy --registry localhost:5000 --timeout 3600

# Run with live output and detailed logging
madengine-cli run --tags dummy --live-output --verbose \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'
```

### Split Build/Run Workflow

For distributed deployments and production environments:

```bash
# Build Phase (on build server)
cd /path/to/MAD
madengine-cli build --tags dummy resnet --registry docker.io \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}' \
  --clean-docker-cache

# Run Phase (on GPU nodes)
madengine-cli run --manifest-file build_manifest.json --timeout 1800
```

### Multi-Node Production Deployment

```bash
# Build on central server
madengine-cli build --tags production_models --registry prod.registry.com \
  --additional-context '{"gpu_vendor": "NVIDIA", "guest_os": "UBUNTU"}' \
  --summary-output build_report.json

# Transfer manifest to GPU cluster
scp build_manifest.json user@gpu-cluster:/path/to/madengine/

# Execute on GPU nodes (registry auto-detected from manifest)
madengine-cli run --manifest-file build_manifest.json \
  --summary-output execution_report.json
```

## MAD Model Discovery

madengine automatically discovers available models from the MAD package structure, supporting multiple discovery methods for maximum flexibility.

### Discovery Sources

#### 1. Root Models Configuration (`models.json`)
Traditional static model definitions at the MAD package root:

```bash
# Discover and run models from root configuration
madengine-cli run --tags dummy                    # Single model
madengine-cli run --tags dummy pyt_huggingface_bert  # Multiple models
madengine discover --tags dummy                   # List available models
```

#### 2. Directory-Specific Models (`scripts/{model_dir}/models.json`)
Organized model definitions in subdirectories:

```bash
# Run models from specific directories
madengine-cli run --tags dummy2:dummy_2
madengine discover --tags dummy2:dummy_2
```

#### 3. Dynamic Model Discovery (`scripts/{model_dir}/get_models_json.py`)
Python scripts that generate model configurations dynamically:

```bash
# Run dynamic models with parameters
madengine-cli run --tags dummy3:dummy_3
madengine-cli run --tags dummy3:dummy_3:batch_size=512:in=32:out=16
```

### Required MAD Structure

For proper model discovery, ensure your MAD package follows this structure:

```
MAD/
├── models.json                          # Root model definitions
├── scripts/
│   ├── dummy2/
│   │   ├── models.json                  # Static model configs
│   │   └── run.sh
│   ├── dummy3/
│   │   ├── get_models_json.py          # Dynamic model discovery  
│   │   └── run.sh
│   └── common/
│       └── tools.json                   # Build tools configuration
├── data.json                            # Data provider configurations
├── credential.json                      # Authentication credentials
└── pyproject.toml                       # madengine package config
```

### Tag System Examples

**Simple Tags:**
```bash
madengine-cli run --tags dummy                    # From root models.json
madengine-cli run --tags pyt_huggingface_bert     # Standard model
```

**Directory Tags:**
```bash
madengine-cli run --tags dummy2:dummy_2           # Directory-specific model
```

**Parameterized Tags:**
```bash
madengine-cli run --tags dummy3:dummy_3:batch_size=512              # Single parameter
madengine-cli run --tags dummy3:dummy_3:batch_size=512:in=32:out=16 # Multiple parameters
```

### Discovery Validation

```bash
# List all discoverable models
madengine discover

# Discover specific models
madengine discover --tags dummy
madengine discover --tags dummy2:dummy_2  
madengine discover --tags dummy3:dummy_3:batch_size=256
```

## Command Line Interface

madengine provides two CLI interfaces: the traditional `madengine` command and the modern `madengine-cli` for distributed workflows.

### Traditional CLI (`madengine`)

Basic model execution and discovery:

```bash
# Run models locally
madengine run --tags pyt_huggingface_bert --live-output \
  --additional-context '{"guest_os": "UBUNTU"}'

# Discover available models
madengine discover --tags dummy

# Generate reports
madengine report to-html --csv-file-path perf.csv

# Database operations
madengine database create-table
```

### Modern Distributed CLI (`madengine-cli`)

Advanced distributed workflows with rich terminal output:

#### Build Command
```bash
madengine-cli build [OPTIONS]
```

Create Docker images and build manifests for distributed execution:

```bash
# Basic build with registry
madengine-cli build --tags dummy resnet --registry localhost:5000

# Build with comprehensive configuration
madengine-cli build --tags production_models \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}' \
  --clean-docker-cache \
  --summary-output build_summary.json
```

#### Run Command
```bash
madengine-cli run [OPTIONS]
```

Intelligent execution with automatic workflow detection:

```bash
# Execution-only (when manifest exists)
madengine-cli run --manifest-file build_manifest.json --timeout 1800

# Complete workflow (when no manifest)
madengine-cli run --tags dummy --registry localhost:5000 --timeout 3600

# Advanced execution with monitoring
madengine-cli run --tags models --live-output --verbose --keep-alive
```

#### Generate Commands
```bash
# Generate Ansible playbook
madengine-cli generate ansible --output cluster-deployment.yml

# Generate Kubernetes manifests
madengine-cli generate k8s --namespace production
```

#### Export Configuration
```bash
# Export execution configuration for external tools
madengine-cli export-config --tags models --output execution.json
```

### Command Options

**Global Options:**
- `--verbose, -v`: Enable detailed logging with rich output
- `--version`: Show version information

**Core Options:**
- `--tags, -t`: Model tags to process (multiple allowed)
- `--registry, -r`: Docker registry URL
- `--additional-context, -c`: Runtime context as JSON string
- `--additional-context-file, -f`: Runtime context from file
- `--timeout`: Execution timeout in seconds
- `--live-output, -l`: Real-time output streaming

**Build Configuration:**
- `--clean-docker-cache`: Rebuild without cache
- `--manifest-output, -m`: Build manifest output file
- `--summary-output, -s`: Summary report output file

**Advanced Configuration:**
- `--data-config`: Custom data configuration file
- `--tools-config`: Custom tools configuration
- `--force-mirror-local`: Local data mirroring path
- `--disable-skip-gpu-arch`: Disable GPU architecture filtering

## Distributed Execution

madengine supports sophisticated distributed execution scenarios, enabling separation of build and runtime environments for optimal resource utilization and scalability.

### Use Cases

#### 1. Single GPU Node (Development & Testing)
- Individual developers with dedicated GPU workstations
- Simplified workflow maintaining production patterns
- Local model development and validation

#### 2. Multi-Node GPU Clusters (Production)
- Enterprise environments with multiple GPU servers
- Parallel execution and resource sharing
- Centralized build with distributed execution

#### 3. Cloud-Native Deployments (Kubernetes)
- Modern cloud infrastructure with container orchestration
- Auto-scaling and resource management
- Integration with cloud services

#### 4. Hybrid Infrastructure (On-Premise + Cloud)
- Mixed on-premise and cloud resources
- Workload distribution and cost optimization
- Compliance and data locality requirements

#### 5. CI/CD Pipeline Integration
- Continuous integration for ML model validation
- Automated testing and quality gates
- Reproducible benchmarking workflows

### Registry Integration

#### Automatic Registry Detection
The CLI automatically handles registry information:

```bash
# Build phase stores registry info in manifest
madengine-cli build --tags models --registry docker.io

# Run phase auto-detects registry from manifest
madengine-cli run --manifest-file build_manifest.json
```

#### Registry Credentials

Configure registry access in `credential.json`:

```json
{
  "dockerhub": {
    "username": "your-dockerhub-username",
    "password": "your-dockerhub-token"
  },
  "localhost:5000": {
    "username": "local-registry-user", 
    "password": "local-registry-pass"
  },
  "my-registry.com": {
    "username": "custom-registry-user",
    "password": "custom-registry-token"
  }
}
```

**Registry Mapping:**
- `docker.io` or empty → uses `dockerhub` credentials
- `localhost:5000` → uses `localhost:5000` credentials
- Custom registries → uses registry URL as credential key

### Orchestration Integration

#### Ansible Deployment

```bash
# Generate Ansible playbook
madengine-cli generate ansible \
  --manifest-file build_manifest.json \
  --output cluster-deployment.yml

# Create inventory for GPU cluster
cat > gpu_inventory << EOF
[gpu_nodes]
gpu-01 ansible_host=192.168.1.101
gpu-02 ansible_host=192.168.1.102
gpu-03 ansible_host=192.168.1.103

[gpu_nodes:vars]
madengine_path=/opt/madengine
registry_url=production.registry.com
EOF

# Deploy to cluster
ansible-playbook -i gpu_inventory cluster-deployment.yml
```

#### Kubernetes Deployment

```bash
# Generate Kubernetes manifests
madengine-cli generate k8s \
  --manifest-file build_manifest.json \
  --namespace madengine-prod

# Deploy to cluster
kubectl create namespace madengine-prod
kubectl apply -f k8s-madengine-configmap.yaml
kubectl apply -f k8s-madengine-job.yaml

# Monitor execution
kubectl get jobs -n madengine-prod
kubectl logs -n madengine-prod job/madengine-job -f
```

## Configuration

### Context System

Contexts are runtime parameters that control model execution behavior:

```json
{
  "gpu_vendor": "AMD",
  "guest_os": "UBUNTU", 
  "timeout_multiplier": 2.0,
  "tools": [{"name": "rocprof"}]
}
```

**Required Fields for Build Operations:**
- `gpu_vendor`: AMD, NVIDIA, INTEL
- `guest_os`: UBUNTU, CENTOS, ROCKY

### Credential Management

Centralized authentication in `credential.json`:

```json
{
  "AMD_GITHUB": {
    "username": "github_username",
    "password": "github_token"
  },
  "dockerhub": {
    "username": "dockerhub_username", 
    "password": "dockerhub_token"
  },
  "MAD_AWS_S3": {
    "username": "aws_access_key",
    "password": "aws_secret_key"
  }
}
```

### Data Provider Configuration

Configure data sources in `data.json`:

```json
{
  "data_sources": {
    "model_data": {
      "local": "/path/to/local/data",
      "mirrorlocal": "/path/to/mirror",
      "readwrite": "true"
    }
  }
}
```

### Tools Configuration

Customize build tools in `scripts/common/tools.json`:

```json
{
  "docker": {
    "build_args": {...},
    "environment": {...}
  }
}
```

## Advanced Usage

### Custom Timeouts

```bash
# Model-specific timeout in models.json
{"timeout": 3600}

# Command-line timeout override  
madengine-cli run --tags models --timeout 7200

# No timeout (run indefinitely)
madengine-cli run --tags models --timeout 0
```

### Performance Profiling

```bash
# Enable GPU profiling
madengine run --tags pyt_huggingface_bert \
  --additional-context '{"tools": [{"name":"rocprof"}]}'

# Memory and performance monitoring  
madengine-cli run --tags models --live-output --verbose \
  --summary-output detailed_metrics.json
```

### Local Data Mirroring

```bash
# Force local mirroring for all workloads
madengine-cli run --tags models --force-mirror-local /tmp/mirror

# Configure per-model in data.json
{
  "mirrorlocal": "/path/to/local/mirror"
}
```

### Development and Debugging

```bash
# Keep containers alive for debugging
madengine-cli run --tags models --keep-alive --keep-model-dir

# Skip model execution (build/setup only)
madengine-cli run --tags models --skip-model-run

# Detailed logging with stack traces
madengine-cli run --tags models --verbose
```

## Deployment Scenarios

### Scenario 1: AI Research Lab

**Setup**: Multiple GPU workstations, shared storage, local registry  
**Goal**: Compare models across different GPU types

```bash
# Central build server
madengine-cli build --tags research_models --registry lab-registry:5000 \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'

# Distribute via shared storage
cp build_manifest.json /shared/nfs/madengine/

# Execute on researcher workstations
madengine-cli run --manifest-file /shared/nfs/madengine/build_manifest.json \
  --live-output --timeout 7200
```

### Scenario 2: Cloud Service Provider

**Setup**: Kubernetes cluster, CI/CD pipeline, cloud registry  
**Goal**: ML benchmarking as a service

```bash
# CI/CD build pipeline
madengine-cli build --tags customer_models --registry gcr.io/ml-bench \
  --additional-context-file customer_context.json

# Generate K8s deployment
madengine-cli generate k8s --namespace customer-bench-${CUSTOMER_ID}

# Auto-scaling deployment
kubectl apply -f k8s-manifests/ --namespace customer-bench-${CUSTOMER_ID}
```

### Scenario 3: Financial Institution

**Setup**: Secure on-premise network, compliance requirements  
**Goal**: Regular model validation with audit trails

```bash
# Secure build environment
madengine-cli build --tags risk_models --registry secure-registry.internal \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "CENTOS"}' \
  --summary-output audit_build_$(date +%Y%m%d).json

# Compliance deployment
madengine-cli generate ansible --manifest-file build_manifest.json
ansible-playbook -i secure_inventory cluster-deployment.yml \
  --extra-vars "audit_mode=true compliance_log=/audit/ml_bench.log"
```

## Contributing

We welcome contributions to madengine! Please see our [contributing guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone the repository
git clone git@github.com:yourusername/madengine.git
cd madengine

# Install development dependencies
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest

# Code formatting and linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/madengine
```

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints for all functions
- Write comprehensive tests
- Update documentation for new features
- Use semantic commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Legacy Commands Reference

For compatibility with existing workflows, the traditional CLI commands remain available:

### Model Execution
```bash
madengine run --tags pyt_huggingface_bert --live-output \
  --additional-context '{"guest_os": "UBUNTU"}'
```

### Model Discovery  
```bash
madengine discover --tags dummy
madengine discover --tags dummy2:dummy_2
madengine discover --tags dummy3:dummy_3:batch_size=512
```

### Report Generation
```bash
madengine report to-html --csv-file-path perf.csv
madengine report to-email --csv-file-path perf.csv
madengine report update-perf --perf-csv perf.csv
```

### Database Operations
```bash
madengine database create-table
madengine database update-table --csv-file-path perf.csv
madengine database upload-mongodb --type model --file-path data.json
```

### GPU Tools Integration
```bash
# GPU profiling with ROCm
madengine run --tags models \
  --additional-context '{"tools": [{"name":"rocprof"}]}'

# Library tracing
madengine run --tags models \
  --additional-context '{"tools": [{"name":"trace"}]}'
```

---

**Note**: You cannot use backslash '/' or colon ':' characters in model names or tags within `models.json` or `get_models_json.py` scripts, as these are reserved for the hierarchical tag system.

# Clone and install
git clone git@github.com:ROCm/madengine.git
cd madengine

# Install the package
pip install .
```

### Install from repository

You can also install the madengine library directly from the Github repository.

```bash
pip install git+https://github.com/ROCm/madengine.git@main
```

### Development Setup

For contributors and developers, all tools are configured in `pyproject.toml`:

```bash
# Everything needed for development
pip install -e ".[dev]"
pre-commit install

# Common development tasks:
pytest              # Run tests
black src/ tests/   # Format code
isort src/ tests/   # Sort imports  
flake8 src/ tests/  # Lint code
mypy src/madengine  # Type checking
```

### Modern Python Package Management

This project uses modern Python packaging standards:
- **`pyproject.toml`** - Single source of truth for dependencies and configuration
- **No requirements.txt** - Everything is in pyproject.toml
- **Hatchling build backend** - Modern build system
- **pip >= 21.3** - Fully supports pyproject.toml installations

## Clone MAD (Optional)

If you need to work with MAD models:

```bash
git clone git@github.com:ROCm/MAD.git
cd MAD
``` 

# Run madengine CLI

How to run madengine CLI on your local machine.

```shell
(venv) test-node:~/MAD$ madengine --help
usage: madengine [-h] [-v] {run,discover,report,database} ...

A Model automation and dashboarding command-line tool to run LLMs and Deep Learning models locally.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit

Commands:
  Available commands for running models, generating reports, and toolings.

  {run,discover,report,database}
    run                 Run models on container
    discover            Discover the models
    report              Generate report of models
    database            CRUD for database
```

For distributed execution scenarios, use the distributed CLI:

```shell
# Distributed CLI for build/run separation
python -m madengine.distributed_cli --help

# Available commands:
#   build       - Build Docker images for models
#   run         - Run models (execution-only or complete workflow)
#   generate    - Generate Ansible/Kubernetes manifests
#   export-config - Export execution configuration
```

## Run models locally

Command to run LLMs and Deep Learning Models on container.

```
# An example CLI command to run a model
madengine run --tags pyt_huggingface_bert --live-output --additional-context "{'guest_os': 'UBUNTU'}"
```

```shell
(venv) test-node:~/MAD$ madengine run --help
usage: madengine run [-h] [--tags TAGS [TAGS ...]] [--timeout TIMEOUT] [--live-output] [--clean-docker-cache] [--additional-context-file ADDITIONAL_CONTEXT_FILE]
                     [--additional-context ADDITIONAL_CONTEXT] [--data-config-file-name DATA_CONFIG_FILE_NAME] [--tools-json-file-name TOOLS_JSON_FILE_NAME]
                     [--generate-sys-env-details GENERATE_SYS_ENV_DETAILS] [--force-mirror-local FORCE_MIRROR_LOCAL] [--keep-alive] [--keep-model-dir]
                     [--skip-model-run] [--disable-skip-gpu-arch] [-o OUTPUT]

Run LLMs and Deep Learning models on container

optional arguments:
  -h, --help            show this help message and exit
  --tags TAGS [TAGS ...]
                        tags to run (can be multiple).
  --timeout TIMEOUT     time out for model run in seconds; Overrides per-model timeout if specified or default timeout of 7200 (2 hrs). Timeout of 0 will never
                        timeout.
  --live-output         prints output in real-time directly on STDOUT
  --clean-docker-cache  rebuild docker image without using cache
  --additional-context-file ADDITIONAL_CONTEXT_FILE
                        additonal context, as json file, to filter behavior of workloads. Overrides detected contexts.
  --additional-context ADDITIONAL_CONTEXT
                        additional context, as string representation of python dict, to filter behavior of workloads. Overrides detected contexts and additional-
                        context-file.
  --data-config-file-name DATA_CONFIG_FILE_NAME
                        custom data configuration file.
  --tools-json-file-name TOOLS_JSON_FILE_NAME
                        custom tools json configuration file.
  --generate-sys-env-details GENERATE_SYS_ENV_DETAILS
                        generate system config env details by default
  --force-mirror-local FORCE_MIRROR_LOCAL
                        Path to force all relevant dataproviders to mirror data locally on.
  --keep-alive          keep Docker container alive after run; will keep model directory after run
  --keep-model-dir      keep model directory after run
  --skip-model-run      skips running the model; will not keep model directory after run unless specified through keep-alive or keep-model-dir
  --disable-skip-gpu-arch
                        disables skipping model based on gpu architecture
  -o OUTPUT, --output OUTPUT
                        output file
```

For each model in models.json, the script
- builds docker images associated with each model. The images are named 'ci-$(model_name)', and are not removed after the script completes.
- starts the docker container, with name, 'container_$(model_name)'. The container should automatically be stopped and removed whenever the script exits. 
- clones the git 'url', and runs the 'script' 
- compiles the final perf.csv and perf.html

### Tag functionality for running model

With the tag functionality, the user can select a subset of the models, that have the corresponding tags matching user specified tags, to be run. User specified tags can be specified with the `--tags` argument. If multiple tags are specified, all models that match any tag is selected.
Each model name in models.json is automatically a tag that can be used to run that model. Tags are also supported in comma-separated form as a Jenkins parameter.


#### Search models with tags

Use cases of running models with static and dynamic search. Tags option supports searching models in models.json, scripts/model_dir/models.json, and scripts/model_dir/get_models_json.py. A user can add new models not only to the models.json file of DLM but also to the model folder in Flexible. To do this, the user needs to follow these steps:

Update models.json: Add the new model's configuration details to the models.json file. This includes specifying the model's name, version, and any other relevant metadata.
Place Model Files: Copy the model files into the appropriate directory within the model folder in Flexible. Ensure that the folder structure and file naming conventions match the expected format.

```
# 1. run models in ~/MAD/models.json
(venv) test-node:~/MAD$ madengine run --tags dummy --live-output

# 2. run model in ~/MAD/scripts/dummy2/models.json
(venv) test-node:~/MAD$ madengine run --tags dummy2:dummy_2 --live-output

# 3. run model in ~/MAD/scripts/dummy3/get_models_json.py
(venv) test-node:~/MAD$ madengine run --tags dummy3:dummy_3 --live-output

# 4. run model with configurations
(venv) test-node:~/MAD$ madengine run --tags dummy2:dummy_2:batch_size=512:in=32:out=16 --live-output

# 5. run model with configurations
(venv) test-node:~/MAD$ madengine run --tags dummy3:dummy_3:batch_size=512:in=32:out=16 --live-output
```

The configs of batch_size512:in32:out16 will be pass to environment variables and build arguments of docker.

### Custom timeouts
The default timeout for model run is 2 hrs. This can be overridden if the model in models.json contains a `'timeout' : TIMEOUT` entry. Both the default timeout and/or timeout specified in models.json can be overridden using `--timeout TIMEOUT` command line argument. Having `TIMEOUT` set to 0 means that the model run will never timeout.

### Live output functionality 
By default, `madengine` is silent. The output is piped into log files. By specifying `--live-output`, the output is printed in real-time to STDOUT. 

### Contexts
Contexts are run-time parameters that change how the model is executed. Some contexts are auto-detected. Detected contexts may be over-ridden. Contexts are also used to filter Dockerfile used in model.  

For more details, see [How to provide contexts](docs/how-to-provide-contexts.md)

### Credentials
Credentials to clone model git urls and access Docker registries are provided in a centralized `credential.json` file. Models that require special credentials for cloning have a special `cred` field in the model definition in `models.json`. This field denotes the specific credential in `credential.json` to use. Public models repositories can skip the `cred` field. 

There are several types of credentials supported:

#### Git Repository Credentials

1. For HTTP/HTTPS git urls, `username` and `password` should be provided in the credential. For Source Code Management(SCM) systems that support Access Tokens, the token can be substituted for the `password` field. The `username` and `password` will be passed as a docker build argument and a container environment variable in the docker build and run steps. For example, for `"cred":"AMD_GITHUB"` field in `models.json` and entry `"AMD_GITHUB": { "username": "github_username", "password":"pass" }` in `credential.json` the following docker build arguments and container environment variables will be added: `AMD_GITHUB_USERNAME="github_username"` and `AMD_GITHUB_PASSWORD="pass"`. 
      
2. For SSH git urls, `username` and `ssh_key_file` should be provided in the credential. The `username` is the SSH username, and `ssh_key_file` is the private ssh key, that has been registered with the SCM system. 

#### Data Provider Credentials

3. For NAS urls, `HOST`, `PORT`, `USERNAME`, and `PASSWORD` should be provided in the credential. Please check env variables starting with NAS in [Environment Variables](https://github.com/ROCm/madengine/blob/main/README.md#environment-variables)

4. For AWS S3 urls, `USERNAME`, and `PASSWORD` should be provided in the credential with var name as MAD_AWS_S3 as mentioned in [Environment Variables](https://github.com/ROCm/madengine/blob/main/README.md#environment-variables)

#### Docker Registry Credentials

5. For Docker registries (Docker Hub, private registries), `username` and `password` should be provided. The credential key maps to the registry URL:
   - `dockerhub` - for Docker Hub (docker.io) 
   - `localhost:5000` - for local registry
   - `myregistry.com` - for custom registry

Example `credential.json` with registry credentials:
```json
{
    "dockerhub": {
        "username": "your-dockerhub-username",
        "password": "your-dockerhub-password-or-token"
    },
    "localhost:5000": {
        "username": "local-registry-user",
        "password": "local-registry-pass"
    },
    "AMD_GITHUB": {
        "username": "github_username", 
        "password": "github_token"
    }
}
```

Due to legal requirements, the Credentials to access all models is not provided by default in DLM. Please contact the model owner if you wish to access and run the model.


### Local data provider
The DLM user may wish to run a model locally multiple times, with the input data downloaded once, and reused subsquently. This functionality is only supported on models that support the Data Provider functionality. That is, the model specification in `models.json` have the `data` field, which points to a data specification in `data.json`.

To use existing data on a local path, add to the data specification, using a `local` field within `data.json`. By default, this path is mounted read-only. To change this path to read-write, specify the `readwrite` field to `'true'` in the data configuration.

If no data exists in local path, a local copy of data can be downloaded using by setting the `mirrorlocal` field in data specification in `data.json`. Not all providers support `mirrorlocal`. For the ones that do support this feature, the remote data is mirrored on this host path during the first run. In subsequent runs, the data may be reused through synchronization mechanisms. If the user wishes to skip the remote synchronization, the same location can be set as a `local` data provider in data.json, with higher precedence, or as the only provider for the data, by locally editing `data.json`. 

Alternatively, the command-line argument, `--force-mirror-local` forces local mirroring on *all* workloads, to the provided FORCEMIRRORLOCAL path.

## Distributed Execution

madengine supports distributed execution scenarios where Docker images are built on a central host and then distributed to remote nodes for execution. This is useful for:

- **CI/CD Pipelines**: Build images once in CI, deploy to multiple GPU nodes
- **Multi-node Setups**: Build on a central host, run on distributed GPU clusters
- **Resource Optimization**: Separate build and runtime environments

### Distributed CLI Commands

The distributed execution functionality is available through the `madengine.distributed_cli` module:

```bash
# Build Docker images and create manifest
python -m madengine.distributed_cli build --tags dummy --registry docker.io

# Run models using manifest (registry auto-detected)
python -m madengine.distributed_cli run --manifest-file build_manifest.json

# Complete workflow (build + run)
python -m madengine.distributed_cli run --tags dummy --registry docker.io
```

### Registry Auto-Detection

The distributed CLI automatically detects registry information from build manifests, eliminating the need to specify `--registry` for run commands:

**Build Phase:**
```bash
# Build and push images to Docker Hub
python -m madengine.distributed_cli build --tags dummy --registry docker.io
# Creates build_manifest.json with registry information
```

**Run Phase:**
```bash
# Registry is automatically detected from manifest
python -m madengine.distributed_cli run --manifest-file build_manifest.json
# No need to specify --registry parameter
```

### Registry Credentials

To use Docker registries, add credentials to `credential.json`:

```json
{
    "dockerhub": {
        "username": "your-dockerhub-username",
        "password": "your-dockerhub-password-or-token"
    },
    "localhost:5000": {
        "username": "your-local-registry-username",
        "password": "your-local-registry-password"
    }
}
```

**Registry Mapping:**
- `docker.io` or empty → uses `dockerhub` credentials
- `localhost:5000` → uses `localhost:5000` credentials  
- Custom registries → uses registry URL as credential key

### Distributed Workflow Examples

**Local Development:**
```bash
# Build without registry (local images only)
python -m madengine.distributed_cli build --tags dummy

# Run locally 
python -m madengine.distributed_cli run --manifest-file build_manifest.json
```

**Production Deployment:**
```bash
# 1. Build and push to registry (CI server)
python -m madengine.distributed_cli build --tags dummy --registry docker.io

# 2. Transfer manifest to GPU nodes
scp build_manifest.json user@gpu-node:/path/to/madengine/

# 3. Run on GPU nodes (registry auto-detected)
python -m madengine.distributed_cli run --manifest-file build_manifest.json
```

**Multi-Node with Ansible:**
```bash
# Generate Ansible playbook
python -m madengine.distributed_cli generate ansible \
    --manifest-file build_manifest.json \
    --output madengine_playbook.yml

# Deploy to cluster
ansible-playbook -i gpu_inventory madengine_playbook.yml
```

### Error Handling

The system provides clear error messages for common issues:

**Missing Registry Credentials:**
```
No credentials found for registry: dockerhub
Please add dockerhub credentials to credential.json:
{
  "dockerhub": {
    "username": "your-dockerhub-username",
    "password": "your-dockerhub-password-or-token"
  }
}
```

**Registry Pull Fallback:**
```
Attempting to pull constructed registry image: username/ci-dummy_dummy.ubuntu.amd
Failed to pull from registry, falling back to local image: <error details>
```

For detailed documentation on distributed execution, see [Distributed Execution Solution](docs/distributed-execution-solution.md).

## Discover models

Commands for discovering models through models.json, scripts/{model_dir}/models.json, or scripts/{model_dir}/get_models_json.py

```
(venv) test-node:~/MAD$ madengine discover --help
usage: madengine discover [-h] [--tags TAGS [TAGS ...]]

Discover the models

optional arguments:
  -h, --help            show this help message and exit
  --tags TAGS [TAGS ...]
                        tags to discover models (can be multiple).
```

Use cases about how to discover models:

```
# 1 discover all models in DLM
(venv) test-node:~/MAD$ madengine discover  

# 2. discover specified model using tags in models.json of DLM
(venv) test-node:~/MAD$ madengine discover --tags dummy

# 3. discover specified model using tags in scripts/{model_dir}/models.json with static search i.e. models.json
(venv) test-node:~/MAD$ madengine discover --tags dummy2/dummy_2

# 4. discover specified model using tags in scripts/{model_dir}/get_models_json.py with dynamic search i.e. get_models_json.py
(venv) test-node:~/MAD$ madengine discover --tags dummy3/dummy_3

# 5. pass additional args to your model script from CLI
(venv) test-node:~/MAD$ madengine discover --tags dummy3/dummy_3:bs16

# 6. get multiple models using tags
(venv) test-node:~/MAD$ madengine discover --tags pyt_huggingface_bert pyt_huggingface_gpt2
```

Note: You cannot use a backslash '/' or a colon ':' in a model name or a tag for a model in `models.json` or `get_models_json.py`

## Generate reports

Commands for generating reports.

```
(venv) test-node:~/MAD$ madengine report --help
usage: madengine report [-h] {update-perf,to-html,to-email} ...

optional arguments:
  -h, --help            show this help message and exit

Report Commands:
  Available commands for generating reports.

  {update-perf,to-html,to-email}
    update-perf         Update perf.csv to database
    to-html             Convert CSV to HTML report of models
    to-email            Convert CSV to Email of models
```

### Report command - Update perf CSV to database

Update perf.csv to database

```
(venv) test-node:~/MAD$ madengine report update-perf --help
usage: madengine report update-perf [-h] [--single_result SINGLE_RESULT] [--exception-result EXCEPTION_RESULT] [--failed-result FAILED_RESULT]
                                    [--multiple-results MULTIPLE_RESULTS] [--perf-csv PERF_CSV] [--model-name MODEL_NAME] [--common-info COMMON_INFO]

Update performance metrics of models perf.csv to database.

optional arguments:
  -h, --help            show this help message and exit
  --single_result SINGLE_RESULT
                        path to the single result json
  --exception-result EXCEPTION_RESULT
                        path to the single result json
  --failed-result FAILED_RESULT
                        path to the single result json
  --multiple-results MULTIPLE_RESULTS
                        path to the results csv
  --perf-csv PERF_CSV
  --model-name MODEL_NAME
  --common-info COMMON_INFO
```

### Report command - Convert CSV to HTML

Convert CSV to HTML report of models

```
(venv) test-node:~/MAD$ madengine report to-html --help
usage: madengine report to-html [-h] [--csv-file-path CSV_FILE_PATH]

Convert CSV to HTML report of models.

optional arguments:
  -h, --help            show this help message and exit
  --csv-file-path CSV_FILE_PATH
```

### Report command - Convert CSV to Email

Convert CSV to Email report of models

```
(venv) test-node:~/MAD$ madengine report to-email --help
usage: madengine report to-email [-h] [--csv-file-path CSV_FILE_PATH]

Convert CSV to Email of models.

optional arguments:
  -h, --help            show this help message and exit
  --csv-file-path CSV_FILE_PATH
                        Path to the directory containing the CSV files.
```

## Database

Commands for database, such as create and update table of DB.

```
(venv) test-node:~/MAD$ madengine database --help
usage: madengine database [-h] {create-table,update-table,upload-mongodb} ...

optional arguments:
  -h, --help            show this help message and exit

Database Commands:
  Available commands for database, such as creating and updating table in DB.

  {create-table,update-table,upload-mongodb}
    create-table        Create table in DB
    update-table        Update table in DB
    upload-mongodb      Update table in DB
```

### Database - Create Table
```
(venv) test-node:~/MAD$ madengine database create-table --help
usage: madengine database create-table [-h] [-v]

Create table in DB.

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  verbose output
```

### Database - Update Table
```
(venv) test-node:~/MAD$ madengine database update-table --help
usage: madengine database update-table [-h] [--csv-file-path CSV_FILE_PATH] [--model-json-path MODEL_JSON_PATH]

Update table in DB.

optional arguments:
  -h, --help            show this help message and exit
  --csv-file-path CSV_FILE_PATH
                        Path to the csv file
  --model-json-path MODEL_JSON_PATH
                        Path to the model json file
```

### Database - Upload MongoDB

```
(venv) test-node:~/MAD$ madengine database upload-mongodb --help
usage: madengine database upload-mongodb [-h] [--type TYPE] [--file-path FILE_PATH] [--name NAME]

Update table in DB.

optional arguments:
  -h, --help            show this help message and exit
  --type TYPE           type of document to upload: job or run
  --file-path FILE_PATH
                        total path to directory where perf_entry.csv, *env.csv, and *.log are stored
  --name NAME           name of model to upload
```

## Tools in madengine

There are some tools distributed with madengine together. They work with madengine CLI to profile GPU and get trace of ROCm libraries.

### Tools - GPU Info Profile

Profile GPU usage of running LLMs and Deep Learning models.

```
(venv) test-node:~/MAD$ madengine run --tags pyt_huggingface_bert --additional-context "{'guest_os': 'UBUNTU','tools': [{'name':'rocprof'}]}"
```

### Tools - Trace Libraries of ROCm

Trace library usage of running LLMs and Deep Learning models. A demo of running model with tracing rocBlas.

```
(venv) test-node:~/MAD$ madengine run --tags pyt_huggingface_bert --additional-context "{'guest_os': 'UBUNTU','tools': [{'name':'rocblas_trace'}]}"
```

## Environment Variables

Madengine also exposes environment variables to allow for models location setting or data loading at DLM/MAD runtime.

| Field                       | Description                                                                       |
|-----------------------------| ----------------------------------------------------------------------------------|
| MODEL_DIR                   | the location of models dir                                                        |
| PUBLIC_GITHUB_ROCM_KEY           | username and token of GitHub                                                      |
| MAD_AWS_S3                  | the username and password of AWS S3                                               |
| NAS_NODES                   | the list of credentials of NAS Nodes                                              |

Examples for running models using environment variables.
```bash
# Apply AWS S3
MAD_AWS_S3='{"USERNAME":"username","PASSWORD":"password"}' madengine run --tags dummy_data_aws --live-output

# Apply customized NAS
NAS_NODES=[{"HOST":"hostname","PORT":"22","USERNAME":"username","PASSWORD":"password"}] madengine run --tags dummy_data_austin_nas --live-output
```

## Unit Test
Run pytest to validate unit tests of MAD Engine.

```
pytest -v -s
```
