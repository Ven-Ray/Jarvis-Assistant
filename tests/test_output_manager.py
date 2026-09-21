"""
Test output management for Jarvis.
Provides shared cleanup of generated test-output .txt files.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Approved directory for generated test output (relative to project root)
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "output")

# Confirmed generated test-output filenames (not fixtures, not user data)
GENERATED_TEST_FILES = [
    "test_lm_output.txt",
    "test_output.txt",
    "test_results.txt",
    "test_run_output.txt",
]


def cleanup_test_output(output_dir=None):
    """
    Remove leftover generated test-output .txt files from previous runs.

    Args:
        output_dir: Directory to clean. Defaults to TEST_OUTPUT_DIR (tests/).

    Returns:
        List of successfully deleted file paths.
    """
    if output_dir is None:
        output_dir = TEST_OUTPUT_DIR

    # Resolve to absolute path for safety checks
    abs_output_dir = os.path.abspath(output_dir)

    deleted_files = []

    for filename in GENERATED_TEST_FILES:
        filepath = os.path.join(abs_output_dir, filename)

        # Safety check: verify target is inside approved directory
        if not os.path.abspath(filepath).startswith(abs_output_dir):
            logger.warning(f"Skipping {filename}: path escapes approved directory")
            continue

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted_files.append(filepath)
                logger.info(f"Deleted leftover test output: {filepath}")
            else:
                logger.debug(f"No leftover file to delete: {filepath}")
        except OSError as e:
            logger.warning(f"Failed to delete {filepath}: {e}")

    return deleted_files


def get_test_output_path(filename):
    """
    Get the full path for a test output file in the approved directory.

    Args:
        filename: Name of the test output file.

    Returns:
        Full absolute path within TEST_OUTPUT_DIR.
    """
    return os.path.join(TEST_OUTPUT_DIR, filename)


def ensure_test_output_dir():
    """Ensure the test output directory exists."""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    return TEST_OUTPUT_DIR
