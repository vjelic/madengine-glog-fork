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


def build_command(args):
    """Handle the build command."""
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


def run_command(args):
    """Handle the run command."""
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


def full_command(args):
    """Handle the full workflow command."""
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


def generate_ansible_command(args):
    """Handle Ansible playbook generation."""
    create_ansible_playbook(
        manifest_file=args.manifest_file,
        execution_config=args.execution_config,
        playbook_file=args.output
    )
    return True


def generate_k8s_command(args):
    """Handle Kubernetes manifest generation."""
    create_kubernetes_manifests(
        manifest_file=args.manifest_file,
        execution_config=args.execution_config,
        namespace=args.namespace
    )
    return True


def export_config_command(args):
    """Handle configuration export."""
    orchestrator = DistributedOrchestrator(args)
    
    # Discover models to get configuration
    from madengine.tools.discover_models import DiscoverModels
    discover_models = DiscoverModels(args=args)
    models = discover_models.run()
    
    orchestrator.export_execution_config(models, args.output)
    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MADEngine Distributed Orchestrator",
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
  %(prog)s generate-ansible --output madengine.yml
  
  # Generate Kubernetes manifests with custom namespace
  %(prog)s generate-k8s --namespace madengine-prod --tags llama
        """
    )
    
    # Common arguments - aligned with mad.py run command
    parser.add_argument('--tags', nargs='+', default=[], 
                       help="tags to run (can be multiple).")
    parser.add_argument('--ignore-deprecated-flag', action='store_true', 
                       help="Force run deprecated models even if marked deprecated.")
    parser.add_argument('--timeout', type=int, default=-1, 
                       help="time out for model run in seconds; Overrides per-model timeout if specified or default timeout of 7200 (2 hrs). Timeout of 0 will never timeout.")
    parser.add_argument('--live-output', action='store_true', 
                       help="prints output in real-time directly on STDOUT")
    parser.add_argument('--clean-docker-cache', action='store_true', 
                       help="rebuild docker image without using cache")
    parser.add_argument('--additional-context-file', default=None, 
                       help="additonal context, as json file, to filter behavior of workloads. Overrides detected contexts.")
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
    parser.add_argument('--keep-alive', action='store_true', 
                       help="keep Docker container alive after run; will keep model directory after run")
    parser.add_argument('--keep-model-dir', action='store_true', 
                       help="keep model directory after run")
    parser.add_argument('--skip-model-run', action='store_true', 
                       help="skips running the model; will not keep model directory after run unless specified through keep-alive or keep-model-dir")
    parser.add_argument('--disable-skip-gpu-arch', action='store_true', 
                       help="disables skipping model based on gpu architecture")
    parser.add_argument('-o', '--output', default='perf.csv', 
                       help='output file')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build Docker images for models')
    build_parser.add_argument('--registry', type=str,
                             help='Docker registry to push images to')
    build_parser.add_argument('--manifest-output', type=str, default='build_manifest.json',
                             help='Output file for build manifest (default: build_manifest.json)')
    build_parser.add_argument('--summary-output', type=str,
                             help='Output file for build summary JSON')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run model containers')
    run_parser.add_argument('--manifest-file', type=str, default='build_manifest.json',
                           help='Build manifest file (default: build_manifest.json)')
    run_parser.add_argument('--registry', type=str,
                           help='Docker registry to pull images from')
    run_parser.add_argument('--summary-output', type=str,
                           help='Output file for execution summary JSON')
    
    # Full workflow command
    full_parser = subparsers.add_parser('full', help='Run complete build and execution workflow')
    full_parser.add_argument('--registry', type=str,
                            help='Docker registry for image distribution')
    full_parser.add_argument('--summary-output', type=str,
                            help='Output file for complete workflow summary JSON')
    
    # Generate Ansible command
    ansible_parser = subparsers.add_parser('generate-ansible', 
                                          help='Generate Ansible playbook for distributed execution')
    ansible_parser.add_argument('--manifest-file', type=str, default='build_manifest.json',
                               help='Build manifest file (default: build_manifest.json)')
    ansible_parser.add_argument('--execution-config', type=str, default='execution_config.json',
                               help='Execution config file (default: execution_config.json)')
    ansible_parser.add_argument('--output', type=str, default='madengine_distributed.yml',
                               help='Output Ansible playbook file (default: madengine_distributed.yml)')
    
    # Generate Kubernetes command
    k8s_parser = subparsers.add_parser('generate-k8s',
                                      help='Generate Kubernetes manifests for distributed execution')
    k8s_parser.add_argument('--manifest-file', type=str, default='build_manifest.json',
                           help='Build manifest file (default: build_manifest.json)')
    k8s_parser.add_argument('--execution-config', type=str, default='execution_config.json',
                           help='Execution config file (default: execution_config.json)')
    k8s_parser.add_argument('--namespace', type=str, default='madengine',
                           help='Kubernetes namespace (default: madengine)')
    
    # Export config command
    export_parser = subparsers.add_parser('export-config',
                                         help='Export execution configuration for external tools')
    export_parser.add_argument('--output', type=str, default='execution_config.json',
                              help='Output configuration file (default: execution_config.json)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Command mapping
    commands = {
        'build': build_command,
        'run': run_command, 
        'full': full_command,
        'generate-ansible': generate_ansible_command,
        'generate-k8s': generate_k8s_command,
        'export-config': export_config_command,
    }
    
    try:
        success = commands[args.command](args)
        return 0 if success else 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
