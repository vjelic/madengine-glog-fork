# madengine-cli: Modern CLI for madengine

A production-ready, modern command-line interface for the madengine Distributed Orchestrator built with Typer and Rich.

## Features

🚀 **Modern Design**: Built with Typer for excellent CLI experience and Rich for beautiful terminal output  
📊 **Rich Output**: Progress bars, tables, panels, and syntax highlighting  
✅ **Better Error Handling**: Clear error messages with helpful suggestions  
🎯 **Type Safety**: Full type annotations with automatic validation  
📝 **Auto-completion**: Built-in shell completion support  
🎨 **Colorful Interface**: Beautiful, informative output with emojis and colors  
⚡ **Performance**: Optimized for speed and responsiveness  

## Installation

The new CLI will be available after installing the updated package:

```bash
pip install -e .
```

## Usage

### Basic Commands

#### Build Models
```bash
# Build models with specific tags
madengine-cli build --tags dummy resnet --registry localhost:5000

# Build with additional context (required for build-only operations)
madengine-cli build --tags llama --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'

# Build with context from file
madengine-cli build --tags bert --additional-context-file context.json --clean-cache
```

#### Run Models
```bash
# Run complete workflow (build + run)
madengine-cli run --tags dummy --registry localhost:5000 --timeout 3600

# Run using existing manifest (execution only)
madengine-cli run --manifest-file build_manifest.json --timeout 1800

# Run with live output
madengine-cli run --tags resnet --live-output --verbose
```

#### Generate Orchestration Files
```bash
# Generate Ansible playbook
madengine-cli generate ansible --output my-playbook.yml

# Generate Kubernetes manifests
madengine-cli generate k8s --namespace production

# Export configuration
madengine-cli export-config --tags dummy --output execution.json
```

### Advanced Examples

#### Production Build and Deploy
```bash
# 1. Build models for production
madengine-cli build \
  --tags llama bert resnet \
  --registry production.registry.com \
  --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}' \
  --clean-cache \
  --summary-output build_summary.json \
  --verbose

# 2. Run with timeout and keep containers alive for debugging
madengine-cli run \
  --manifest-file build_manifest.json \
  --timeout 7200 \
  --keep-alive \
  --summary-output run_summary.json
```

#### Multi-Environment Workflow
```bash
# Development environment
madengine-cli build --tags dummy --additional-context-file dev-context.json

# Production environment  
madengine-cli build --tags llama bert --additional-context-file prod-context.json --registry prod.registry.com

# Generate deployment manifests
madengine-cli generate k8s --namespace madengine-prod --execution-config prod-execution.json
```

## Command Reference

### Global Options
- `--verbose, -v`: Enable verbose logging with detailed output
- `--version`: Show version information

### Build Command
```bash
madengine-cli build [OPTIONS]
```

**Options:**
- `--tags, -t`: Model tags to build (multiple allowed)
- `--registry, -r`: Docker registry URL
- `--additional-context, -c`: Additional context as JSON string
- `--additional-context-file, -f`: File containing additional context JSON
- `--clean-cache`: Rebuild without using Docker cache
- `--manifest-output, -m`: Output file for build manifest
- `--summary-output, -s`: Output file for build summary JSON
- `--live-output, -l`: Print output in real-time
- `--output, -o`: Performance output file

### Run Command
```bash
madengine-cli run [OPTIONS]
```

**Options:**
- `--tags, -t`: Model tags to run (multiple allowed)
- `--manifest-file, -m`: Build manifest file path
- `--registry, -r`: Docker registry URL
- `--timeout`: Timeout in seconds (-1 for default, 0 for no timeout)
- `--keep-alive`: Keep containers alive after run
- `--keep-model-dir`: Keep model directory after run
- `--skip-model-run`: Skip running the model
- All build options (for full workflow mode)

### Generate Commands
```bash
madengine-cli generate ansible [OPTIONS]
madengine-cli generate k8s [OPTIONS]
```

**Ansible Options:**
- `--manifest-file, -m`: Build manifest file
- `--execution-config, -e`: Execution config file
- `--output, -o`: Output playbook file

**Kubernetes Options:**
- `--manifest-file, -m`: Build manifest file
- `--execution-config, -e`: Execution config file
- `--namespace, -n`: Kubernetes namespace

### Export Config Command
```bash
madengine-cli export-config [OPTIONS]
```

**Options:**
- `--tags, -t`: Model tags to export config for
- `--output, -o`: Output configuration file
- Standard model selection options

## Configuration Files

### Additional Context File (context.json)
```json
{
  "gpu_vendor": "AMD",
  "guest_os": "UBUNTU",
  "custom_option": "value"
}
```

**Required for build-only operations:**
- `gpu_vendor`: AMD, NVIDIA, INTEL
- `guest_os`: UBUNTU, CENTOS, ROCKY

### Execution Config File
Generated automatically or can be exported using `export-config` command.

## Output Features

### Rich Tables
Results are displayed in beautiful tables showing:
- ✅ Successful builds/runs
- ❌ Failed builds/runs  
- 📊 Counts and item lists

### Progress Indicators
- 🔄 Spinner animations during operations
- 📈 Progress bars for long-running tasks
- ⏱️ Real-time status updates

### Error Handling
- 🎯 Clear error messages with context
- 💡 Helpful suggestions for fixing issues
- 🔍 Detailed stack traces in verbose mode

### Panels and Formatting
- 📋 Configuration panels showing current settings
- 🎨 Syntax highlighted JSON output
- 🏷️ Color-coded status indicators

## Differences from Original CLI

### Improvements
1. **Better UX**: Rich output, progress bars, helpful error messages
2. **Type Safety**: Full type annotations and automatic validation
3. **Modern Architecture**: Clean separation of concerns, testable code
4. **Enhanced Output**: Tables, panels, and formatted displays
5. **Better Error Handling**: Context-aware error messages with suggestions
6. **Auto-completion**: Built-in shell completion support

### Backward Compatibility
- All original functionality is preserved
- Command structure is mostly the same
- New CLI is available as `madengine-cli` while original remains as `madengine`

## Development

### Running Tests
```bash
# Test the new CLI
madengine-cli --help
madengine-cli build --help
madengine-cli run --help

# Compare with original
madengine-cli --help
```

### Adding New Features
The new CLI is built with:
- **Typer**: For command-line parsing and validation
- **Rich**: For beautiful terminal output
- **Click**: Underlying framework (via Typer)

See the source code in `src/madengine/mad_cli.py` for implementation details.
