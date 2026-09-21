#!/usr/bin/env python3
"""
Jarvis Frontend Launcher
Launches the futuristic PyQt6 frontend for the Jarvis assistant.
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.test_output_manager import cleanup_test_output
from frontend.main_window import main


def run():
    """Run the frontend with startup test-output cleanup."""
    # Clean up leftover generated test-output files from previous runs
    try:
        deleted = cleanup_test_output()
        if deleted:
            print(f"Cleaned up {len(deleted)} leftover test output file(s)")
    except Exception as e:
        # Continue startup even if cleanup fails
        logging.warning(f"Test output cleanup failed during startup: {e}")

    main()


if __name__ == "__main__":
    run()