"""
Dependency Manager - Handles automatic installation of optional dependencies

This module provides utilities to check for and automatically install
missing optional dependencies required by various components of GameTrainer.

Following clean code principles: Single Responsibility - handles dependency management only.
"""

import sys
import subprocess
from typing import Dict, List


def ensure_dependencies(required_packages: Dict[str, str] = None) -> None:
    """
    Checks for and automatically installs missing optional dependencies.
    
    Time complexity: O(1) per package check, O(n) for installation where n is package size.
    
    Args:
        required_packages: Dictionary mapping install names to import names.
                          If None, uses default optional dependencies.
                          Example: {'tqdm': 'tqdm', 'pywin32': 'win32gui'}
    
    Following clean code principles: Single Responsibility - handles dependency management.
    """
    if required_packages is None:
        # Default optional dependencies for GameTrainer
        # pywin32 is imported as 'win32gui', but installed as 'pywin32'
        required_packages = {
            'tqdm': 'tqdm',
            'rich': 'rich',
            'pywin32': 'win32gui'
        }
    
    missing_packages: List[str] = []
    
    # Check which packages are missing
    for install_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(install_name)
    
    # Install missing packages if any
    if missing_packages:
        print(f"Installing missing dependencies: {', '.join(missing_packages)}...")
        for package in missing_packages:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"  ✓ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"  ✗ Failed to install {package} - continuing anyway")
        print()


def check_package_available(package_name: str) -> bool:
    """
    Checks if a specific package is available for import.
    
    Time complexity: O(1) - simple import check.
    
    Args:
        package_name: The import name of the package (e.g., 'tqdm', 'win32gui')
    
    Returns:
        bool: True if package is available, False otherwise
    """
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def check_progress_bar_available() -> bool:
    """
    Checks if tqdm and rich are available for progress bar functionality.
    
    Time complexity: O(1) - simple import checks.
    
    Returns:
        bool: True if both tqdm and rich are available, False otherwise
    """
    return check_package_available('tqdm') and check_package_available('rich')

