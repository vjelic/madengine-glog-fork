#!/usr/bin/env python3
"""
Setup script for madengine

This setup.py provides compatibility with environments that require traditional 
setup.py installations while reading configuration from pyproject.toml.

USAGE RECOMMENDATIONS:

Modern installations (PREFERRED):
    pip install .
    python -m build
    pip install -e .[dev]

Legacy installations (for compatibility):
    python setup.py install
    python setup.py develop
    python setup.py sdist
    python setup.py bdist_wheel

This setup.py reads configuration from pyproject.toml and provides the same
functionality using the traditional setuptools approach. The warnings you see
about overwritten values are expected since both methods define the same
configuration.

ENVIRONMENT COMPATIBILITY:
- CI/CD systems that don't support pyproject.toml
- Older Python environments
- Systems requiring setup.py for packaging
- Development environments with older setuptools
"""

import sys
from pathlib import Path

try:
    from setuptools import setup, find_packages
except ImportError:
    print("setuptools is required for setup.py")
    print("Install it using: pip install setuptools")
    sys.exit(1)

def read_readme():
    """Read README.md file for long description."""
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def get_config_from_pyproject():
    """Read configuration from pyproject.toml."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            try:
                import toml as tomllib_alt
                def load(f):
                    return tomllib_alt.load(f)
                tomllib.load = load
            except ImportError:
                print("Warning: No TOML library found. Using fallback configuration.")
                return get_fallback_config()
    
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    if not pyproject_path.exists():
        return get_fallback_config()
    
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        
        project = data.get("project", {})
        
        # Extract configuration
        config = {
            "name": project.get("name", "madengine"),
            "description": project.get("description", "MAD Engine"),
            "authors": project.get("authors", []),
            "dependencies": project.get("dependencies", []),
            "optional_dependencies": project.get("optional-dependencies", {}),
            "requires_python": project.get("requires-python", ">=3.8"),
            "classifiers": project.get("classifiers", []),
            "urls": project.get("urls", {}),
            "scripts": project.get("scripts", {}),
        }
        
        return config
        
    except Exception as e:
        print(f"Warning: Could not read pyproject.toml: {e}")
        return get_fallback_config()

def get_fallback_config():
    """Fallback configuration if pyproject.toml cannot be read."""
    return {
        "name": "madengine",
        "description": "MAD Engine is a set of interfaces to run various AI models from public MAD.",
        "authors": [{"name": "Advanced Micro Devices", "email": "mad.support@amd.com"}],
        "dependencies": [
            "pandas", "GitPython", "jsondiff", "sqlalchemy", "setuptools-rust",
            "paramiko", "mysql-connector-python", "pymysql", "tqdm", "pytest",
            "typing-extensions", "pymongo", "toml",
        ],
        "optional_dependencies": {
            "dev": [
                "pytest", "pytest-cov", "pytest-xdist", "pytest-timeout",
                "pytest-mock", "pytest-asyncio",
            ]
        },
        "requires_python": ">=3.8",
        "classifiers": [
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        "urls": {
            "Homepage": "https://github.com/ROCm/madengine",
            "Issues": "https://github.com/ROCm/madengine/issues",
        },
        "scripts": {
            "madengine": "madengine.mad:main"
        },
    }

def get_version():
    """Get version from git tags or fallback to a default."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
            return f"1.0.0.dev0+g{commit}"
    except:
        pass
    return "1.0.0.dev0"

def main():
    """Main setup function."""
    config = get_config_from_pyproject()
    
    # Extract author information
    authors = config.get("authors", [])
    if authors:
        author_name = authors[0].get("name", "Advanced Micro Devices")
        author_email = authors[0].get("email", "mad.support@amd.com")
    else:
        author_name = "Advanced Micro Devices"
        author_email = "mad.support@amd.com"
    
    # Extract scripts/entry points
    scripts = config.get("scripts", {})
    entry_points = {"console_scripts": []}
    for script_name, module_path in scripts.items():
        entry_points["console_scripts"].append(f"{script_name}={module_path}")
    
    # Setup configuration
    setup_kwargs = {
        "name": config["name"],
        "version": get_version(),
        "author": author_name,
        "author_email": author_email,
        "description": config["description"],
        "long_description": read_readme(),
        "long_description_content_type": "text/markdown",
        "url": config["urls"].get("Homepage", "https://github.com/ROCm/madengine"),
        "project_urls": config["urls"],
        "package_dir": {"": "src"},
        "packages": find_packages(where="src"),
        "install_requires": config["dependencies"],
        "extras_require": config["optional_dependencies"],
        "python_requires": config["requires_python"],
        "entry_points": entry_points,
        "classifiers": config["classifiers"],
        "include_package_data": True,
        "package_data": {
            "madengine": ["scripts/**/*", "scripts/**/.*"],
        },
        "zip_safe": False,
        "platforms": ["any"],
    }
    
    setup(**setup_kwargs)

if __name__ == "__main__":
    main()
