"""
Pytest configuration for Jarvis test suite.
Ensures proper import paths and shared fixtures.
"""

import sys
import os

# Add project root to path so tests can import jarvis, location, etc.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_output_manager import ensure_test_output_dir


def pytest_configure(config):
    """Ensure test output directory exists before running any tests."""
    try:
        ensure_test_output_dir()
    except Exception as e:
        print(f"Warning: Could not create test output directory: {e}")
