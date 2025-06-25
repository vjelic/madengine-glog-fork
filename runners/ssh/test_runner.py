#!/usr/bin/env python3
"""Test script for SSH Multi-Node Runner

This script provides basic unit tests and validation for the SSH runner.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from run import SSHMultiNodeRunner, load_config_file, merge_config_and_args, parse_args
except ImportError:
    print("Error: Could not import run module. Make sure run.py is in the same directory.")
    sys.exit(1)


class TestSSHMultiNodeRunner(unittest.TestCase):
    """Test cases for SSH Multi-Node Runner."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_args = MagicMock()
        self.mock_args.model = 'pyt_megatron_lm_train_llama2_7b'
        self.mock_args.nodes = '10.0.0.1,10.0.0.2'
        self.mock_args.master_addr = '10.0.0.1'
        self.mock_args.master_port = 4000
        self.mock_args.ssh_user = 'testuser'
        self.mock_args.ssh_password = 'testpass'
        self.mock_args.ssh_key = None
        self.mock_args.shared_data_path = '/nfs/data'
        self.mock_args.nccl_interface = 'eth0'
        self.mock_args.gloo_interface = 'eth0'
        self.mock_args.timeout = 3600
        self.mock_args.madengine_path = 'madengine'
        self.mock_args.additional_args = ''
    
    def test_initialization(self):
        """Test runner initialization."""
        runner = SSHMultiNodeRunner(self.mock_args)
        
        self.assertEqual(runner.nodes, ['10.0.0.1', '10.0.0.2'])
        self.assertEqual(runner.master_addr, '10.0.0.1')
        self.assertEqual(runner.master_port, '4000')
        self.assertEqual(runner.ssh_user, 'testuser')
        self.assertEqual(runner.model_tag, 'pyt_megatron_lm_train_llama2_7b')
    
    def test_command_generation(self):
        """Test madengine command generation."""
        runner = SSHMultiNodeRunner(self.mock_args)
        
        # Test command for node rank 0
        cmd_0 = runner._build_madengine_command(0)
        self.assertIn('madengine run', cmd_0)
        self.assertIn('pyt_megatron_lm_train_llama2_7b', cmd_0)
        self.assertIn('"NODE_RANK": "0"', cmd_0)
        self.assertIn('"NNODES": "2"', cmd_0)
        self.assertIn('--force-mirror-local /nfs/data', cmd_0)
        
        # Test command for node rank 1
        cmd_1 = runner._build_madengine_command(1)
        self.assertIn('"NODE_RANK": "1"', cmd_1)
    
    def test_validation_errors(self):
        """Test configuration validation errors."""
        # Test missing nodes
        args_copy = MagicMock()
        for attr in ['model', 'nodes', 'master_addr', 'master_port', 'ssh_user', 'ssh_password', 'ssh_key']:
            setattr(args_copy, attr, getattr(self.mock_args, attr))
        args_copy.nodes = ''
        with self.assertRaises(ValueError):
            SSHMultiNodeRunner(args_copy)
        
        # Test missing SSH user
        args_copy = MagicMock()
        for attr in ['model', 'nodes', 'master_addr', 'master_port', 'ssh_user', 'ssh_password', 'ssh_key']:
            setattr(args_copy, attr, getattr(self.mock_args, attr))
        args_copy.ssh_user = ''
        with self.assertRaises(ValueError):
            SSHMultiNodeRunner(args_copy)
        
        # Test missing authentication
        args_copy = MagicMock()
        for attr in ['model', 'nodes', 'master_addr', 'master_port', 'ssh_user', 'ssh_password', 'ssh_key']:
            setattr(args_copy, attr, getattr(self.mock_args, attr))
        delattr(args_copy, 'ssh_password')
        delattr(args_copy, 'ssh_key')
        with self.assertRaises(ValueError):
            SSHMultiNodeRunner(args_copy)
    
    def test_config_file_loading(self):
        """Test configuration file loading."""
        # Create a temporary config file
        config_content = """
[cluster]
nodes = node1,node2,node3
master_addr = node1
master_port = 5000

[ssh]
user = testuser
key_file = /path/to/key

[training]
model = test_model
shared_data_path = /shared/data
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            config_dict = load_config_file(temp_config_path)
            
            self.assertEqual(config_dict['cluster_nodes'], 'node1,node2,node3')
            self.assertEqual(config_dict['cluster_master_addr'], 'node1')
            self.assertEqual(config_dict['cluster_master_port'], '5000')
            self.assertEqual(config_dict['ssh_user'], 'testuser')
            self.assertEqual(config_dict['ssh_key_file'], '/path/to/key')
            self.assertEqual(config_dict['training_model'], 'test_model')
            
        finally:
            os.unlink(temp_config_path)
    
    def test_config_file_not_found(self):
        """Test error handling for missing config file."""
        with self.assertRaises(FileNotFoundError):
            load_config_file('/nonexistent/config.ini')


class MockSSHIntegrationTest(unittest.TestCase):
    """Integration tests with mocked SSH connections."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_args = MagicMock()
        self.mock_args.model = 'pyt_megatron_lm_train_llama2_7b'
        self.mock_args.nodes = '10.0.0.1,10.0.0.2'
        self.mock_args.master_addr = '10.0.0.1'
        self.mock_args.master_port = 4000
        self.mock_args.ssh_user = 'testuser'
        self.mock_args.ssh_password = 'testpass'
        self.mock_args.ssh_key = None
        self.mock_args.shared_data_path = '/nfs/data'
        self.mock_args.nccl_interface = 'eth0'
        self.mock_args.gloo_interface = 'eth0'
        self.mock_args.timeout = 3600
        self.mock_args.madengine_path = 'madengine'
        self.mock_args.additional_args = ''
    
    @patch('run.paramiko.SSHClient')
    def test_connectivity_check(self, mock_ssh_client_class):
        """Test node connectivity checking."""
        # Mock SSH client
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        
        # Mock successful connection and command execution
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'connectivity_test'
        mock_ssh_client.exec_command.return_value = (None, mock_stdout, None)
        
        runner = SSHMultiNodeRunner(self.mock_args)
        reachable_nodes = runner._check_node_connectivity()
        
        self.assertEqual(len(reachable_nodes), 2)
        self.assertIn('10.0.0.1', reachable_nodes)
        self.assertIn('10.0.0.2', reachable_nodes)
    
    @patch('run.paramiko.SSHClient')
    def test_command_execution(self, mock_ssh_client_class):
        """Test command execution on nodes."""
        # Mock SSH client
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        
        # Mock successful command execution
        mock_stdout = MagicMock()
        mock_stdout.__iter__ = lambda self: iter(['Training started...', 'Training completed!'])
        mock_stdout.channel.recv_exit_status.return_value = 0
        
        mock_stderr = MagicMock()
        mock_stderr.__iter__ = lambda self: iter([])
        
        mock_ssh_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        
        runner = SSHMultiNodeRunner(self.mock_args)
        hostname, success, output = runner._execute_on_node('10.0.0.1', 0)
        
        self.assertEqual(hostname, '10.0.0.1')
        self.assertTrue(success)
        self.assertIn('Training started...', output)
    
    @patch('run.paramiko.SSHClient')
    def test_prerequisites_validation_success(self, mock_ssh_client_class):
        """Test successful prerequisites validation."""
        # Mock SSH client
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        
        # Mock successful prerequisites checks
        def mock_exec_command(command):
            mock_stdout = MagicMock()
            mock_stderr = MagicMock()
            if 'test -d DeepLearningModels' in command:
                mock_stdout.read.return_value = b'exists'
            elif 'which madengine' in command:
                mock_stdout.read.return_value = b'found'
            elif 'cd DeepLearningModels' in command:
                mock_stdout.read.return_value = b'/home/user/DeepLearningModels'
                mock_stderr.read.return_value = b''
            return (None, mock_stdout, mock_stderr)
        
        mock_ssh_client.exec_command.side_effect = mock_exec_command
        
        runner = SSHMultiNodeRunner(self.mock_args)
        success, error_msg = runner._validate_remote_node_prerequisites('10.0.0.1')
        
        self.assertTrue(success)
        self.assertEqual(error_msg, "")
    
    @patch('run.paramiko.SSHClient')
    def test_prerequisites_validation_missing_deeplearning_models(self, mock_ssh_client_class):
        """Test prerequisites validation with missing DeepLearningModels folder."""
        # Mock SSH client
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        
        # Mock missing DeepLearningModels folder
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'missing'
        mock_ssh_client.exec_command.return_value = (None, mock_stdout, None)
        
        runner = SSHMultiNodeRunner(self.mock_args)
        success, error_msg = runner._validate_remote_node_prerequisites('10.0.0.1')
        
        self.assertFalse(success)
        self.assertIn('DeepLearningModels folder not found', error_msg)
    
    @patch('run.paramiko.SSHClient')
    def test_prerequisites_validation_missing_madengine(self, mock_ssh_client_class):
        """Test prerequisites validation with missing madengine."""
        # Mock SSH client
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        
        # Mock DeepLearningModels exists but madengine missing
        def mock_exec_command(command):
            mock_stdout = MagicMock()
            mock_stderr = MagicMock()
            if 'test -d DeepLearningModels' in command:
                mock_stdout.read.return_value = b'exists'
            elif 'which madengine' in command or 'madengine --help' in command:
                mock_stdout.read.return_value = b'missing'
            return (None, mock_stdout, mock_stderr)
        
        mock_ssh_client.exec_command.side_effect = mock_exec_command
        
        runner = SSHMultiNodeRunner(self.mock_args)
        success, error_msg = runner._validate_remote_node_prerequisites('10.0.0.1')
        
        self.assertFalse(success)
        self.assertIn('madengine not found', error_msg)


def run_tests():
    """Run all tests."""
    print("🧪 Running SSH Multi-Node Runner Tests...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSSHMultiNodeRunner))
    suite.addTests(loader.loadTestsFromTestCase(MockSSHIntegrationTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


def validate_environment():
    """Validate that the environment is set up correctly."""
    print("🔍 Validating environment...")
    
    issues = []
    
    # Check if paramiko is available
    try:
        import paramiko
        print("✅ paramiko is available")
    except ImportError:
        issues.append("❌ paramiko is not installed. Run: pip install paramiko")
    
    # Check if run.py exists
    run_py_path = os.path.join(os.path.dirname(__file__), 'run.py')
    if os.path.exists(run_py_path):
        print("✅ run.py found")
    else:
        issues.append("❌ run.py not found in current directory")
    
    # Check if requirements.txt exists
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        print("✅ requirements.txt found")
    else:
        issues.append("❌ requirements.txt not found")
    
    if issues:
        print("\n🚨 Issues found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ Environment validation passed!")
        return True


if __name__ == "__main__":
    print("SSH Multi-Node Runner Test Suite")
    print("=" * 40)
    
    # Validate environment first
    if not validate_environment():
        print("\n💥 Environment validation failed. Please fix the issues above.")
        sys.exit(1)
    
    # Run tests
    if run_tests():
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)
