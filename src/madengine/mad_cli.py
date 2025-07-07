#!/usr/bin/env python3
"""
Modern CLI for madengine Distributed Orchestrator

Production-ready command-line interface built with Typer and Rich
for building and running models in distributed scenarios.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    from typing import Annotated  # Python 3.9+
except ImportError:
    from typing_extensions import Annotated  # Python 3.8

import typer
from rich import print as rprint
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.traceback import install

# Install rich traceback handler for better error displays
install(show_locals=True)

# Initialize Rich console
console = Console()

# Import madengine components
from madengine.tools.distributed_orchestrator import (
    DistributedOrchestrator,
    create_ansible_playbook,
    create_kubernetes_manifests,
)

# Initialize the main Typer app
app = typer.Typer(
    name="madengine-cli",
    help="🚀 madengine Distributed Orchestrator - Build and run AI models in distributed scenarios",
    rich_markup_mode="rich",
    add_completion=False,
    no_args_is_help=True,
)

# Sub-applications for organized commands
generate_app = typer.Typer(
    name="generate",
    help="📋 Generate orchestration files (Ansible, Kubernetes)",
    rich_markup_mode="rich",
)
app.add_typer(generate_app, name="generate")

# Constants
DEFAULT_MANIFEST_FILE = "build_manifest.json"
DEFAULT_EXECUTION_CONFIG = "execution_config.json"
DEFAULT_PERF_OUTPUT = "perf.csv"
DEFAULT_DATA_CONFIG = "data.json"
DEFAULT_TOOLS_CONFIG = "./scripts/common/tools.json"
DEFAULT_ANSIBLE_OUTPUT = "madengine_distributed.yml"
DEFAULT_K8S_NAMESPACE = "madengine"
DEFAULT_TIMEOUT = -1

# Exit codes
class ExitCode:
    SUCCESS = 0
    FAILURE = 1
    BUILD_FAILURE = 2
    RUN_FAILURE = 3
    INVALID_ARGS = 4


# Valid values for validation
VALID_GPU_VENDORS = ["AMD", "NVIDIA", "INTEL"]
VALID_GUEST_OS = ["UBUNTU", "CENTOS", "ROCKY"]


def setup_logging(verbose: bool = False) -> None:
    """Setup Rich logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Setup rich logging handler
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=verbose,
        markup=True,
        rich_tracebacks=True,
    )
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[rich_handler],
    )


def create_args_namespace(**kwargs) -> object:
    """Create an argparse.Namespace-like object from keyword arguments."""
    class Args:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    return Args(**kwargs)


def validate_additional_context(
    additional_context: str,
    additional_context_file: Optional[str] = None,
) -> Dict[str, str]:
    """
    Validate and parse additional context.
    
    Args:
        additional_context: JSON string containing additional context
        additional_context_file: Optional file containing additional context
        
    Returns:
        Dict containing parsed additional context
        
    Raises:
        typer.Exit: If validation fails
    """
    context = {}
    
    # Load from file first
    if additional_context_file:
        try:
            with open(additional_context_file, 'r') as f:
                context = json.load(f)
            console.print(f"✅ Loaded additional context from file: [cyan]{additional_context_file}[/cyan]")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            console.print(f"❌ Failed to load additional context file: [red]{e}[/red]")
            raise typer.Exit(ExitCode.INVALID_ARGS)
    
    # Parse string context (overrides file)
    if additional_context and additional_context != '{}':
        try:
            string_context = json.loads(additional_context)
            context.update(string_context)
            console.print("✅ Loaded additional context from command line")
        except json.JSONDecodeError as e:
            console.print(f"❌ Invalid JSON in additional context: [red]{e}[/red]")
            console.print("💡 Please provide valid JSON format")
            raise typer.Exit(ExitCode.INVALID_ARGS)
    
    if not context:
        console.print("❌ [red]No additional context provided[/red]")
        console.print("💡 For build operations, you must provide additional context with gpu_vendor and guest_os")
        
        # Show example usage
        example_panel = Panel(
            """[bold cyan]Example usage:[/bold cyan]
madengine-cli build --tags dummy --additional-context '{"gpu_vendor": "AMD", "guest_os": "UBUNTU"}'

[bold cyan]Or using a file:[/bold cyan]
madengine-cli build --tags dummy --additional-context-file context.json

[bold cyan]Required fields:[/bold cyan]
• gpu_vendor: [green]AMD[/green], [green]NVIDIA[/green], [green]INTEL[/green]
• guest_os: [green]UBUNTU[/green], [green]CENTOS[/green], [green]ROCKY[/green]""",
            title="Additional Context Help",
            border_style="blue",
        )
        console.print(example_panel)
        raise typer.Exit(ExitCode.INVALID_ARGS)
    
    # Validate required fields
    required_fields = ['gpu_vendor', 'guest_os']
    missing_fields = [field for field in required_fields if field not in context]
    
    if missing_fields:
        console.print(f"❌ Missing required fields: [red]{', '.join(missing_fields)}[/red]")
        console.print("💡 Both gpu_vendor and guest_os are required for build operations")
        raise typer.Exit(ExitCode.INVALID_ARGS)
    
    # Validate gpu_vendor
    gpu_vendor = context['gpu_vendor'].upper()
    if gpu_vendor not in VALID_GPU_VENDORS:
        console.print(f"❌ Invalid gpu_vendor: [red]{context['gpu_vendor']}[/red]")
        console.print(f"💡 Supported values: [green]{', '.join(VALID_GPU_VENDORS)}[/green]")
        raise typer.Exit(ExitCode.INVALID_ARGS)
    
    # Validate guest_os
    guest_os = context['guest_os'].upper()
    if guest_os not in VALID_GUEST_OS:
        console.print(f"❌ Invalid guest_os: [red]{context['guest_os']}[/red]")
        console.print(f"💡 Supported values: [green]{', '.join(VALID_GUEST_OS)}[/green]")
        raise typer.Exit(ExitCode.INVALID_ARGS)
    
    console.print(f"✅ Context validated: [green]{gpu_vendor}[/green] + [green]{guest_os}[/green]")
    return context


def save_summary_with_feedback(summary: Dict, output_path: Optional[str], summary_type: str) -> None:
    """Save summary to file with user feedback."""
    if output_path:
        try:
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            console.print(f"💾 {summary_type} summary saved to: [cyan]{output_path}[/cyan]")
        except IOError as e:
            console.print(f"❌ Failed to save {summary_type} summary: [red]{e}[/red]")
            raise typer.Exit(ExitCode.FAILURE)


def display_results_table(summary: Dict, title: str) -> None:
    """Display results in a formatted table."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Items", style="dim")
    
    successful = summary.get("successful_builds", summary.get("successful_runs", []))
    failed = summary.get("failed_builds", summary.get("failed_runs", []))
    
    # Helper function to extract display names from items
    def get_display_names(items, limit=5):
        if not items:
            return ""
        
        display_items = []
        for item in items[:limit]:
            if isinstance(item, dict):
                # For dictionary items (run results), use model name or name field
                name = item.get("model", item.get("name", str(item)[:20]))
                display_items.append(name)
            else:
                # For string items (build results), use as-is
                display_items.append(str(item))
        
        result = ", ".join(display_items)
        if len(items) > limit:
            result += "..."
        return result
    
    if successful:
        table.add_row("✅ Success", str(len(successful)), get_display_names(successful))
    
    if failed:
        table.add_row("❌ Failed", str(len(failed)), get_display_names(failed))
    
    if not successful and not failed:
        table.add_row("ℹ️ No items", "0", "")
    
    console.print(table)


@app.command()
def build(
    tags: Annotated[List[str], typer.Option("--tags", "-t", help="Model tags to build (can specify multiple)")] = [],
    registry: Annotated[Optional[str], typer.Option("--registry", "-r", help="Docker registry to push images to")] = None,
    additional_context: Annotated[str, typer.Option("--additional-context", "-c", help="Additional context as JSON string")] = "{}",
    additional_context_file: Annotated[Optional[str], typer.Option("--additional-context-file", "-f", help="File containing additional context JSON")] = None,
    clean_docker_cache: Annotated[bool, typer.Option("--clean-docker-cache", help="Rebuild images without using cache")] = False,
    manifest_output: Annotated[str, typer.Option("--manifest-output", "-m", help="Output file for build manifest")] = DEFAULT_MANIFEST_FILE,
    summary_output: Annotated[Optional[str], typer.Option("--summary-output", "-s", help="Output file for build summary JSON")] = None,
    live_output: Annotated[bool, typer.Option("--live-output", "-l", help="Print output in real-time")] = False,
    output: Annotated[str, typer.Option("--output", "-o", help="Performance output file")] = DEFAULT_PERF_OUTPUT,
    ignore_deprecated_flag: Annotated[bool, typer.Option("--ignore-deprecated", help="Force run deprecated models")] = False,
    data_config_file_name: Annotated[str, typer.Option("--data-config", help="Custom data configuration file")] = DEFAULT_DATA_CONFIG,
    tools_json_file_name: Annotated[str, typer.Option("--tools-config", help="Custom tools JSON configuration")] = DEFAULT_TOOLS_CONFIG,
    generate_sys_env_details: Annotated[bool, typer.Option("--sys-env-details", help="Generate system config env details")] = True,
    force_mirror_local: Annotated[Optional[str], typer.Option("--force-mirror-local", help="Path to force local data mirroring")] = None,
    disable_skip_gpu_arch: Annotated[bool, typer.Option("--disable-skip-gpu-arch", help="Disable skipping models based on GPU architecture")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
) -> None:
    """
    🔨 Build Docker images for models in distributed scenarios.
    
    This command builds Docker images for the specified model tags and optionally
    pushes them to a registry. Additional context with gpu_vendor and guest_os
    is required for build-only operations.
    """
    setup_logging(verbose)
    
    console.print(Panel(
        f"🔨 [bold cyan]Building Models[/bold cyan]\n"
        f"Tags: [yellow]{', '.join(tags) if tags else 'All models'}[/yellow]\n"
        f"Registry: [yellow]{registry or 'Local only'}[/yellow]",
        title="Build Configuration",
        border_style="blue"
    ))
    
    try:
        # Validate additional context
        validate_additional_context(additional_context, additional_context_file)
        
        # Create arguments object
        args = create_args_namespace(
            tags=tags,
            registry=registry,
            additional_context=additional_context,
            additional_context_file=additional_context_file,
            clean_docker_cache=clean_docker_cache,
            manifest_output=manifest_output,
            live_output=live_output,
            output=output,
            ignore_deprecated_flag=ignore_deprecated_flag,
            data_config_file_name=data_config_file_name,
            tools_json_file_name=tools_json_file_name,
            generate_sys_env_details=generate_sys_env_details,
            force_mirror_local=force_mirror_local,
            disable_skip_gpu_arch=disable_skip_gpu_arch,
            verbose=verbose,
            _separate_phases=True,
        )
        
        # Initialize orchestrator in build-only mode
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing build orchestrator...", total=None)
            orchestrator = DistributedOrchestrator(args, build_only_mode=True)
            progress.update(task, description="Building models...")
            
            build_summary = orchestrator.build_phase(
                registry=registry,
                clean_cache=clean_docker_cache,
                manifest_output=manifest_output
            )
            progress.update(task, description="Build completed!")
        
        # Display results
        display_results_table(build_summary, "Build Results")
        
        # Save summary
        save_summary_with_feedback(build_summary, summary_output, "Build")
        
        # Check results and exit
        failed_builds = len(build_summary.get("failed_builds", []))
        if failed_builds == 0:
            console.print("🎉 [bold green]All builds completed successfully![/bold green]")
            raise typer.Exit(ExitCode.SUCCESS)
        else:
            console.print(f"💥 [bold red]Build failed for {failed_builds} models[/bold red]")
            raise typer.Exit(ExitCode.BUILD_FAILURE)
            
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"💥 [bold red]Build process failed: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(ExitCode.FAILURE)


@app.command()
def run(
    tags: Annotated[List[str], typer.Option("--tags", "-t", help="Model tags to run (can specify multiple)")] = [],
    manifest_file: Annotated[str, typer.Option("--manifest-file", "-m", help="Build manifest file path")] = "",
    registry: Annotated[Optional[str], typer.Option("--registry", "-r", help="Docker registry URL")] = None,
    timeout: Annotated[int, typer.Option("--timeout", help="Timeout for model run in seconds (-1 for default, 0 for no timeout)")] = DEFAULT_TIMEOUT,
    additional_context: Annotated[str, typer.Option("--additional-context", "-c", help="Additional context as JSON string")] = "{}",
    additional_context_file: Annotated[Optional[str], typer.Option("--additional-context-file", "-f", help="File containing additional context JSON")] = None,
    keep_alive: Annotated[bool, typer.Option("--keep-alive", help="Keep Docker containers alive after run")] = False,
    keep_model_dir: Annotated[bool, typer.Option("--keep-model-dir", help="Keep model directory after run")] = False,
    skip_model_run: Annotated[bool, typer.Option("--skip-model-run", help="Skip running the model")] = False,
    clean_docker_cache: Annotated[bool, typer.Option("--clean-docker-cache", help="Rebuild images without using cache (for full workflow)")] = False,
    manifest_output: Annotated[str, typer.Option("--manifest-output", help="Output file for build manifest (full workflow)")] = DEFAULT_MANIFEST_FILE,
    summary_output: Annotated[Optional[str], typer.Option("--summary-output", "-s", help="Output file for summary JSON")] = None,
    live_output: Annotated[bool, typer.Option("--live-output", "-l", help="Print output in real-time")] = False,
    output: Annotated[str, typer.Option("--output", "-o", help="Performance output file")] = DEFAULT_PERF_OUTPUT,
    ignore_deprecated_flag: Annotated[bool, typer.Option("--ignore-deprecated", help="Force run deprecated models")] = False,
    data_config_file_name: Annotated[str, typer.Option("--data-config", help="Custom data configuration file")] = DEFAULT_DATA_CONFIG,
    tools_json_file_name: Annotated[str, typer.Option("--tools-config", help="Custom tools JSON configuration")] = DEFAULT_TOOLS_CONFIG,
    generate_sys_env_details: Annotated[bool, typer.Option("--sys-env-details", help="Generate system config env details")] = True,
    force_mirror_local: Annotated[Optional[str], typer.Option("--force-mirror-local", help="Path to force local data mirroring")] = None,
    disable_skip_gpu_arch: Annotated[bool, typer.Option("--disable-skip-gpu-arch", help="Disable skipping models based on GPU architecture")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
) -> None:
    """
    🚀 Run model containers in distributed scenarios.
    
    If manifest-file is provided and exists, runs execution phase only.
    Otherwise runs the complete workflow (build + run).
    """
    setup_logging(verbose)
    
    # Input validation
    if timeout < -1:
        console.print("❌ [red]Timeout must be -1 (default) or a positive integer[/red]")
        raise typer.Exit(ExitCode.INVALID_ARGS)
    
    try:
        # Check if we're doing execution-only or full workflow
        manifest_exists = manifest_file and os.path.exists(manifest_file)
        
        if manifest_exists:
            console.print(Panel(
                f"🚀 [bold cyan]Running Models (Execution Only)[/bold cyan]\n"
                f"Manifest: [yellow]{manifest_file}[/yellow]\n"
                f"Registry: [yellow]{registry or 'Auto-detected'}[/yellow]\n"
                f"Timeout: [yellow]{timeout if timeout != -1 else 'Default'}[/yellow]s",
                title="Execution Configuration",
                border_style="green"
            ))
            
            # Create arguments object for execution only
            args = create_args_namespace(
                tags=tags,
                manifest_file=manifest_file,
                registry=registry,
                timeout=timeout,
                keep_alive=keep_alive,
                keep_model_dir=keep_model_dir,
                skip_model_run=skip_model_run,
                live_output=live_output,
                output=output,
                ignore_deprecated_flag=ignore_deprecated_flag,
                data_config_file_name=data_config_file_name,
                tools_json_file_name=tools_json_file_name,
                generate_sys_env_details=generate_sys_env_details,
                force_mirror_local=force_mirror_local,
                disable_skip_gpu_arch=disable_skip_gpu_arch,
                verbose=verbose,
                _separate_phases=True,
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Initializing execution orchestrator...", total=None)
                orchestrator = DistributedOrchestrator(args)
                progress.update(task, description="Running models...")
                
                execution_summary = orchestrator.run_phase(
                    manifest_file=manifest_file,
                    registry=registry,
                    timeout=timeout,
                    keep_alive=keep_alive
                )
                progress.update(task, description="Execution completed!")
            
            # Display results
            display_results_table(execution_summary, "Execution Results")
            save_summary_with_feedback(execution_summary, summary_output, "Execution")
            
            failed_runs = len(execution_summary.get("failed_runs", []))
            if failed_runs == 0:
                console.print("🎉 [bold green]All model executions completed successfully![/bold green]")
                raise typer.Exit(ExitCode.SUCCESS)
            else:
                console.print(f"💥 [bold red]Execution failed for {failed_runs} models[/bold red]")
                raise typer.Exit(ExitCode.RUN_FAILURE)
        
        else:
            # Full workflow
            if manifest_file:
                console.print(f"⚠️  Manifest file [yellow]{manifest_file}[/yellow] not found, running complete workflow")
            
            console.print(Panel(
                f"🔨🚀 [bold cyan]Complete Workflow (Build + Run)[/bold cyan]\n"
                f"Tags: [yellow]{', '.join(tags) if tags else 'All models'}[/yellow]\n"
                f"Registry: [yellow]{registry or 'Local only'}[/yellow]\n"
                f"Timeout: [yellow]{timeout if timeout != -1 else 'Default'}[/yellow]s",
                title="Workflow Configuration",
                border_style="magenta"
            ))
            
            # Create arguments object for full workflow
            args = create_args_namespace(
                tags=tags,
                registry=registry,
                timeout=timeout,
                additional_context=additional_context,
                additional_context_file=additional_context_file,
                keep_alive=keep_alive,
                keep_model_dir=keep_model_dir,
                skip_model_run=skip_model_run,
                clean_docker_cache=clean_docker_cache,
                manifest_output=manifest_output,
                live_output=live_output,
                output=output,
                ignore_deprecated_flag=ignore_deprecated_flag,
                data_config_file_name=data_config_file_name,
                tools_json_file_name=tools_json_file_name,
                generate_sys_env_details=generate_sys_env_details,
                force_mirror_local=force_mirror_local,
                disable_skip_gpu_arch=disable_skip_gpu_arch,
                verbose=verbose,
                _separate_phases=True,
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Build phase
                task = progress.add_task("Initializing workflow orchestrator...", total=None)
                orchestrator = DistributedOrchestrator(args)
                
                progress.update(task, description="Building models...")
                build_summary = orchestrator.build_phase(
                    registry=registry,
                    clean_cache=clean_docker_cache,
                    manifest_output=manifest_output
                )
                
                failed_builds = len(build_summary.get("failed_builds", []))
                if failed_builds > 0:
                    progress.update(task, description="Build failed!")
                    console.print(f"💥 [bold red]Build failed for {failed_builds} models, aborting workflow[/bold red]")
                    display_results_table(build_summary, "Build Results")
                    raise typer.Exit(ExitCode.BUILD_FAILURE)
                
                # Run phase
                progress.update(task, description="Running models...")
                execution_summary = orchestrator.run_phase(
                    manifest_file=manifest_output,
                    registry=registry,
                    timeout=timeout,
                    keep_alive=keep_alive
                )
                progress.update(task, description="Workflow completed!")
            
            # Combine summaries
            workflow_summary = {
                "build_phase": build_summary,
                "run_phase": execution_summary,
                "overall_success": (
                    len(build_summary.get("failed_builds", [])) == 0 and
                    len(execution_summary.get("failed_runs", [])) == 0
                )
            }
            
            # Display results
            display_results_table(build_summary, "Build Results")
            display_results_table(execution_summary, "Execution Results")
            save_summary_with_feedback(workflow_summary, summary_output, "Workflow")
            
            if workflow_summary["overall_success"]:
                console.print("🎉 [bold green]Complete workflow finished successfully![/bold green]")
                raise typer.Exit(ExitCode.SUCCESS)
            else:
                failed_runs = len(execution_summary.get("failed_runs", []))
                if failed_runs > 0:
                    console.print(f"💥 [bold red]Workflow completed but {failed_runs} model executions failed[/bold red]")
                    raise typer.Exit(ExitCode.RUN_FAILURE)
                else:
                    console.print("💥 [bold red]Workflow failed for unknown reasons[/bold red]")
                    raise typer.Exit(ExitCode.FAILURE)
                    
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"💥 [bold red]Run process failed: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(ExitCode.FAILURE)


@generate_app.command("ansible")
def generate_ansible(
    manifest_file: Annotated[str, typer.Option("--manifest-file", "-m", help="Build manifest file")] = DEFAULT_MANIFEST_FILE,
    output: Annotated[str, typer.Option("--output", "-o", help="Output Ansible playbook file")] = DEFAULT_ANSIBLE_OUTPUT,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
) -> None:
    """
    📋 Generate Ansible playbook for distributed execution.
    
    Uses the enhanced build manifest as the primary configuration source.
    """
    setup_logging(verbose)
    
    console.print(Panel(
        f"📋 [bold cyan]Generating Ansible Playbook[/bold cyan]\n"
        f"Manifest: [yellow]{manifest_file}[/yellow]\n"
        f"Output: [yellow]{output}[/yellow]",
        title="Ansible Generation",
        border_style="blue"
    ))
    
    try:
        # Validate input files
        if not os.path.exists(manifest_file):
            console.print(f"❌ [bold red]Manifest file not found: {manifest_file}[/bold red]")
            raise typer.Exit(ExitCode.FAILURE)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating Ansible playbook...", total=None)
            
            create_ansible_playbook(
                manifest_file=manifest_file,
                playbook_file=output
            )
            
            progress.update(task, description="Ansible playbook generated!")
        
        console.print(f"✅ [bold green]Ansible playbook generated successfully: [cyan]{output}[/cyan][/bold green]")
        
    except Exception as e:
        console.print(f"💥 [bold red]Failed to generate Ansible playbook: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(ExitCode.FAILURE)


@generate_app.command("k8s")
def generate_k8s(
    manifest_file: Annotated[str, typer.Option("--manifest-file", "-m", help="Build manifest file")] = DEFAULT_MANIFEST_FILE,
    namespace: Annotated[str, typer.Option("--namespace", "-n", help="Kubernetes namespace")] = DEFAULT_K8S_NAMESPACE,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
) -> None:
    """
    ☸️  Generate Kubernetes manifests for distributed execution.
    
    Uses the enhanced build manifest as the primary configuration source.
    """
    setup_logging(verbose)
    
    console.print(Panel(
        f"☸️  [bold cyan]Generating Kubernetes Manifests[/bold cyan]\n"
        f"Manifest: [yellow]{manifest_file}[/yellow]\n"
        f"Namespace: [yellow]{namespace}[/yellow]",
        title="Kubernetes Generation",
        border_style="blue"
    ))
    
    try:
        # Validate input files
        if not os.path.exists(manifest_file):
            console.print(f"❌ [bold red]Manifest file not found: {manifest_file}[/bold red]")
            raise typer.Exit(ExitCode.FAILURE)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating Kubernetes manifests...", total=None)
            
            create_kubernetes_manifests(
                manifest_file=manifest_file,
                namespace=namespace
            )
            
            progress.update(task, description="Kubernetes manifests generated!")
        
        console.print(f"✅ [bold green]Kubernetes manifests generated successfully[/bold green]")
        
    except Exception as e:
        console.print(f"💥 [bold red]Failed to generate Kubernetes manifests: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(ExitCode.FAILURE)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", help="Show version and exit")] = False,
) -> None:
    """
    🚀 madengine Distributed Orchestrator
    
    Modern CLI for building and running AI models in distributed scenarios.
    Built with Typer and Rich for a beautiful, production-ready experience.
    """
    if version:
        # You might want to get the actual version from your package
        console.print("🚀 [bold cyan]madengine-cli[/bold cyan] version [green]1.0.0[/green]")
        raise typer.Exit()
    
    # If no command is provided, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        ctx.exit()


def cli_main() -> None:
    """Entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n🛑 [yellow]Operation cancelled by user[/yellow]")
        sys.exit(ExitCode.FAILURE)
    except Exception as e:
        console.print(f"💥 [bold red]Unexpected error: {e}[/bold red]")
        console.print_exception()
        sys.exit(ExitCode.FAILURE)


if __name__ == "__main__":
    cli_main()
