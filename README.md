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

![madengine Architecture Overview](docs/img/architecture_overview.png)

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

![Distributed Workflow](docs/img/distributed_workflow.png)

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
madengine-cli build --tags dummy --registry localhost:5000

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
    "repository": "your-repository",
    "username": "your-dockerhub-username",
    "password": "your-dockerhub-token"
  },
  "localhost:5000": {
    "repository": "local-repository",    
    "username": "local-registry-user", 
    "password": "local-registry-pass"
  },
  "my-registry.com": {
    "repository": "custon-repository",    
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
        "nas": {
            "path": "/home/datum"
        },
        "minio": {
            "path": "s3://datasets/datum"
        },
        "aws": {
            "path": "s3://datasets/datum"
        }
    }
  }
}
```

### Tools Configuration

Customize build tools in `scripts/common/tools.json`:

```json
{
  "tools": {
    "rocprof": {
      "cmd": "rocprof",
      "env_vars": {...}
    },
    "nvprof": {
      "cmd": "nvprof",
      "env_vars": {...}
    }    
  }
}
```

### Environment Variables

madengine supports various environment variables for configuration and behavior control:

| Variable | Type | Description |
|----------|------|-------------|
| `MAD_VERBOSE_CONFIG` | boolean | Set to "true" to enable verbose configuration logging |
| `MAD_SETUP_MODEL_DIR` | boolean | Set to "true" to enable automatic MODEL_DIR setup during import |
| `MODEL_DIR` | string | Path to model directory to copy to current working directory |
| `MAD_MINIO` | JSON string | MinIO configuration for distributed storage |
| `MAD_AWS_S3` | JSON string | AWS S3 configuration for cloud storage |
| `NAS_NODES` | JSON string | NAS nodes configuration for network storage |
| `PUBLIC_GITHUB_ROCM_KEY` | JSON string | GitHub token configuration for ROCm access |

**Configuration Priority:**
1. Environment variables (as JSON strings)
2. `credential.json` file
3. Built-in defaults

**Example Usage:**
```bash
# Enable verbose logging
export MAD_VERBOSE_CONFIG=true

# Configure AWS S3 access
export MAD_AWS_S3='{"username": "aws_access_key", "password": "aws_secret_key"}'

# Set model directory
export MODEL_DIR=/path/to/models
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
