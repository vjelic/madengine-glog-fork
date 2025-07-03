#!/usr/bin/env python3
"""
Command-line interface for MADEngine Distributed Orchestrator

This provides CLI commands for building and running models in distributed scenarios.
"""

import argparse
import sys
import os
import json
from madengine.tools.distributed_orchestrator import (
    DistributedOrchestrator, 
    create_ansible_playbook, 
    create_kubernetes_manifests
)

# -----------------------------------------------------------------------------
# Sub-command functions
# -----------------------------------------------------------------------------
# Router of the command-line arguments to the corresponding functions

def build_models(args: argparse.Namespace):
    """Build Docker images for models in distributed scenarios.
    
    Args:
        args: The command-line arguments.
    """
    print("Building models for distributed execution")
    orchestrator = DistributedOrchestrator(args)
    
    build_summary = orchestrator.build_phase(
        registry=args.registry,
        clean_cache=args.clean_docker_cache,
        manifest_output=args.manifest_output
    )
    
    # Save build summary
    if args.summary_output:
        with open(args.summary_output, 'w') as f:
            json.dump(build_summary, f, indent=2)
        print(f"Build summary saved to: {args.summary_output}")
    
    return len(build_summary["failed_builds"]) == 0


def run_models(args: argparse.Namespace):
    """Run model containers in distributed scenarios.
    
    Args:
        args: The command-line arguments.
    """
    print("Running models in distributed execution")
    orchestrator = DistributedOrchestrator(args)
    
    execution_summary = orchestrator.run_phase(
        manifest_file=args.manifest_file,
        registry=args.registry,
        timeout=args.timeout,
        keep_alive=args.keep_alive
    )
    
    # Save execution summary
    if args.summary_output:
        with open(args.summary_output, 'w') as f:
            json.dump(execution_summary, f, indent=2)
        print(f"Execution summary saved to: {args.summary_output}")
    
    return len(execution_summary["failed_runs"]) == 0


def full_workflow(args: argparse.Namespace):
    """Execute complete build and execution workflow.
    
    Args:
        args: The command-line arguments.
    """
    print("Running complete distributed workflow")
    orchestrator = DistributedOrchestrator(args)
    
    workflow_summary = orchestrator.full_workflow(
        registry=args.registry,
        clean_cache=args.clean_docker_cache,
        timeout=args.timeout,
        keep_alive=args.keep_alive
    )
    
    # Save workflow summary
    if args.summary_output:
        with open(args.summary_output, 'w') as f:
            json.dump(workflow_summary, f, indent=2)
        print(f"Workflow summary saved to: {args.summary_output}")
    
    return workflow_summary["overall_success"]


def generate_ansible(args: argparse.Namespace):
    """Generate Ansible playbook for distributed execution.
    
    Args:
        args: The command-line arguments.
    """
    print("Generating Ansible playbook")
    create_ansible_playbook(
        manifest_file=args.manifest_file,
        execution_config=args.execution_config,
        playbook_file=args.output
    )
    return True


def generate_k8s(args: argparse.Namespace):
    """Generate Kubernetes manifests for distributed execution.
    
    Args:
        args: The command-line arguments.
    """
    print("Generating Kubernetes manifests")
    create_kubernetes_manifests(
        manifest_file=args.manifest_file,
        execution_config=args.execution_config,
        namespace=args.namespace
    )
    return True


def export_config(args: argparse.Namespace):
    """Export execution configuration for external tools.
    
    Args:
        args: The command-line arguments.
    """
    print("Exporting execution configuration")
    orchestrator = DistributedOrchestrator(args)
    
    # Discover models to get configuration
    from madengine.tools.discover_models import DiscoverModels
    discover_models = DiscoverModels(args=args)
    models = discover_models.run()
    
    orchestrator.export_execution_config(models, args.output)
    return True


# -----------------------------------------------------------------------------
# Main function
# -----------------------------------------------------------------------------
def main():
    """Main function to parse the command-line arguments for distributed execution."""
    parser = argparse.ArgumentParser(
        description="MADEngine Distributed Orchestrator - Build and run models in distributed scenarios.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build models with specific tags and push to registry
  %(prog)s build --tags llama bert --registry localhost:5000 --clean-docker-cache
  
  # Run models using pre-built manifest with custom timeout
  %(prog)s run --manifest-file build_manifest.json --timeout 3600
  
  # Complete workflow with specific tags and registry
  %(prog)s full --tags resnet --registry localhost:5000 --timeout 3600 --live-output
  
  # Generate Ansible playbook for distributed execution
  %(prog)s generate ansible --output madengine.yml
  
  # Generate Kubernetes manifests with custom namespace
  %(prog)s generate k8s --namespace madengine-prod
        """
    )
    
    subparsers = parser.add_subparsers(title="Commands", description="Available commands for distributed model execution.", dest="command")
    
    # Function to add common model arguments
    def add_model_arguments(parser):
        """Add common model selection and context arguments."""
        parser.add_argument('--tags', nargs='+', default=[], 
                           help="tags to run (can be multiple).")
        parser.add_argument('--ignore-deprecated-flag', action='store_true', 
                           help="Force run deprecated models even if marked deprecated.")
        parser.add_argument('--additional-context-file', default=None, 
                           help="additional context, as json file, to filter behavior of workloads. Overrides detected contexts.")
        parser.add_argument('--additional-context', default='{}', 
                           help="additional context, as string representation of python dict, to filter behavior of workloads. Overrides detected contexts and additional-context-file.")
        parser.add_argument('--data-config-file-name', default="data.json", 
                           help="custom data configuration file.")
        parser.add_argument('--tools-json-file-name', default="./scripts/common/tools.json", 
                           help="custom tools json configuration file.")
        parser.add_argument('--generate-sys-env-details', default=True, 
                           help='generate system config env details by default')
        parser.add_argument('--force-mirror-local', default=None, 
                           help="Path to force all relevant dataproviders to mirror data locally on.")
        parser.add_argument('--disable-skip-gpu-arch', action='store_true', 
                           help="disables skipping model based on gpu architecture")

    # Function to add build-specific arguments  
    def add_build_arguments(parser):
        """Add build-specific arguments."""
        parser.add_argument('--registry', type=str,
                           help='Docker registry to push images to')
        parser.add_argument('--clean-docker-cache', action='store_true', 
                           help="rebuild docker image without using cache")
        parser.add_argument('--manifest-output', type=str, default='build_manifest.json',
                           help='Output file for build manifest (default: build_manifest.json)')
        parser.add_argument('--summary-output', type=str,
                           help='Output file for build summary JSON')
        parser.add_argument('--live-output', action='store_true', 
                           help="prints output in real-time directly on STDOUT")
        parser.add_argument('-o', '--output', default='perf.csv', 
                           help='output file')

    # Function to add run-specific arguments
    def add_run_arguments(parser):
        """Add run-specific arguments."""
        parser.add_argument('--manifest-file', type=str, default='build_manifest.json',
                           help='Build manifest file (default: build_manifest.json)')
        parser.add_argument('--registry', type=str,
                           help='Docker registry to pull images from')
        parser.add_argument('--timeout', type=int, default=-1, 
                           help="time out for model run in seconds; Overrides per-model timeout if specified or default timeout of 7200 (2 hrs). Timeout of 0 will never timeout.")
        parser.add_argument('--keep-alive', action='store_true', 
                           help="keep Docker container alive after run; will keep model directory after run")
        parser.add_argument('--keep-model-dir', action='store_true', 
                           help="keep model directory after run")
        parser.add_argument('--skip-model-run', action='store_true', 
                           help="skips running the model; will not keep model directory after run unless specified through keep-alive or keep-model-dir")
        parser.add_argument('--summary-output', type=str,
                           help='Output file for execution summary JSON')
        parser.add_argument('-o', '--output', default='perf.csv', 
                           help='output file')

    # Build command
    parser_build = subparsers.add_parser('build', 
                                        description="Build Docker images for models in distributed scenarios", 
                                        help='Build Docker images for models')
    add_model_arguments(parser_build)
    add_build_arguments(parser_build)
    parser_build.set_defaults(func=build_models)

    # Run command
    parser_run = subparsers.add_parser('run', 
                                      description="Run model containers in distributed scenarios", 
                                      help='Run model containers')
    add_model_arguments(parser_run)
    add_run_arguments(parser_run)
    parser_run.set_defaults(func=run_models)

    # Full workflow command
    parser_full = subparsers.add_parser('full', 
                                       description="Run complete build and execution workflow", 
                                       help='Run complete build and execution workflow')
    add_model_arguments(parser_full)
    add_build_arguments(parser_full)
    # Add some run arguments for full workflow
    parser_full.add_argument('--timeout', type=int, default=-1, 
                           help="time out for model run in seconds; Overrides per-model timeout if specified or default timeout of 7200 (2 hrs). Timeout of 0 will never timeout.")
    parser_full.add_argument('--keep-alive', action='store_true', 
                           help="keep Docker container alive after run; will keep model directory after run")
    parser_full.add_argument('--keep-model-dir', action='store_true', 
                           help="keep model directory after run")
    parser_full.add_argument('--skip-model-run', action='store_true', 
                           help="skips running the model; will not keep model directory after run unless specified through keep-alive or keep-model-dir")
    parser_full.set_defaults(func=full_workflow)

    # Generate command group
    parser_generate = subparsers.add_parser('generate', help='Generate orchestration files')
    subparsers_generate = parser_generate.add_subparsers(title="Generate Commands", 
                                                        description="Available commands for generating orchestration files.", 
                                                        dest="generate_command")
    
    # Generate Ansible subcommand
    parser_generate_ansible = subparsers_generate.add_parser('ansible', 
                                                           description="Generate Ansible playbook for distributed execution", 
                                                           help='Generate Ansible playbook')
    parser_generate_ansible.add_argument('--manifest-file', type=str, default='build_manifest.json',
                                       help='Build manifest file (default: build_manifest.json)')
    parser_generate_ansible.add_argument('--execution-config', type=str, default='execution_config.json',
                                       help='Execution config file (default: execution_config.json)')
    parser_generate_ansible.add_argument('--output', type=str, default='madengine_distributed.yml',
                                       help='Output Ansible playbook file (default: madengine_distributed.yml)')
    parser_generate_ansible.set_defaults(func=generate_ansible)

    # Generate Kubernetes subcommand
    parser_generate_k8s = subparsers_generate.add_parser('k8s',
                                                        description="Generate Kubernetes manifests for distributed execution", 
                                                        help='Generate Kubernetes manifests')
    parser_generate_k8s.add_argument('--manifest-file', type=str, default='build_manifest.json',
                                   help='Build manifest file (default: build_manifest.json)')
    parser_generate_k8s.add_argument('--execution-config', type=str, default='execution_config.json',
                                   help='Execution config file (default: execution_config.json)')
    parser_generate_k8s.add_argument('--namespace', type=str, default='madengine',
                                   help='Kubernetes namespace (default: madengine)')
    parser_generate_k8s.set_defaults(func=generate_k8s)

    # Export config command
    parser_export = subparsers.add_parser('export-config',
                                         description="Export execution configuration for external tools", 
                                         help='Export execution configuration')
    add_model_arguments(parser_export)
    parser_export.add_argument('--output', type=str, default='execution_config.json',
                              help='Output configuration file (default: execution_config.json)')
    parser_export.set_defaults(func=export_config)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        success = args.func(args)
        return 0 if success else 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
