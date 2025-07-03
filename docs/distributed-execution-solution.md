# MADEngine Distributed Execution Solution

## Overview

This solution splits the MADEngine `run_models.py` workflow into separate **build** and **run** phases to enable distributed execution scenarios such as:

- **Ansible**: Build images on a central host, distribute and run on multiple GPU nodes
- **Kubernetes**: Build images in CI/CD, deploy as jobs across GPU clusters
- **Multi-node setups**: Build once, run on multiple remote nodes with different GPU configurations

## Architecture

### Original Flow Problem
The original `run_models.py` has a tightly coupled flow:
```
Model Discovery → Docker Build → Container Run → Performance Collection
```

### New Split Architecture
```
BUILD PHASE (Central Host):
  Model Discovery → Docker Build → Push to Registry → Export Manifest

RUN PHASE (Remote Nodes): 
  Load Manifest → Pull Images → Container Run → Performance Collection
```

## Components

### 1. DockerBuilder (`docker_builder.py`)
Handles the Docker image building phase:
- Builds images for all discovered models
- Pushes images to a registry (optional)
- Exports a build manifest with image metadata
- Supports credential handling and build arguments

### 2. ContainerRunner (`container_runner.py`)
Handles the container execution phase:
- Loads build manifest from build phase
- Pulls images from registry if needed
- Runs containers with proper GPU, mount, and environment configurations
- Collects performance metrics and results

### 3. DistributedOrchestrator (`distributed_orchestrator.py`)
Coordinates the distributed workflow:
- Manages both build and run phases
- Supports complete workflows or individual phases
- Generates deployment configurations for external tools
- Handles credential and context management

### 4. Distributed CLI (`distributed_cli.py`)
Command-line interface for distributed operations:
- `build` - Build images and create manifest
- `run` - Execute containers using manifest
- `full` - Complete build + run workflow
- `generate-ansible` - Create Ansible playbooks
- `generate-k8s` - Create Kubernetes manifests

## Usage Examples

### 1. Basic Split Workflow

**Build Phase (on CI/Build server):**
```bash
# Build all models and push to registry
python -m madengine.tools.distributed_cli build \
    --registry localhost:5000 \
    --clean-cache \
    --manifest-output build_manifest.json

# This creates:
# - build_manifest.json (contains image info, build metadata)
# - Images pushed to localhost:5000 registry
```

**Run Phase (on GPU nodes):**
```bash
# Copy build_manifest.json to GPU nodes, then:
python -m madengine.tools.distributed_cli run \
    --manifest-file build_manifest.json \
    --registry localhost:5000 \
    --timeout 3600
```

### 2. Ansible Deployment

**Generate Ansible playbook:**
```bash
# Export execution configuration
python -m madengine.tools.distributed_cli export-config \
    --output execution_config.json

# Generate Ansible playbook
python -m madengine.tools.distributed_cli generate-ansible \
    --manifest-file build_manifest.json \
    --execution-config execution_config.json \
    --output madengine_distributed.yml
```

**Run with Ansible:**
```bash
# Deploy to GPU cluster
ansible-playbook -i gpu_inventory madengine_distributed.yml
```

### 3. Kubernetes Deployment

**Generate K8s manifests:**
```bash
python -m madengine.tools.distributed_cli generate-k8s \
    --manifest-file build_manifest.json \
    --execution-config execution_config.json \
    --namespace madengine-prod
```

**Deploy to Kubernetes:**
```bash
kubectl apply -f k8s-madengine-configmap.yaml
kubectl apply -f k8s-madengine-job.yaml
```

## Integration with Existing MADEngine

### Minimal Changes Required

The solution maintains compatibility with existing MADEngine components:

1. **Context System**: Uses existing `Context` class for configuration
2. **Data Provider**: Integrates with existing `Data` class for data management  
3. **Docker Integration**: Uses existing `Docker` class for container management
4. **Model Discovery**: Uses existing `DiscoverModels` for finding models

### Migration Path

1. **Immediate**: Use new distributed CLI for split workflows
2. **Gradual**: Migrate existing workflows to use distributed orchestrator
3. **Full Integration**: Replace `run_models.py` with distributed orchestrator

## Build Manifest Format

The build manifest contains all information needed for distributed execution:

```json
{
  "built_images": {
    "ci-model1_ubuntu_amd": {
      "docker_image": "ci-model1_ubuntu_amd",
      "dockerfile": "model1.ubuntu.amd.Dockerfile", 
      "base_docker": "ubuntu:20.04",
      "docker_sha": "sha256:abc123...",
      "build_duration": 120.5,
      "registry_image": "localhost:5000/ci-model1_ubuntu_amd"
    }
  },
  "context": {
    "docker_env_vars": {...},
    "docker_mounts": {...},
    "docker_build_arg": {...}
  }
}
```

## Benefits

### 1. Resource Optimization
- Build once, run multiple times
- Separate build infrastructure from GPU nodes
- Parallel execution across multiple nodes

### 2. Scalability
- Easy horizontal scaling with Kubernetes
- Support for heterogeneous GPU clusters
- Independent scaling of build vs execution

### 3. Reliability
- Immutable image artifacts
- Reproducible executions across environments
- Better error isolation between phases

### 4. DevOps Integration
- CI/CD friendly with separate phases
- Integration with container orchestrators
- Support for automated deployments

## Configuration Management

### Context Handling
The solution preserves MADEngine's context system:
- Docker environment variables
- GPU configurations
- Mount points and volumes
- Build arguments and credentials

### Credential Management
Secure handling of credentials across distributed environments:
- **Build-time credentials**: For private repositories and base images
- **Runtime credentials**: For model execution and data access  
- **Registry credentials**: For image distribution (see Registry Configuration section)

Registry credentials are automatically used during build phase for:
- Docker login to private registries
- Image pushing with proper authentication
- Secure image distribution across nodes

## Performance Considerations

### Build Phase Optimizations
- Layer caching across builds
- Parallel building of independent models
- Registry-based image distribution

### Run Phase Optimizations  
- Pre-pulling images during idle time
- Shared data mounting across nodes
- GPU resource scheduling and allocation

## Security Considerations

### Image Security
- Signed images with attestation
- Vulnerability scanning integration
- Base image security updates

### Network Security
- Private registry support
- TLS/SSL for image distribution
- Network policies for pod-to-pod communication

## Monitoring and Observability

### Build Metrics
- Build success/failure rates
- Build duration trends
- Image size optimization

### Execution Metrics
- Performance metrics collection
- Resource utilization tracking
- Error rate monitoring across nodes

## Future Enhancements

### 1. Advanced Scheduling
- GPU affinity and topology awareness
- Cost-based scheduling for cloud environments
- Priority-based execution queues

### 2. Auto-scaling
- Dynamic node scaling based on queue depth
- Preemptible instance support
- Cost optimization strategies

### 3. Advanced Monitoring
- Real-time performance dashboards
- Alerting and notification systems
- Historical trend analysis

## Registry Configuration

### Supported Registry Types

The distributed solution supports multiple registry types:

1. **DockerHub** - Public or private repositories
2. **Local Registry** - Self-hosted Docker registry
3. **Cloud Registries** - AWS ECR, Azure ACR, Google GCR
4. **Enterprise Registries** - Harbor, Nexus, etc.

### Registry Authentication

Create a `credential.json` file for registry authentication:

```json
{
  "dockerhub": {
    "username": "your-dockerhub-username",
    "password": "your-dockerhub-token"
  },
  "localhost:5000": {
    "username": "admin",
    "password": "registry-password"
  },
  "your-registry.com": {
    "username": "registry-user",
    "password": "registry-token"
  }
}
```

### Registry Usage Examples

**DockerHub (public):**
```bash
python -m madengine.tools.distributed_cli build \
    --registry docker.io \
    --manifest-output build_manifest.json
```

**DockerHub (private with authentication):**
```bash
# Requires credential.json with "dockerhub" entry
python -m madengine.tools.distributed_cli build \
    --registry dockerhub \
    --manifest-output build_manifest.json
```

**Local Registry:**
```bash
python -m madengine.tools.distributed_cli build \
    --registry localhost:5000 \
    --manifest-output build_manifest.json
```

**Cloud Registry (AWS ECR):**
```bash
python -m madengine.tools.distributed_cli build \
    --registry 123456789012.dkr.ecr.us-west-2.amazonaws.com \
    --manifest-output build_manifest.json
```
