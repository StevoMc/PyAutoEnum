"""
Test configuration for PyAutoEnum.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Set environment variables for testing
os.environ['LOG_LEVEL'] = 'ERROR'
os.environ['PYTHONPATH'] = '.'

# Set up fixtures
import pytest


@pytest.fixture
def sample_target_info():
    """Create a sample TargetInfo for testing."""
    from pyautoenum.config.manager import ConfigManager
    from pyautoenum.data.models import TargetInfo
    
    config = ConfigManager()
    return TargetInfo(config, ip="192.168.1.1", hostname="example.com")
