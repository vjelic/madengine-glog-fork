#!/usr/bin/env python3
"""SSH Multi-Node Runner for MAD Engine

This script orchestrates distributed training across multiple nodes using SSH.
It automatically configures and executes madengine commands on remote nodes
for PyTorch Megatron-LM training workloads.

Example Usage:
    python run.py --model pyt_megatron_lm_train_llama2_7b \
                   --nodes 192.168.1.1,192.168.1.2 \
                   --master-addr 192.168.0.1 \
                   --master-port 4000 \
                   --ssh-user username \
                   --ssh-key /path/to/ssh/key \
                   --shared-data-path /nfs/data

Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""

import argparse
import json
import os
import sys
import time
import threading
import socket
import configparser
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Third-party imports
try:
    import paramiko
except ImportError:
    print("Error: paramiko is required but not installed.")
    print("Please install it with: pip install paramiko")
    sys.exit(1)

# Add madengine to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from madengine.utils.ssh_to_db import print_ssh_out


class SSHMultiNodeRunner:
    """SSH-based multi-node runner for distributed training."""
    
    def __init__(self, args: argparse.Namespace):
        """Initialize the SSH multi-node runner.
        
        Args:
            args: Command line arguments containing configuration
        """
        self.args = args
        self.nodes = [node.strip() for node in args.nodes.split(',')]
        self.master_addr = args.master_addr or self.nodes[0]
        self.master_port = str(args.master_port)
        self.ssh_user = args.ssh_user
        self.ssh_password = getattr(args, 'ssh_password', None)
        self.ssh_key = getattr(args, 'ssh_key', None)
        self.model_tag = args.model
        self.shared_data_path = getattr(args, 'shared_data_path', '/nfs/data')
        self.nccl_interface = getattr(args, 'nccl_interface', 'ens14np0')
        self.gloo_interface = getattr(args, 'gloo_interface', 'ens14np0')
        self.timeout = getattr(args, 'timeout', 3600)  # 1 hour default
        self.madengine_path = getattr(args, 'madengine_path', 'madengine')
        self.additional_args = getattr(args, 'additional_args', '')
        
        # Validate configuration
        self._validate_config()
        
    def _validate_config(self) -> None:
        """Validate the configuration parameters."""
        if not self.nodes:
            raise ValueError("At least one node must be specified")
            
        if not self.ssh_user:
            raise ValueError("SSH username must be specified")
            
        if not self.ssh_password and not self.ssh_key:
            raise ValueError("Either SSH password or SSH key must be specified")
            
        if not self.model_tag:
            raise ValueError("Model tag must be specified")
            
        # Validate SSH key file exists if specified
        if self.ssh_key and not os.path.exists(self.ssh_key):
            raise FileNotFoundError(f"SSH key file not found: {self.ssh_key}")
    
    def _create_ssh_client(self) -> paramiko.SSHClient:
        """Create and configure SSH client.
        
        Returns:
            Configured SSH client
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.load_system_host_keys()
        return ssh_client
    
    def _connect_ssh(self, hostname: str) -> paramiko.SSHClient:
        """Connect to a remote host via SSH.
        
        Args:
            hostname: The hostname or IP to connect to
            
        Returns:
            Connected SSH client
            
        Raises:
            Exception: If connection fails
        """
        ssh_client = self._create_ssh_client()
        
        try:
            if self.ssh_key:
                ssh_client.connect(
                    hostname=hostname,
                    username=self.ssh_user,
                    key_filename=self.ssh_key,
                    timeout=30
                )
            else:
                ssh_client.connect(
                    hostname=hostname,
                    username=self.ssh_user,
                    password=self.ssh_password,
                    timeout=30
                )
            
            print(f"✓ Successfully connected to {hostname}")
            return ssh_client
            
        except paramiko.ssh_exception.AuthenticationException as e:
            raise Exception(f"Authentication failed for {hostname}: {e}")
        except paramiko.ssh_exception.SSHException as e:
            raise Exception(f"SSH error for {hostname}: {e}")
        except socket.error as e:
            raise Exception(f"Socket error for {hostname}: {e}")
    
    def _build_madengine_command(self, node_rank: int) -> str:
        """Build the madengine command for a specific node.
        
        Args:
            node_rank: The rank of this node (0-based)
            
        Returns:
            Complete madengine command string
        """
        multi_node_args = {
            'RUNNER': 'torchrun',
            'MASTER_ADDR': self.master_addr,
            'MASTER_PORT': self.master_port,
            'NNODES': str(len(self.nodes)),
            'NODE_RANK': str(node_rank),
            'NCCL_SOCKET_IFNAME': self.nccl_interface,
            'GLOO_SOCKET_IFNAME': self.gloo_interface
        }
        
        # Build the additional context string
        additional_context = f"'{{'multi_node_args': {json.dumps(multi_node_args)}}}'"
        
        # Build the complete command
        cmd_parts = [
            self.madengine_path,
            'run',
            '--tags', self.model_tag,
            '--additional-context', additional_context
        ]
        
        # Add shared data path if specified
        if self.shared_data_path:
            cmd_parts.extend(['--force-mirror-local', self.shared_data_path])
        
        # Add any additional arguments
        if self.additional_args:
            cmd_parts.append(self.additional_args)
        
        return ' '.join(cmd_parts)
    
    def _execute_on_node(self, hostname: str, node_rank: int) -> Tuple[str, bool, str]:
        """Execute madengine command on a single node.
        
        Args:
            hostname: The hostname/IP of the node
            node_rank: The rank of this node
            
        Returns:
            Tuple of (hostname, success, output/error)
        """
        try:
            ssh_client = self._connect_ssh(hostname)
            
            # Build and execute the madengine command
            command = self._build_madengine_command(node_rank)
            
            # Change to DeepLearningModels directory and execute the command
            full_command = f"cd DeepLearningModels && {command}"
            print(f"🚀 Executing on {hostname} (rank {node_rank}): {full_command}")
            
            # Execute the command
            stdin, stdout, stderr = ssh_client.exec_command(
                full_command, 
                timeout=self.timeout
            )
            
            # Read output in real-time
            output_lines = []
            error_lines = []
            
            # Read stdout
            for line in stdout:
                line = line.strip()
                if line:
                    print(f"[{hostname}:{node_rank}] {line}")
                    output_lines.append(line)
            
            # Read stderr
            for line in stderr:
                line = line.strip()
                if line:
                    print(f"[{hostname}:{node_rank}] ERROR: {line}")
                    error_lines.append(line)
            
            # Get exit code
            exit_code = stdout.channel.recv_exit_status()
            
            ssh_client.close()
            
            if exit_code == 0:
                return hostname, True, '\n'.join(output_lines)
            else:
                error_output = '\n'.join(error_lines) if error_lines else "Command failed with no error output"
                return hostname, False, f"Exit code {exit_code}: {error_output}"
                
        except Exception as e:
            return hostname, False, str(e)
    
    def _check_node_connectivity(self) -> List[str]:
        """Check connectivity to all nodes.
        
        Returns:
            List of nodes that are reachable
        """
        reachable_nodes = []
        
        print("🔍 Checking connectivity to all nodes...")
        
        for hostname in self.nodes:
            try:
                ssh_client = self._connect_ssh(hostname)
                
                # Test basic command execution
                stdin, stdout, stderr = ssh_client.exec_command('echo "connectivity_test"')
                output = stdout.read().decode().strip()
                
                if output == "connectivity_test":
                    reachable_nodes.append(hostname)
                    print(f"✓ {hostname} is reachable")
                else:
                    print(f"✗ {hostname} failed connectivity test")
                
                ssh_client.close()
                
            except Exception as e:
                print(f"✗ {hostname} is not reachable: {e}")
        
        return reachable_nodes
    
    def _wait_for_master_ready(self, master_host: str) -> bool:
        """Wait for master node to be ready to accept connections.
        
        Args:
            master_host: The master node hostname/IP
            
        Returns:
            True if master is ready, False if timeout
        """
        print(f"⏳ Waiting for master node {master_host}:{self.master_port} to be ready...")
        
        max_wait_time = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((master_host, int(self.master_port)))
                sock.close()
                
                if result == 0:
                    print(f"✓ Master node is ready")
                    return True
                    
            except Exception:
                pass
            
            time.sleep(2)
        
        print(f"✗ Master node did not become ready within {max_wait_time} seconds")
        return False
    
    def _validate_remote_node_prerequisites(self, hostname: str) -> Tuple[bool, str]:
        """Validate that remote node has required prerequisites.
        
        Args:
            hostname: The hostname/IP of the node to validate
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            ssh_client = self._connect_ssh(hostname)
            
            # Check if DeepLearningModels folder exists
            print(f"🔍 Checking DeepLearningModels folder on {hostname}...")
            stdin, stdout, stderr = ssh_client.exec_command('test -d DeepLearningModels && echo "exists" || echo "missing"')
            dl_models_result = stdout.read().decode().strip()
            
            if dl_models_result != "exists":
                ssh_client.close()
                return False, f"DeepLearningModels folder not found on {hostname}. Please set up the remote node with DeepLearningModels directory."
            
            print(f"✓ DeepLearningModels folder found on {hostname}")
            
            # Check if madengine is installed and accessible
            print(f"🔍 Checking madengine installation on {hostname}...")
            stdin, stdout, stderr = ssh_client.exec_command(f'which {self.madengine_path} > /dev/null 2>&1 && echo "found" || echo "missing"')
            madengine_result = stdout.read().decode().strip()
            
            if madengine_result != "found":
                # Try alternative check - see if madengine can be executed
                stdin, stdout, stderr = ssh_client.exec_command(f'{self.madengine_path} --help > /dev/null 2>&1 && echo "found" || echo "missing"')
                madengine_alt_result = stdout.read().decode().strip()
                
                if madengine_alt_result != "found":
                    ssh_client.close()
                    return False, f"madengine not found or not accessible on {hostname}. Please install madengine on the remote node or ensure it's in the PATH."
            
            print(f"✓ madengine installation found on {hostname}")
            
            # Check if we can access the DeepLearningModels directory
            print(f"🔍 Checking access to DeepLearningModels directory on {hostname}...")
            stdin, stdout, stderr = ssh_client.exec_command('cd DeepLearningModels && pwd')
            cd_result = stdout.read().decode().strip()
            cd_error = stderr.read().decode().strip()
            
            if cd_error or not cd_result.endswith('DeepLearningModels'):
                ssh_client.close()
                return False, f"Cannot access DeepLearningModels directory on {hostname}. Error: {cd_error or 'Unknown error'}"
            
            print(f"✓ DeepLearningModels directory is accessible on {hostname}")
            
            # Check if shared data path exists (if specified and not the default)
            if self.shared_data_path and self.shared_data_path != '/nfs/data':
                print(f"🔍 Checking shared data path on {hostname}...")
                stdin, stdout, stderr = ssh_client.exec_command(f'test -d "{self.shared_data_path}" && echo "exists" || echo "missing"')
                shared_data_result = stdout.read().decode().strip()
                
                if shared_data_result != "exists":
                    ssh_client.close()
                    return False, f"Shared data path '{self.shared_data_path}' not found on {hostname}. Please ensure the shared filesystem is mounted."
                
                print(f"✓ Shared data path '{self.shared_data_path}' found on {hostname}")
            
            print(f"✓ All checks passed for {hostname}")
            
            ssh_client.close()
            return True, ""
            
        except Exception as e:
            return False, f"Error validating prerequisites on {hostname}: {str(e)}"

    def _check_all_prerequisites(self) -> bool:
        """Check prerequisites on all nodes.
        
        Returns:
            True if all nodes meet prerequisites, False otherwise
        """
        print("🔧 Validating prerequisites on all nodes...")
        
        failed_nodes = []
        
        for hostname in self.nodes:
            success, error_msg = self._validate_remote_node_prerequisites(hostname)
            if not success:
                print(f"❌ {hostname}: {error_msg}")
                failed_nodes.append((hostname, error_msg))
            else:
                print(f"✅ {hostname}: All prerequisites met")
        
        if failed_nodes:
            print(f"\n💥 Prerequisites check failed for {len(failed_nodes)} node(s):")
            for hostname, error_msg in failed_nodes:
                print(f"   • {hostname}: {error_msg}")
            
            self._print_setup_instructions()
            return False
        
        print("✅ All nodes meet the prerequisites")
        return True
    
    def _print_setup_instructions(self) -> None:
        """Print setup instructions for remote nodes."""
        print("\n" + "="*60)
        print("🔧 REMOTE NODE SETUP INSTRUCTIONS")
        print("="*60)
        print("\nTo prepare your remote nodes for multi-node training:")
        print("\n1. DeepLearningModels Directory:")
        print("   • Create or ensure the DeepLearningModels directory exists in the user's home directory")
        print("   • Command: mkdir -p ~/DeepLearningModels")
        print("   • This directory should contain your model configurations and training scripts")
        
        print("\n2. MAD Engine Installation:")
        print("   • Install madengine on each remote node")
        print("   • Command: pip install madengine")
        print("   • Or ensure madengine is in the PATH and executable")
        print("   • Verify with: madengine --help")
        
        if self.shared_data_path and self.shared_data_path != '/nfs/data':
            print(f"\n3. Shared Data Path:")
            print(f"   • Ensure the shared data path '{self.shared_data_path}' exists and is accessible")
            print(f"   • This should be a shared filesystem (NFS, GPFS, etc.) mounted on all nodes")
            print(f"   • All nodes should have read/write access to this path")
        
        print("\n4. SSH Access:")
        print("   • Ensure SSH key-based or password authentication is configured")
        print("   • Test SSH access manually before running this script")
        
        print("\n5. Network Configuration:")
        print(f"   • Ensure nodes can communicate on the specified interfaces:")
        print(f"   • NCCL interface: {self.nccl_interface}")
        print(f"   • GLOO interface: {self.gloo_interface}")
        print(f"   • Master node {self.master_addr} should be accessible on port {self.master_port}")
        
        print("\n" + "="*60)
    
    def run(self) -> bool:
        """Run distributed training across all nodes.
        
        Returns:
            True if all nodes completed successfully, False otherwise
        """
        print(f"🌐 Starting multi-node training on {len(self.nodes)} nodes")
        print(f"📋 Model: {self.model_tag}")
        print(f"🏠 Master: {self.master_addr}:{self.master_port}")
        print(f"📁 Shared data: {self.shared_data_path}")
        print(f"🔗 Nodes: {', '.join(self.nodes)}")
        
        # Check connectivity to all nodes
        reachable_nodes = self._check_node_connectivity()
        
        if len(reachable_nodes) != len(self.nodes):
            unreachable = set(self.nodes) - set(reachable_nodes)
            print(f"❌ Some nodes are unreachable: {', '.join(unreachable)}")
            return False
        
        print("✅ All nodes are reachable")
        
        # Validate prerequisites on all nodes
        if not self._check_all_prerequisites():
            return False
            return False
        
        # Execute on all nodes concurrently
        results = []
        
        with ThreadPoolExecutor(max_workers=len(self.nodes)) as executor:
            # Submit jobs for all nodes
            futures = []
            for i, hostname in enumerate(self.nodes):
                future = executor.submit(self._execute_on_node, hostname, i)
                futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(futures):
                hostname, success, output = future.result()
                results.append((hostname, success, output))
                
                if success:
                    print(f"✅ {hostname} completed successfully")
                else:
                    print(f"❌ {hostname} failed: {output}")
        
        # Check overall success
        successful_nodes = [r[0] for r in results if r[1]]
        failed_nodes = [r[0] for r in results if not r[1]]
        
        print(f"\n📊 Training Results:")
        print(f"✅ Successful nodes: {len(successful_nodes)}/{len(self.nodes)}")
        
        if failed_nodes:
            print(f"❌ Failed nodes: {', '.join(failed_nodes)}")
            return False
        
        print("🎉 Multi-node training completed successfully!")
        return True


def load_config_file(config_path: str) -> Dict:
    """Load configuration from INI file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary with configuration values
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Convert to dictionary with flattened keys
    config_dict = {}
    for section in config.sections():
        for key, value in config[section].items():
            config_dict[f"{section}_{key}"] = value
    
    return config_dict


def merge_config_and_args(config_dict: Dict, args: argparse.Namespace) -> argparse.Namespace:
    """Merge configuration file values with command line arguments.
    Command line arguments take precedence over config file values.
    
    Args:
        config_dict: Configuration dictionary from file
        args: Command line arguments
        
    Returns:
        Updated arguments with config file values applied
    """
    # Mapping of config keys to argument attributes
    config_to_arg_map = {
        'cluster_nodes': 'nodes',
        'cluster_master_addr': 'master_addr', 
        'cluster_master_port': 'master_port',
        'ssh_user': 'ssh_user',
        'ssh_key_file': 'ssh_key',
        'ssh_password': 'ssh_password',
        'training_model': 'model',
        'training_shared_data_path': 'shared_data_path',
        'training_nccl_interface': 'nccl_interface',
        'training_gloo_interface': 'gloo_interface',
        'training_timeout': 'timeout',
        'madengine_madengine_path': 'madengine_path',
        'madengine_additional_args': 'additional_args'
    }
    
    # Apply config values only if argument was not provided
    for config_key, arg_attr in config_to_arg_map.items():
        if config_key in config_dict and not getattr(args, arg_attr, None):
            value = config_dict[config_key]
            # Convert numeric values
            if arg_attr in ['master_port', 'timeout']:
                value = int(value)
            setattr(args, arg_attr, value)
    
    return args


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="SSH Multi-Node Runner for MAD Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with SSH key authentication
  python run.py --model pyt_megatron_lm_train_llama2_7b \\
                 --nodes 192.168.1.1,192.168.1.2 \\
                 --master-addr 192.168.0.1 \\
                 --ssh-user ubuntu \\
                 --ssh-key ~/.ssh/id_rsa
  
  # Run with password authentication
  python run.py --model pyt_megatron_lm_train_llama2_7b \\
                 --nodes node1,node2,node3 \\
                 --ssh-user root \\
                 --ssh-password mypassword \\
                 --shared-data-path /shared/data
                 
  # Run with configuration file
  python run.py --config config.ini
        """
    )
    
    # Configuration file option
    parser.add_argument(
        '--config',
        help='Path to configuration file (INI format)'
    )
    
    # Required arguments (unless provided in config)
    parser.add_argument(
        '--model', 
        help='Model tag to run (e.g., pyt_megatron_lm_train_llama2_7b)'
    )
    
    parser.add_argument(
        '--nodes',
        help='Comma-separated list of node hostnames/IPs'
    )
    
    parser.add_argument(
        '--ssh-user',
        help='SSH username for all nodes'
    )
    
    # SSH authentication (one required unless in config)
    parser.add_argument(
        '--ssh-password',
        help='SSH password for all nodes'
    )
    parser.add_argument(
        '--ssh-key',
        help='Path to SSH private key file'
    )
    
    # Optional arguments
    parser.add_argument(
        '--master-addr',
        help='Master node address (defaults to first node)'
    )
    
    parser.add_argument(
        '--master-port',
        type=int,
        default=4000,
        help='Master node port (default: 4000)'
    )
    
    parser.add_argument(
        '--shared-data-path',
        default='/nfs/data',
        help='Path to shared data filesystem (default: /nfs/data)'
    )
    
    parser.add_argument(
        '--nccl-interface',
        default='ens14np0',
        help='NCCL socket interface (default: ens14np0)'
    )
    
    parser.add_argument(
        '--gloo-interface', 
        default='ens14np0',
        help='GLOO socket interface (default: ens14np0)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=3600,
        help='Execution timeout in seconds (default: 3600)'
    )
    
    parser.add_argument(
        '--madengine-path',
        default='madengine',
        help='Path to madengine executable (default: madengine)'
    )
    
    parser.add_argument(
        '--additional-args',
        help='Additional arguments to pass to madengine'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Load configuration file if provided
    if args.config:
        config_dict = load_config_file(args.config)
        args = merge_config_and_args(config_dict, args)
    
    # Validate required arguments after config loading
    if not args.model:
        parser.error("--model is required (can be provided via config file)")
    if not args.nodes:
        parser.error("--nodes is required (can be provided via config file)")
    if not args.ssh_user:
        parser.error("--ssh-user is required (can be provided via config file)")
    if not args.ssh_password and not args.ssh_key:
        parser.error("Either --ssh-password or --ssh-key is required (can be provided via config file)")
    
    return args


def main():
    """Main entry point."""
    try:
        args = parse_args()
        runner = SSHMultiNodeRunner(args)
        success = runner.run()
        
        if success:
            print("🎯 All nodes completed successfully!")
            sys.exit(0)
        else:
            print("💥 Some nodes failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
