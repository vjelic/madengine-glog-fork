# madengine Distributed Execution Solution

## Overview

The madengine Distributed Execution Solution enables flexible deployment of AI model benchmarking across diverse infrastructure setups. This solution splits the traditional monolithic workflow into separate **build** and **run** phases, enabling distributed execution scenarios from simple single-node setups to complex multi-cluster deployments.

![madengine Distributed Execution Architecture Overview](img/architecture_overview.png)

### Why Distributed Execution?

Traditional AI benchmarking tools tightly couple model building and execution, limiting deployment flexibility. Our solution addresses real-world challenges:

- **Resource Optimization**: Build once on powerful build servers, run on specialized GPU nodes
- **Infrastructure Flexibility**: Deploy across heterogeneous hardware without rebuilding
- **CI/CD Integration**: Seamlessly integrate with existing DevOps pipelines
- **Cost Efficiency**: Leverage different instance types for build vs. execution workloads
- **Scale Management**: Distribute workloads across multiple nodes or clusters

### Supported Use Cases

![Distributed Workflow Example](img/distributed_workflow.png)

#### 1. **Single GPU Node** (Development & Testing)
- **Scenario**: Individual developers or small teams with dedicated GPU workstations
- **Benefits**: Simplified workflow while maintaining production-ready patterns
- **Example**: Data scientist running model comparisons on a local workstation

#### 2. **Multi-Node GPU Clusters** (Production Workloads)
- **Scenario**: Enterprise environments with multiple GPU servers
- **Benefits**: Parallel execution, resource sharing, centralized management
- **Example**: ML engineering team benchmarking models across different GPU types

#### 3. **Cloud-Native Deployments** (Kubernetes/Container Orchestration)
- **Scenario**: Modern cloud infrastructure with container orchestration
- **Benefits**: Auto-scaling, resource management, integration with cloud services
- **Example**: Cloud provider offering ML benchmarking as a service

#### 4. **Hybrid Infrastructure** (On-Premise + Cloud)
- **Scenario**: Organizations with mixed on-premise and cloud resources
- **Benefits**: Workload distribution, cost optimization, data locality
- **Example**: Financial institution with compliance requirements and cloud bursting needs

#### 5. **CI/CD Pipeline Integration** (Automated Testing)
- **Scenario**: Continuous integration environments for ML model validation
- **Benefits**: Automated testing, reproducible results, quality gates
- **Example**: MLOps pipeline validating model performance before deployment

## Architecture & Design

### Legacy Challenges
The original `run_models.py` workflow created several limitations:
```
Model Discovery → Docker Build → Container Run → Performance Collection
```

**Problems:**
- Tight coupling between build and execution phases
- Resource waste (building on expensive GPU nodes)
- Limited scalability (serial execution)
- Difficult CI/CD integration
- Complex multi-environment deployment

### Modern Split Architecture
Our solution decouples these phases for maximum flexibility:

```
BUILD PHASE (Central/CI Server):
  Model Discovery → Docker Build → Push to Registry → Export Manifest

RUN PHASE (GPU Nodes):
  Load Manifest → Pull Images → Container Run → Performance Collection
```

**Benefits:**
- **Resource Efficiency**: Build on CPU-optimized instances, run on GPU-optimized instances
- **Parallel Execution**: Multiple nodes can run different models simultaneously
- **Reproducibility**: Same Docker images ensure consistent results across environments
- **Scalability**: Easy horizontal scaling by adding more execution nodes
- **Cost Optimization**: Use appropriate instance types for each phase 
  Load Manifest → Pull Images → Container Run → Performance Collection

## Core Components

### 1. **Modern CLI** (`madengine-cli`)
Production-ready command-line interface built with Typer and Rich:
- **Beautiful Output**: Progress bars, tables, panels with rich formatting
- **Smart Commands**: Automatic workflow detection (build-only vs. full workflow)
- **Type Safety**: Full type annotations with automatic validation
- **Error Handling**: Context-aware error messages with helpful suggestions

**Key Commands:**
- `madengine-cli build` - Build images and create manifest
- `madengine-cli run` - Intelligent run command (execution-only or full workflow)
- `madengine-cli generate` - Create deployment configurations
- `madengine-cli export-config` - Export configurations for external tools

### 2. **DockerBuilder** (`docker_builder.py`)
Handles the Docker image building phase:
- Builds images for all discovered models with proper tagging
- Pushes images to registries with credential handling
- Exports comprehensive build manifests with metadata
- Supports advanced build arguments and caching strategies

### 3. **ContainerRunner** (`container_runner.py`)
Manages container execution phase:
- Loads build manifests and pulls images automatically
- Configures GPU access, mounts, and environment variables
- Collects performance metrics and execution results
- Handles timeout management and container lifecycle

### 4. **DistributedOrchestrator** (`distributed_orchestrator.py`)
Coordinates the distributed workflow:
- Manages both independent and combined build/run phases
- Generates deployment configurations for external orchestration tools
- Handles credential management and context passing
- Provides comprehensive logging and error reporting

## Getting Started

### Prerequisites

**For All Deployments:**
- madengine installed on build and execution nodes
- Docker installed and running
- Access to a Docker registry (local or cloud-based)

**For GPU Execution:**
- ROCm Docker support (for AMD GPUs) or NVIDIA Docker runtime (for NVIDIA GPUs)
- Appropriate GPU drivers installed

**For Distributed Deployments:**
- Network connectivity between build server and GPU nodes
- SSH access or orchestration tools (Ansible/Kubernetes) configured

### Quick Start: Single Node

Perfect for development, testing, or single-workstation deployments:

```bash
# Install and setup
pip install -e .

# Simple workflow: build and run on same machine
madengine-cli run --tags dummy --registry localhost:5000 --timeout 3600

# Or split phases for testing distributed workflow
madengine-cli build --tags dummy --registry localhost:5000 \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'
madengine-cli run --manifest-file build_manifest.json
```

### Quick Start: Multi-Node

For production deployments across multiple GPU servers:

```bash
# On build server
madengine-cli build --tags resnet bert --registry my-registry.com:5000 \
  --additional-context '{"gpu_vendor": "NVIDIA", "guest_os": "UBUNTU"}'

# Transfer manifest to GPU nodes
scp build_manifest.json user@gpu-node-01:/path/to/madengine/

# On each GPU node
madengine-cli run --manifest-file build_manifest.json --timeout 7200
```

## Usage Examples & Deployment Patterns

### 1. Development Workflow (Single Node)

**Audience**: Data scientists, ML engineers, individual developers  
**Use Case**: Local model development and testing

```bash
# Complete workflow for development
madengine-cli run --tags dummy --registry localhost:5000 \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}' \
  --live-output --verbose

# Split workflow for testing distributed patterns
madengine-cli build --tags dummy --registry localhost:5000 \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}' \
  --clean-docker-cache

madengine-cli run --manifest-file build_manifest.json --timeout 1800
```

### 2. Production Split Workflow

**Audience**: DevOps engineers, platform teams  
**Use Case**: Production deployments with resource optimization

**Build Phase (on CI/Build server):**
```bash
# Build all models and push to registry
madengine-cli build \
    --tags resnet bert llama \
    --registry production.registry.com \
    --additional-context '{"gpu_vendor": "NVIDIA", "guest_os": "UBUNTU"}' \
    --clean-docker-cache \
    --manifest-output build_manifest.json \
    --summary-output build_summary.json

# This creates:
# - build_manifest.json (contains image info, model info, build metadata)
# - Images pushed to production.registry.com
# - build_summary.json (build status and metrics)
```

**Run Phase (on GPU nodes):**
```bash
# Copy build_manifest.json to GPU nodes, then:
madengine-cli run \
    --manifest-file build_manifest.json \
    --timeout 3600 \
    --summary-output execution_summary.json

# Registry information is automatically detected from the manifest
# No need to specify --registry parameter unless you want to override
```

### 3. Intelligent Workflow Detection

**Audience**: All users  
**Use Case**: Simplified operations with automatic workflow detection

The `madengine-cli run` command automatically detects whether to perform execution-only or complete workflow:

**Complete Workflow (when no manifest exists):**
```bash
# Automatically runs build + run phases
madengine-cli run \
    --tags resnet \
    --registry localhost:5000 \
    --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}' \
    --timeout 3600 \
    --clean-docker-cache
```

**Execution-Only Mode (when manifest exists):**
```bash
# Only runs the execution phase using existing manifest
# Registry is automatically detected from the manifest
madengine-cli run \
    --manifest-file build_manifest.json \
    --timeout 3600

# Optional: Override registry from manifest
madengine-cli run \
    --manifest-file build_manifest.json \
    --registry custom-registry.com \
    --timeout 3600
```

### 4. Ansible Deployment

**Audience**: Infrastructure teams, system administrators  
**Use Case**: Automated deployment across multiple GPU nodes

**Export execution configuration:**
```bash
# Export execution configuration for external tools
madengine-cli export-config \
    --tags resnet bert \
    --additional-context '{"gpu_vendor": "NVIDIA", "guest_os": "UBUNTU"}' \
    --output execution_config.json
```

**Generate Ansible playbook:**
```bash
# Generate Ansible playbook using the manifest and config
madengine-cli generate ansible \
    --manifest-file build_manifest.json \
    --execution-config execution_config.json \
    --output madengine_distributed.yml
```

**Run with Ansible:**
```bash
# Create inventory file for your GPU cluster
cat > gpu_inventory << EOF
[gpu_nodes]
gpu-node-01 ansible_host=192.168.1.101 ansible_user=madengine
gpu-node-02 ansible_host=192.168.1.102 ansible_user=madengine
gpu-node-03 ansible_host=192.168.1.103 ansible_user=madengine

[gpu_nodes:vars]
madengine_path=/opt/madengine
registry_url=production.registry.com
EOF

# Deploy to GPU cluster
ansible-playbook -i gpu_inventory madengine_distributed.yml
```

### 5. Kubernetes Deployment

**Audience**: Platform engineers, cloud architects  
**Use Case**: Cloud-native deployments with auto-scaling and resource management

**Export execution configuration:**
```bash
# Export execution configuration for external tools
madengine-cli export-config \
    --tags llama bert \
    --additional-context '{"gpu_vendor": "NVIDIA", "guest_os": "UBUNTU"}' \
    --output execution_config.json
```

**Generate K8s manifests:**
```bash
madengine-cli generate k8s \
    --manifest-file build_manifest.json \
    --execution-config execution_config.json \
    --namespace madengine-prod
```

**Deploy to Kubernetes:**
```bash
# Create namespace and deploy
kubectl create namespace madengine-prod
kubectl apply -f k8s-madengine-configmap.yaml
kubectl apply -f k8s-madengine-job.yaml

# Monitor execution
kubectl get jobs -n madengine-prod
kubectl logs -n madengine-prod job/madengine-job -f
```

**Important K8s Customization Notes:**
- Update `nodeSelector` to match your GPU node labels
- Adjust resource requests/limits based on model requirements  
- Modify GPU resource types (`nvidia.com/gpu` vs `amd.com/gpu`) based on hardware
- Update the container image to use your distributed runner image
- Customize the command to use: `madengine-cli run --manifest-file=/config/manifest.json`

## Real-World Deployment Scenarios

### Scenario 1: AI Research Lab

**Setup**: 5 GPU workstations, shared NFS storage, local Docker registry  
**Requirement**: Researchers need to compare models across different GPU types

```bash
# Central build server (shared machine)
madengine-cli build --tags transformer_models --registry lab-registry:5000 \
  --additional-context '{"gpu_vendor": "NVIDIA", "guest_os": "UBUNTU"}' \
  --clean-docker-cache

# Distribute to workstations via shared storage
cp build_manifest.json /shared/nfs/madengine/

# Each researcher runs on their workstation
madengine-cli run --manifest-file /shared/nfs/madengine/build_manifest.json \
  --timeout 7200 --keep-alive --live-output
```

### Scenario 2: Cloud Service Provider

**Setup**: Kubernetes cluster with mixed GPU types, CI/CD pipeline, cloud registry  
**Requirement**: Provide ML benchmarking as a service to customers

```bash
# CI/CD Pipeline (GitLab/Jenkins)
madengine-cli build --tags customer_models --registry gcr.io/ml-bench \
  --additional-context-file customer_context.json \
  --summary-output build_metrics.json

# Generate K8s manifests for auto-scaling deployment
madengine-cli generate k8s --namespace customer-bench-$CUSTOMER_ID

# Deploy with auto-scaling based on queue depth
kubectl apply -f k8s-manifests/ --namespace customer-bench-$CUSTOMER_ID
```

### Scenario 3: Financial Institution

**Setup**: On-premise secure network, compliance requirements, air-gapped registry  
**Requirement**: Regular model validation with audit trails

```bash
# Secure build environment
madengine-cli build --tags risk_models --registry secure-registry.internal \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "CENTOS"}' \
  --summary-output audit_build_$(date +%Y%m%d).json

# Ansible deployment with compliance logging
madengine-cli generate ansible --manifest-file build_manifest.json
ansible-playbook -i secure_gpu_inventory madengine_distributed.yml \
  --extra-vars "audit_mode=true compliance_log=/audit/ml_bench_$(date +%Y%m%d).log"
```

## Advanced Configuration & Optimization

### Configuration Export & External Integration

**Audience**: DevOps teams, integration specialists  
**Use Case**: Integration with existing tools and monitoring systems

The `export-config` command allows you to export execution configurations for use with external orchestration tools:

```bash
# Export configuration with specific tags
madengine-cli export-config \
    --tags llama bert \
    --additional-context '{"gpu_vendor": "NVIDIA", "guest_os": "UBUNTU"}' \
    --output execution_config.json

# Export configuration for all discovered models
madengine-cli export-config \
    --additional-context-file production_context.json \
    --output all_models_config.json
```

**Exported Configuration Includes:**
- Model discovery information and metadata
- Required credentials and authentication
- Docker environment variables and volume mounts
- GPU configuration and resource requirements
- Custom tool configurations and data paths

**Integration Examples:**
```bash
# Integration with monitoring systems
curl -X POST http://monitoring.internal/api/benchmarks \
     -H "Content-Type: application/json" \
     -d @execution_config.json

# Custom orchestration with Terraform
terraform apply -var-file="execution_config.json"

# Jenkins pipeline integration
jenkins-cli build madengine-benchmark --parameters execution_config.json
```

### Performance Optimization

**Build Optimization:**
```bash
# Clean build for reproducible images
madengine-cli build \
    --tags production_models \
    --registry production.registry.com \
    --clean-docker-cache \
    --additional-context '{"gpu_vendor": "NVIDIA", "guest_os": "UBUNTU"}' \
    --tools-config ./configs/optimized-tools.json

# Parallel builds with resource management
madengine-cli build \
    --tags batch_1 batch_2 batch_3 \
    --registry localhost:5000 \
    --sys-env-details \
    --disable-skip-gpu-arch
```

**Execution Optimization:**
```bash
# High-performance execution with custom timeouts
madengine-cli run \
    --manifest-file build_manifest.json \
    --timeout 0 \
    --keep-model-dir \
    --force-mirror-local /fast-ssd/data \
    --summary-output detailed_metrics.json

# Resource monitoring during execution
madengine-cli run \
    --manifest-file build_manifest.json \
    --live-output \
    --verbose
```

### CLI Reference Summary

**Essential Commands for Different Users:**

**Data Scientists / Researchers:**
```bash
# Simple complete workflow
madengine-cli run --tags dummy --registry localhost:5000

# Development with live monitoring
madengine-cli run --tags my_model --live-output --verbose \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'
```

**DevOps Engineers:**
```bash
# Production build pipeline
madengine-cli build --tags production_suite --registry prod.registry.com \
  --clean-docker-cache --summary-output build_report.json

# Execution with monitoring
madengine-cli run --manifest-file build_manifest.json \
  --timeout 7200 --summary-output execution_report.json
```

**Platform Teams:**
```bash
# Generate deployment configs
madengine-cli export-config --tags cluster_models --output deploy_config.json
madengine-cli generate ansible --output cluster_deployment.yml
madengine-cli generate k8s --namespace ml-production
```

## Integration & Migration

### Compatibility with Existing madengine

The distributed solution maintains full compatibility with existing madengine components:

**Preserved Components:**
- **Context System**: Uses existing `Context` class for configuration management
- **Data Provider**: Integrates seamlessly with existing `Data` class for data handling  
- **Docker Integration**: Leverages existing `Docker` class for container management
- **Model Discovery**: Uses existing `DiscoverModels` for finding and filtering models
- **All CLI Arguments**: Supports all existing madengine command-line options

**Enhanced Features:**
- **Modern CLI**: Beautiful output with progress bars, tables, and rich formatting
- **Better Error Handling**: Context-aware error messages with helpful suggestions
- **Type Safety**: Full type annotations with automatic validation
- **Advanced Configuration**: Additional options for optimization and customization

### Migration Strategies

#### 1. **Gradual Migration** (Recommended)
```bash
# Phase 1: Start using new CLI for development
madengine-cli run --tags dummy --registry localhost:5000

# Phase 2: Adopt split workflow for production
madengine-cli build --tags prod_models --registry prod.registry.com
madengine-cli run --manifest-file build_manifest.json

# Phase 3: Integrate with orchestration tools
madengine-cli generate ansible --output prod_deployment.yml
```

#### 2. **Side-by-Side Comparison**
```bash
# Run both old and new workflows for validation
python -m madengine.mad --tags dummy  # Original
madengine-cli run --tags dummy         # New

# Compare results and performance metrics
```

#### 3. **Direct Replacement**
```bash
# Replace existing scripts/pipelines with new CLI
# Old: python -m madengine.mad --tags production --registry localhost:5000
# New: madengine-cli run --tags production --registry localhost:5000
```

### Enterprise Integration Patterns

#### CI/CD Pipeline Integration
```yaml
# GitLab CI example
stages:
  - build
  - test
  - deploy

build_models:
  stage: build
  script:
    - madengine-cli build --tags $MODEL_TAGS --registry $CI_REGISTRY_IMAGE
    - madengine-cli export-config --output config.json
  artifacts:
    paths:
      - build_manifest.json
      - config.json

test_models:
  stage: test
  script:
    - madengine-cli run --manifest-file build_manifest.json --timeout 1800
  artifacts:
    reports:
      junit: test_results.xml

deploy_production:
  stage: deploy
  script:
    - madengine-cli generate k8s --namespace production
    - kubectl apply -f k8s-madengine-*.yaml
```

#### Monitoring Integration
```bash
# Prometheus metrics export
madengine-cli run --manifest-file build_manifest.json \
  --summary-output metrics.json

# Custom metrics processing
python post_process_metrics.py metrics.json > prometheus_metrics.txt
curl -X POST http://pushgateway:9091/metrics/job/madengine < prometheus_metrics.txt
```

## Step-by-Step Tutorial: Single Model Deployment

This tutorial walks through deploying a single model (`dummy`) across distributed infrastructure.

### Phase 1: Build and Prepare

**Step 1: Build the Model**
```bash
cd /path/to/madengine

# Build dummy model with proper context
madengine-cli build \
    --tags dummy \
    --registry localhost:5000 \
    --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}' \
    --manifest-output dummy_manifest.json \
    --summary-output dummy_build.json \
    --clean-docker-cache
```

**Step 2: Verify Build**
```bash
# Check build status
cat dummy_build.json | jq '.successful_builds | length'

# Verify registry push
docker images | grep dummy
curl http://localhost:5000/v2/_catalog
```

### Phase 2: Single Node Execution

**Step 3: Local Testing**
```bash
# Test locally first
madengine-cli run \
    --manifest-file dummy_manifest.json \
    --timeout 1800 \
    --live-output \
    --summary-output dummy_execution.json
```

### Phase 3: Multi-Node Deployment

**Step 4: Manual Distribution**
```bash
# Copy to remote GPU node
scp dummy_manifest.json user@gpu-node:/opt/madengine/

# SSH and execute
ssh user@gpu-node 'cd /opt/madengine && madengine-cli run --manifest-file dummy_manifest.json'
```

**Step 5: Automated Deployment**
```bash
# Generate Ansible playbook
madengine-cli export-config --tags dummy --output dummy_config.json
madengine-cli generate ansible --manifest-file dummy_manifest.json --output deploy.yml

# Deploy with Ansible
ansible-playbook -i gpu_inventory deploy.yml
```

### Phase 4: Production Kubernetes

**Step 6: Container Orchestration**
```bash
# Generate K8s manifests
madengine-cli generate k8s --namespace madengine-prod --manifest-file dummy_manifest.json

# Deploy to cluster
kubectl create namespace madengine-prod
kubectl apply -f k8s-madengine-configmap.yaml
kubectl apply -f k8s-madengine-job.yaml

# Monitor execution
kubectl logs -f job/madengine-job -n madengine-prod
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Build Phase Problems

**Registry Connectivity Issues:**
```bash
# Test registry access
curl -v http://localhost:5000/v2/_catalog
docker login localhost:5000

# Fix: Check registry service and firewall
sudo systemctl status docker-registry
sudo ufw allow 5000
```

**Model Discovery Failures:**
```bash
# Verify model tags and paths
madengine-cli export-config --tags dummy --verbose

# Fix: Check model configuration files
ls -la scripts/dummy/
cat models.json | jq '.models[] | select(.tags[] | contains("dummy"))'
```

**Docker Build Failures:**
```bash
# Check Docker daemon and space
docker system info
docker system df

# Fix: Clean up space and restart Docker
docker system prune -f
sudo systemctl restart docker
```

#### Execution Phase Problems

**GPU Access Issues:**
```bash
# Check GPU availability
nvidia-smi  # or rocm-smi for AMD
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Fix: Install Docker GPU runtime
sudo apt-get install nvidia-docker2
sudo systemctl restart docker
```

**Image Pull Failures:**
```bash
# Test image pull manually
docker pull localhost:5000/madengine/dummy:latest

# Fix: Check registry URL in manifest
cat build_manifest.json | jq '.registry'
```

**Permission Errors:**
```bash
# Check Docker permissions
groups $USER | grep docker

# Fix: Add user to Docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Network and Distribution Issues

**SSH/Ansible Connectivity:**
```bash
# Test SSH access
ssh -v user@gpu-node

# Fix: Setup SSH keys
ssh-copy-id user@gpu-node
```

**Kubernetes Deployment Problems:**
```bash
# Check cluster access
kubectl cluster-info
kubectl get nodes

# Fix: Update kubeconfig
kubectl config view
kubectl config use-context correct-cluster
```

### Performance Optimization Tips

#### For Build Phase:
- Use `--clean-docker-cache` sparingly (only when needed)
- Enable Docker BuildKit for faster builds
- Use local registry to reduce push/pull times
- Build during off-peak hours for better resource utilization

#### For Execution Phase:
- Use `--force-mirror-local` for faster data access
- Set appropriate `--timeout` values based on model complexity
- Enable `--live-output` for long-running jobs
- Use `--keep-alive` for debugging failed executions

### Monitoring and Logging

**Enable Verbose Logging:**
```bash
madengine-cli run --manifest-file build_manifest.json --verbose
```

**Monitor Resource Usage:**
```bash
# GPU monitoring
watch -n 1 nvidia-smi

# System monitoring
htop
iostat -x 1
```

**Collect Execution Metrics:**
```bash
madengine-cli run --manifest-file build_manifest.json \
  --summary-output execution_metrics.json \
  --live-output
```

## Quick Reference

### Command Cheat Sheet

**Single Node Development:**
```bash
# Complete workflow
madengine-cli run --tags dummy --registry localhost:5000

# Split workflow for testing
madengine-cli build --tags dummy --registry localhost:5000 \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'
madengine-cli run --manifest-file build_manifest.json
```

**Multi-Node Production:**
```bash
# Build phase (CI/Build server)
madengine-cli build --tags prod_models --registry prod.registry.com \
  --additional-context-file production.json --clean-docker-cache

# Execution phase (GPU nodes)
madengine-cli run --manifest-file build_manifest.json --timeout 7200
```

**Automated Deployment:**
```bash
# Ansible
madengine-cli export-config --output config.json
madengine-cli generate ansible --output deployment.yml
ansible-playbook -i inventory deployment.yml

# Kubernetes
madengine-cli generate k8s --namespace production
kubectl apply -f k8s-madengine-*.yaml
```

### File Outputs

| File | Purpose | When Generated |
|------|---------|----------------|
| `build_manifest.json` | Build metadata and image info | After successful build |
| `execution_config.json` | Runtime configuration | Via `export-config` command |
| `*_summary.json` | Build/execution metrics | When `--summary-output` used |
| `madengine_distributed.yml` | Ansible playbook | Via `generate ansible` |
| `k8s-madengine-*.yaml` | Kubernetes manifests | Via `generate k8s` |
| `perf.csv` | Performance results | After model execution |

### Best Practices

1. **Always use `--additional-context`** for build-only operations
2. **Test locally first** before distributed deployment
3. **Use semantic tagging** for model organization
4. **Monitor build and execution metrics** with summary outputs
5. **Implement proper registry authentication** for production
6. **Customize generated templates** for your infrastructure
7. **Use version control** for configuration files
8. **Document your deployment patterns** for team consistency

## Benefits Summary

### For Development Teams
- **Faster Iteration**: Build once, test on multiple configurations
- **Local Development**: Full workflow on single machines
- **Easy Debugging**: Live output and container inspection capabilities

### For Operations Teams  
- **Resource Optimization**: Separate build and execution infrastructure
- **Scalability**: Horizontal scaling across multiple nodes
- **Integration**: Seamless CI/CD and orchestration tool support
- **Monitoring**: Comprehensive metrics and logging

### For Organizations
- **Cost Efficiency**: Use appropriate instance types for each workload phase
- **Flexibility**: Support diverse infrastructure setups
- **Compliance**: Audit trails and reproducible builds
- **Innovation**: Enable new deployment patterns and use cases

---

**Next Steps:**
1. Try the single-node quick start for your use case
2. Explore split workflow for your infrastructure
3. Integrate with your existing CI/CD pipelines
4. Scale to multi-node deployments
5. Customize for your specific requirements

For additional support and examples, see the [madengine-cli guide](./madengine-cli-guide.md) and project documentation.
