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
        clean_cache=args.clean_cache,
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
        clean_cache=args.clean_cache,
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
  # Build all models and push to registry
  %(prog)s build --registry localhost:5000 --clean-cache
  
  # Run models using pre-built manifest
  %(prog)s run --manifest-file build_manifest.json
  
  # Complete workflow with registry
  %(prog)s full --registry localhost:5000 --timeout 3600
  
  # Generate Ansible playbook
  %(prog)s generate-ansible --output madengine.yml
  
  # Generate Kubernetes manifests
  %(prog)s generate-k8s --namespace madengine-prod
        """
    )
    
    # Common arguments
    parser.add_argument('--live-output', action='store_true', default=True,
                       help='Enable live output (default: True)')
    parser.add_argument('--additional-context', type=str,
                       help='Additional context string')
    parser.add_argument('--additional-context-file', type=str,
                       help='Additional context file')
    parser.add_argument('--data-config-file-name', type=str, default='data.json',
                       help='Data configuration file (default: data.json)')
    parser.add_argument('--force-mirror-local', action='store_true',
                       help='Force local mirroring of data')
    parser.add_argument('--model', type=str, 
                       help='Specific model to process')
    parser.add_argument('--dockerfile', type=str,
                       help='Dockerfile pattern to use')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build Docker images for models')
    build_parser.add_argument('--registry', type=str,
                             help='Docker registry to push images to')
    build_parser.add_argument('--clean-cache', action='store_true',
                             help='Use --no-cache for Docker builds')
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
    run_parser.add_argument('--timeout', type=int, default=7200,
                           help='Execution timeout per model in seconds (default: 7200)')
    run_parser.add_argument('--keep-alive', action='store_true',
                           help='Keep containers alive after execution')
    run_parser.add_argument('--summary-output', type=str,
                           help='Output file for execution summary JSON')
    
    # Full workflow command
    full_parser = subparsers.add_parser('full', help='Run complete build and execution workflow')
    full_parser.add_argument('--registry', type=str,
                            help='Docker registry for image distribution')
    full_parser.add_argument('--clean-cache', action='store_true',
                            help='Use --no-cache for Docker builds')
    full_parser.add_argument('--timeout', type=int, default=7200,
                            help='Execution timeout per model in seconds (default: 7200)')
    full_parser.add_argument('--keep-alive', action='store_true',
                            help='Keep containers alive after execution')
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
