# madengine-cli Guide

A production-ready, modern command-line interface for the madengine Distributed Orchestrator built with Typer and Rich for building and running AI models in distributed scenarios within the MAD (Model Automation and Dashboarding) package.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [MAD Model Discovery and Tag System](#mad-model-discovery-and-tag-system)
- [Command Overview](#command-overview)
- [Usage](#usage)
  - [Core Commands](#core-commands)
  - [Production Examples](#production-examples)
- [Command Reference](#command-reference)
- [Configuration Files](#configuration-files)
- [Advanced Configuration](#advanced-configuration)
- [Output & User Experience](#output--user-experience)
- [Best Practices](#best-practices)
- [Migration Guide](#migration-guide)
- [Development & Testing](#development--testing)
- [Troubleshooting](#troubleshooting)
- [Exit Codes](#exit-codes)
- [Shell Completion](#shell-completion)

## Overview

The `madengine-cli` is the next-generation CLI interface that replaces and enhances the original distributed CLI. It provides a modern, user-friendly interface with rich terminal output, better error handling, and improved workflow management.

madengine is designed to work within the **MAD (Model Automation and Dashboarding) package**, which serves as a comprehensive model hub containing Docker configurations, scripts, and adopted AI models. The CLI automatically discovers available models from the MAD repository structure to enable selective building and execution.

## Features

🚀 **Modern Design**: Built with Typer for excellent CLI experience and Rich for beautiful terminal output  
📊 **Rich Output**: Progress bars, tables, panels, and syntax highlighting  
✅ **Better Error Handling**: Clear error messages with helpful suggestions  
🎯 **Type Safety**: Full type annotations with automatic validation  
📝 **Auto-completion**: Built-in shell completion support  
🎨 **Colorful Interface**: Beautiful, informative output with emojis and colors  
⚡ **Performance**: Optimized for speed and responsiveness  
🔄 **Intelligent Workflows**: Automatic detection of build-only vs. full workflow operations  
📋 **Configuration Export**: Export configurations for external orchestration tools  

## Installation

madengine is designed to be installed within the MAD package environment:

```bash
# Navigate to MAD package directory
cd /path/to/MAD

# Install madengine within MAD package (development mode)
pip install -e .
```

**Prerequisites:**
- **MAD package** cloned and available
- Python 3.8 or higher
- Docker installed and running
- Access to MAD model repository structure

## Quick Start

### Single Command Workflow
```bash
# Navigate to MAD package directory
cd /path/to/MAD

# Complete workflow: build and run models in one command (discovers models from MAD)
madengine-cli run --tags dummy --registry localhost:5000 --timeout 3600
```

### Separated Build and Run
```bash
# 1. Build phase: Create Docker images and manifest (within MAD package)
cd /path/to/MAD
madengine-cli build --tags dummy --registry localhost:5000 \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'

# 2. Run phase: Execute using the generated manifest
madengine-cli run --manifest-file build_manifest.json
```

### MAD Model Discovery Examples
```bash
# Discover models from different MAD sources
madengine-cli run --tags dummy                           # Root models.json
madengine-cli run --tags dummy2:dummy_2                  # scripts/dummy2/models.json  
madengine-cli run --tags dummy3:dummy_3:batch_size=512   # scripts/dummy3/get_models_json.py
```

## MAD Model Discovery and Tag System

### Understanding MAD Package Structure

madengine-cli works within the **MAD (Model Automation and Dashboarding) package** and automatically discovers available models from multiple sources:

#### Model Discovery Sources

**1. Root Models Configuration** (`models.json`)
- Main model definitions at MAD package root
- Traditional static model configurations
```bash
madengine-cli build --tags dummy                    # Discovers from root models.json
madengine-cli build --tags pyt_huggingface_bert     # Standard model tags
```

**2. Directory-Specific Models** (`scripts/{model_dir}/models.json`)  
- Static model definitions in subdirectories
- Organized by model families or categories
```bash
madengine-cli build --tags dummy2:dummy_2           # From scripts/dummy2/models.json
```

**3. Dynamic Model Discovery** (`scripts/{model_dir}/get_models_json.py`)
- Python scripts that generate model configurations dynamically
- Supports parameterized model variants
```bash
madengine-cli build --tags dummy3:dummy_3                          # Basic dynamic model
madengine-cli build --tags dummy3:dummy_3:batch_size=512:in=32     # With parameters
```

#### Tag System Examples

**Simple Tags (Root Models):**
```bash
madengine-cli run --tags dummy                                      # Single model
madengine-cli run --tags dummy pyt_huggingface_bert                 # Multiple models
```

**Directory Tags (Organized Models):**
```bash
madengine-cli run --tags dummy2:dummy_2                             # Directory-specific
```

**Parameterized Tags (Dynamic Models):**
```bash
madengine-cli run --tags dummy3:dummy_3:batch_size=512              # With batch size
madengine-cli run --tags dummy3:dummy_3:batch_size=512:in=32:out=16 # Multiple params
```

#### Required MAD Structure

For proper model discovery, ensure your MAD package has this structure:
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
└── pyproject.toml                       # madengine package configuration
```

#### Discovery Validation

Verify model discovery is working:
```bash
# List all discoverable models
madengine discover

# Check specific model discovery
madengine discover --tags dummy
madengine discover --tags dummy2:dummy_2
madengine discover --tags dummy3:dummy_3:batch_size=256
```

## Command Overview

The CLI provides four main command groups:

| Command | Purpose | Use Case |
|---------|---------|----------|
| `build` | Build Docker images and create manifest | Build-only operations, CI/CD pipelines |
| `run` | Execute models (with optional build) | Complete workflows, execution-only with manifest |
| `generate` | Create orchestration files | Ansible playbooks, Kubernetes manifests |
| `export-config` | Export execution configurations | External tool integration |

## Usage

### Core Commands

#### Build Command
Create Docker images and build manifest for later execution (discovers models from MAD):

```bash
# Basic build with registry (discovers from MAD root models.json)
madengine-cli build --tags dummy resnet --registry localhost:5000

# Build directory-specific models
madengine-cli build --tags dummy2:dummy_2 --registry localhost:5000

# Build with additional context (required for build-only operations)
madengine-cli build --tags pyt_huggingface_gpt2 \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'

# Build dynamic models with parameters
madengine-cli build --tags dummy3:dummy_3:batch_size=512 \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'

# Build with context from file and clean cache
madengine-cli build --tags pyt_huggingface_bert \
  --additional-context-file context.json \
  --clean-docker-cache \
  --summary-output build_summary.json
```

#### Run Command (Intelligent Workflow Detection)
The run command automatically detects whether to perform execution-only or full workflow:

```bash
# Execution-only: Use existing manifest (registry auto-detected)
madengine-cli run --manifest-file build_manifest.json --timeout 1800

# Complete workflow: Build + Run (when no valid manifest exists)
madengine-cli run --tags dummy --registry localhost:5000 --timeout 3600

# Run with live output and debugging options
madengine-cli run --tags resnet --live-output --verbose --keep-alive
```

#### Generate Commands
Create orchestration files for distributed deployment:

```bash
# Generate Ansible playbook
madengine-cli generate ansible --output my-playbook.yml

# Generate Kubernetes manifests with custom namespace
madengine-cli generate k8s --namespace production

# Generate with specific manifest and execution config
madengine-cli generate ansible \
  --manifest-file build_manifest.json \
  --execution-config production_config.json \
  --output production_playbook.yml
```

#### Export Configuration
Export execution configurations for external tools:

```bash
# Export configuration for specific models
madengine-cli export-config --tags dummy resnet --output execution.json

# Export with additional context
madengine-cli export-config --tags pyt_huggingface_gpt2 \
  --additional-context-file context.json \
  --output custom_config.json
```

### Production Examples

#### Development Environment
```bash
# Quick development testing
madengine-cli run --tags dummy --additional-context-file dev-context.json --live-output

# Build for local testing
madengine-cli build --tags custom-model \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}' \
  --clean-docker-cache
```

#### CI/CD Pipeline Integration
```bash
# Build phase in CI (with comprehensive logging)
madengine-cli build \
  --tags pyt_huggingface_gpt2 pyt_huggingface_bert resnet \
  --registry production.registry.com \
  --additional-context-file production-context.json \
  --clean-docker-cache \
  --summary-output build_summary.json \
  --verbose

# Execution phase on target infrastructure
madengine-cli run \
  --manifest-file build_manifest.json \
  --timeout 7200 \
  --keep-alive \
  --summary-output execution_summary.json
```

#### Multi-Environment Deployment
```bash
# Production build with advanced configuration
madengine-cli build \
  --tags production_suite \
  --additional-context-file prod-context.json \
  --registry prod.registry.com \
  --tools-config ./configs/prod-tools.json \
  --data-config ./configs/prod-data.json \
  --disable-skip-gpu-arch \
  --force-mirror-local /tmp/local-data

# Generate deployment configurations
madengine-cli generate k8s \
  --namespace madengine-prod \
  --execution-config prod-execution.json
  
madengine-cli generate ansible \
  --manifest-file build_manifest.json \
  --output cluster_deployment.yml
```

## Command Reference

### Global Options

Available for all commands:
- `--verbose, -v`: Enable verbose logging with detailed output and rich tracebacks
- `--version`: Show version information and exit

### Build Command

```bash
madengine-cli build [OPTIONS]
```

Create Docker images and build manifest for distributed execution.

**Required for build-only operations:**
- Either `--additional-context` or `--additional-context-file` with `gpu_vendor` and `guest_os`

**Core Options:**
- `--tags, -t`: Model tags to build (multiple allowed)
- `--registry, -r`: Docker registry URL for pushing images
- `--additional-context, -c`: Additional context as JSON string
- `--additional-context-file, -f`: File containing additional context JSON

**Build Configuration:**
- `--clean-docker-cache`: Rebuild without using Docker cache
- `--manifest-output, -m`: Output file for build manifest (default: build_manifest.json)
- `--summary-output, -s`: Output file for build summary JSON
- `--live-output, -l`: Print output in real-time

**Performance & Output:**
- `--output, -o`: Performance output file (default: perf.csv)
- `--ignore-deprecated`: Force run deprecated models

**Advanced Configuration:**
- `--data-config`: Custom data configuration file (default: data.json)
- `--tools-config`: Custom tools JSON configuration (default: ./scripts/common/tools.json)
- `--sys-env-details`: Generate system config env details (default: true)
- `--force-mirror-local`: Path to force local data mirroring
- `--disable-skip-gpu-arch`: Disable skipping models based on GPU architecture

### Run Command

```bash
madengine-cli run [OPTIONS]
```

Intelligent execution command that automatically detects workflow type:
- **Execution-only**: When valid `--manifest-file` exists (registry auto-detected)
- **Complete workflow**: When no valid manifest (performs build + run)

**Core Options:**
- `--tags, -t`: Model tags to run (multiple allowed) - for full workflow
- `--manifest-file, -m`: Build manifest file path - for execution-only
- `--registry, -r`: Docker registry URL - for full workflow
- `--timeout`: Timeout in seconds (-1 for default, 0 for no timeout)

**Execution Control:**
- `--keep-alive`: Keep Docker containers alive after run
- `--keep-model-dir`: Keep model directory after run
- `--skip-model-run`: Skip running the model
- `--live-output, -l`: Print output in real-time

**Full Workflow Options (when no valid manifest):**
- All build options are available
- `--clean-docker-cache`: Rebuild images without using cache
- `--manifest-output`: Output file for build manifest

**Context & Configuration:**
- `--additional-context, -c`: Additional context as JSON string
- `--additional-context-file, -f`: File containing additional context JSON
- `--summary-output, -s`: Output file for summary JSON
- `--output, -o`: Performance output file
- All advanced configuration options from build command

### Generate Commands

Create orchestration files for distributed deployment.

#### Ansible Playbook Generation
```bash
madengine-cli generate ansible [OPTIONS]
```

**Options:**
- `--manifest-file, -m`: Build manifest file (default: build_manifest.json)
- `--execution-config, -e`: Execution config file (default: execution_config.json)
- `--output, -o`: Output Ansible playbook file (default: madengine_distributed.yml)

#### Kubernetes Manifests Generation
```bash
madengine-cli generate k8s [OPTIONS]
```

**Options:**
- `--manifest-file, -m`: Build manifest file (default: build_manifest.json)
- `--execution-config, -e`: Execution config file (default: execution_config.json)
- `--namespace, -n`: Kubernetes namespace (default: madengine)

### Export Config Command

```bash
madengine-cli export-config [OPTIONS]
```

Export execution configurations for external orchestration tools and integrations.

**Options:**
- `--tags, -t`: Model tags to export config for (multiple allowed)
- `--output, -o`: Output configuration file (default: execution_config.json)
- `--additional-context, -c`: Additional context as JSON string
- `--additional-context-file, -f`: File containing additional context JSON
- `--ignore-deprecated`: Force run deprecated models
- `--data-config`: Custom data configuration file (default: data.json)
- `--tools-config`: Custom tools JSON configuration (default: ./scripts/common/tools.json)
- `--sys-env-details`: Generate system config env details (default: true)
- `--force-mirror-local`: Path to force local data mirroring
- `--disable-skip-gpu-arch`: Disable skipping models based on GPU architecture

## Configuration Files

### Additional Context File (context.json)

Required for build-only operations and provides runtime context for model execution:

```json
{
  "gpu_vendor": "AMD",
  "guest_os": "UBUNTU",
  "custom_option": "value"
}
```

**Required Fields for Build Operations:**
- `gpu_vendor`: AMD, NVIDIA, INTEL
- `guest_os`: UBUNTU, CENTOS, ROCKY

**Example Context Files:**

*Development Context (dev-context.json):*
```json
{
  "gpu_vendor": "AMD",
  "guest_os": "UBUNTU",
  "debug_mode": true,
  "log_level": "DEBUG"
}
```

*Production Context (prod-context.json):*
```json
{
  "gpu_vendor": "AMD", 
  "guest_os": "UBUNTU",
  "optimization_level": "high",
  "memory_limit": "16GB",
  "timeout_multiplier": 2.0
}
```

### Build Manifest File (build_manifest.json)

Auto-generated during build phase, contains:
- Docker image metadata and registry information
- Model configuration and build parameters
- System environment details
- Registry authentication information

**Registry Auto-Detection**: The run command automatically detects registry information from build manifests, eliminating the need to specify `--registry` for execution-only operations.

### Execution Config File (execution_config.json)

Generated by `export-config` command or automatically during execution:
- Model execution parameters
- Resource requirements and constraints  
- Environment-specific configuration
- Performance tuning parameters

### Data Configuration File (data.json)

Contains data sources and datasets configuration:
```json
{
  "data_sources": {
    "default": "/path/to/datasets",
    "cache": "/tmp/model_cache"
  },
  "preprocessing": {
    "enabled": true,
    "batch_size": 32
  }
}
```

### Tools Configuration File (tools.json)

Contains build tools and environment configuration:
```json
{
  "docker": {
    "buildkit": true,
    "cache_type": "registry"
  },
  "compilers": {
    "optimization": "O3"
  }
}
```

## Advanced Configuration

### System Environment Details
The `--sys-env-details` flag (enabled by default) generates detailed system configuration information during the build process, including:
- Hardware specifications (GPU, CPU, memory)
- Driver versions and compatibility information
- Operating system and kernel details
- Docker and container runtime information

### GPU Architecture Handling
Use `--disable-skip-gpu-arch` to prevent automatic skipping of models that are not compatible with the detected GPU architecture. This is useful for:
- Cross-platform builds
- Testing compatibility across different hardware
- CI/CD environments with mixed GPU types

### Local Data Mirroring
Use `--force-mirror-local <path>` to force local data mirroring to a specific path during execution. Benefits include:
- Faster data access for repeated runs
- Offline operation capability
- Bandwidth optimization in distributed environments

### Registry Auto-Detection
The CLI automatically handles registry information:
- **Build Phase**: Registry URL is stored in build manifest
- **Run Phase**: Registry is automatically detected from manifest
- **Override**: Explicit `--registry` parameter overrides auto-detection

## Output & User Experience

### Rich Terminal Output

The CLI provides a modern, informative interface with:

#### Visual Indicators
- ✅ **Successful operations** with green checkmarks
- ❌ **Failed operations** with red X marks  
- 📊 **Summary tables** showing build/run statistics
- 🔄 **Spinner animations** during long operations
- 📈 **Progress bars** for tracked operations
- ⏱️ **Real-time status updates** with live output

#### Information Panels
- 📋 **Configuration panels** showing current settings before execution
- 🎨 **Syntax highlighted JSON** for configuration display
- 🏷️ **Color-coded status indicators** throughout the interface
- 💡 **Contextual help** with suggestions for common issues

#### Error Handling & Validation
- 🎯 **Clear error messages** with actionable context
- 💡 **Helpful suggestions** for fixing issues with example usage panels
- 🔍 **Detailed stack traces** in verbose mode for debugging
- ✅ **Input validation** with clear feedback for required fields
- 📋 **Example usage panels** for common configuration errors
- 🔧 **Smart validation** that checks context requirements for build-only operations

**Example Error Output:**
```
❌ Build failed for 2 models
💥 Additional context is required for build-only operations

💡 Example usage:
   madengine-cli build --tags dummy \
     --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'
```

#### Progress Tracking
- **Spinner Progress**: For operations without predictable duration
- **Build Progress**: Real-time feedback during Docker image creation
- **Execution Progress**: Live model execution status
- **Multi-phase Progress**: Clear indication of build → run workflow phases

### Output Files and Logging

#### Summary Files
- **Build Summary** (`build_summary.json`): Comprehensive build results and metrics
- **Execution Summary** (`execution_summary.json`): Runtime performance and status
- **Workflow Summary**: Combined build + run results for full workflows

#### Performance Data  
- **Performance CSV** (`perf.csv`): Detailed performance metrics
- **Live Output**: Real-time streaming of model execution logs
- **Verbose Logging**: Rich logging with context and stack traces

#### Generated Artifacts
- **Build Manifest** (`build_manifest.json`): Image metadata and registry information
- **Execution Config** (`execution_config.json`): Runtime configuration export
- **Orchestration Files**: Ansible playbooks and Kubernetes manifests

## Best Practices

### Development Workflow
```bash
# Ensure you're working within MAD package directory
cd /path/to/MAD

# 1. Start with quick local testing (discovers models from MAD)
madengine-cli run --tags dummy --live-output --verbose

# 2. Test different model discovery sources
madengine-cli build --tags dummy2:dummy_2 \
  --additional-context-file dev-context.json \
  --clean-docker-cache

# 3. Test dynamic models with parameters
madengine-cli build --tags dummy3:dummy_3:batch_size=256 \
  --additional-context-file dev-context.json

# 4. Validate execution
madengine-cli run --manifest-file build_manifest.json --keep-alive
```

### Production Deployment
```bash
# 1. Build with comprehensive configuration
madengine-cli build \
  --tags production_models \
  --registry prod.registry.com \
  --additional-context-file production-context.json \
  --tools-config ./configs/production-tools.json \
  --clean-docker-cache \
  --summary-output build_report.json

# 2. Generate orchestration
madengine-cli export-config \
  --tags production_models \
  --output production_config.json

madengine-cli generate ansible \
  --manifest-file build_manifest.json \
  --execution-config production_config.json \
  --output production_deployment.yml

# 3. Execute with monitoring
madengine-cli run \
  --manifest-file build_manifest.json \
  --timeout 7200 \
  --summary-output execution_report.json
```

### Error Prevention
- **Always validate context**: Use `--additional-context-file` for consistent builds
- **Use summary outputs**: Enable monitoring and debugging with `--summary-output`
- **Test locally first**: Validate workflows with `--live-output` and `--verbose`
- **Clean builds for production**: Use `--clean-docker-cache` for reproducible builds
- **Set appropriate timeouts**: Use `--timeout` to prevent hanging operations

### Performance Optimization
- **Registry caching**: Use consistent registry URLs for layer caching
- **Local data mirroring**: Use `--force-mirror-local` for repeated runs
- **Parallel execution**: Build multiple models by specifying multiple `--tags`
- **Resource management**: Use `--keep-alive` for debugging, avoid in production

## Migration Guide

### From Original CLI
The new `madengine-cli` replaces the original distributed CLI with enhanced functionality:

**Original Command:**
```bash
python -m madengine.distributed_cli build --tags dummy --registry localhost:5000
python -m madengine.distributed_cli run --manifest-file build_manifest.json
```

**New Command:**
```bash
madengine-cli build --tags dummy --registry localhost:5000
madengine-cli run --manifest-file build_manifest.json
```

### Key Differences
1. **Enhanced UX**: Rich terminal output with progress indicators and panels
2. **Better Error Handling**: Context-aware errors with actionable suggestions  
3. **Intelligent Workflows**: Automatic detection of execution-only vs. full workflow
4. **Improved Validation**: Smart validation of context requirements
5. **Modern Architecture**: Built with Typer and Rich for better maintainability

### Backward Compatibility
- All original functionality is preserved and enhanced
- Command structure remains mostly compatible
- Original CLI remains available as `python -m madengine.distributed_cli`
- New CLI is available as `madengine-cli`

### Breaking Changes
- `--clean-cache` is now `--clean-docker-cache` for clarity
- Some default file paths have been updated for better organization
- Enhanced validation may catch previously ignored configuration issues

## Development & Testing

### CLI Testing
```bash
# Verify installation and basic functionality
madengine-cli --version
madengine-cli --help

# Test individual commands
madengine-cli build --help
madengine-cli run --help
madengine-cli generate --help
madengine-cli export-config --help

# Test sub-commands
madengine-cli generate ansible --help
madengine-cli generate k8s --help
```

### Development Environment Setup
```bash
# Navigate to MAD package directory
cd /path/to/MAD

# Install madengine in development mode within MAD package
pip install -e .

# Verify MAD model discovery is working
madengine discover                    # List all discoverable models
madengine discover --tags dummy       # Check specific model discovery

# Run with full debugging (discovers models from MAD structure)
madengine-cli run --tags dummy --verbose --live-output

# Test different model discovery sources
madengine-cli build --tags dummy2:dummy_2 --verbose     # Directory models
madengine-cli build --tags dummy3:dummy_3 --verbose     # Dynamic models

# Test configuration validation
madengine-cli build --tags dummy  # Should show context requirement error
```

### Technical Architecture

The modern CLI is built with:

- **Typer**: Command-line parsing, validation, and help generation
- **Rich**: Beautiful terminal output, progress bars, and panels  
- **Click**: Underlying framework providing robust CLI capabilities
- **Type Annotations**: Full type safety with automatic validation
- **Argparse Compatibility**: Seamless integration with existing orchestrator

**Key Components:**
- `mad_cli.py`: Main CLI application with Typer commands
- `distributed_orchestrator.py`: Core orchestration logic
- Rich console integration for enhanced user experience
- Type-safe argument parsing and validation

### Extending the CLI

```python
# Example: Adding a new command
@app.command()
def new_command(
    param: Annotated[str, typer.Option("--param", help="Parameter description")]
) -> None:
    """New command description."""
    console.print(f"Executing with param: {param}")
```

## Troubleshooting

### Common Issues

#### Context Validation Errors
```
❌ Additional context is required for build-only operations
```
**Solution**: Provide context with `--additional-context` or `--additional-context-file`:
```bash
madengine-cli build --tags dummy \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'
```

#### Registry Connection Issues
```
❌ Failed to push to registry: connection refused
```
**Solutions**:
- Verify registry URL and connectivity
- Check authentication credentials
- Use `--verbose` for detailed error information

#### Build Failures
```
💥 Build failed for 2 models
```
**Debugging Steps**:
1. Use `--verbose` for detailed logs
2. Check `--summary-output` file for specific error details
3. Use `--live-output` to see real-time build progress
4. Try `--clean-docker-cache` to ensure clean builds

#### Timeout Issues
```
⏱️ Operation timed out after 3600 seconds
```
**Solutions**:
- Increase timeout: `--timeout 7200`
- Use `--timeout 0` for no timeout limit
- Check system resources and model complexity

### Debug Mode
```bash
# Enable comprehensive debugging
madengine-cli run --tags dummy \
  --verbose \
  --live-output \
  --keep-alive \
  --summary-output debug_summary.json
```

### Log Analysis
- **Build logs**: Available in Docker build output
- **Execution logs**: Captured in summary files and live output
- **Rich tracebacks**: Automatic in verbose mode with file/line information

## Exit Codes

The CLI uses specific exit codes for integration with scripts and CI/CD pipelines:

| Exit Code | Meaning | Description |
|-----------|---------|-------------|
| `0` | Success | All operations completed successfully |
| `1` | General failure | Unexpected errors or general failures |
| `2` | Build failure | Docker build or image creation failed |
| `3` | Run failure | Model execution or container runtime failed |
| `4` | Invalid arguments | Invalid command-line arguments or validation errors |

**CI/CD Integration Example:**
```bash
#!/bin/bash
madengine-cli build --tags production_models --registry prod.registry.com
build_exit_code=$?

if [ $build_exit_code -eq 2 ]; then
    echo "Build failed - stopping pipeline"
    exit 1
elif [ $build_exit_code -eq 0 ]; then
    echo "Build successful - proceeding to deployment"
    madengine-cli run --manifest-file build_manifest.json
fi
```

## Shell Completion

Enable shell completion for better developer experience:

### Bash
```bash
# Add to ~/.bashrc
eval "$(_MADENGINE_CLI_COMPLETE=bash_source madengine-cli)"
```

### Zsh  
```bash
# Add to ~/.zshrc
eval "$(_MADENGINE_CLI_COMPLETE=zsh_source madengine-cli)"
```

### Fish
```bash
# Add to ~/.config/fish/config.fish
eval (env _MADENGINE_CLI_COMPLETE=fish_source madengine-cli)
```

This enables tab completion for commands, options, and file paths, significantly improving the development experience.

---

*For additional help and examples, see the [Distributed Execution Solution Guide](distributed-execution-solution.md) and other documentation in the `docs/` directory.*
