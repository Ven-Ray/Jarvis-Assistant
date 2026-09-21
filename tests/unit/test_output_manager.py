"""
Tests for test output management and cleanup behavior.
Verifies that generated test-output .txt files are properly managed,
consolidated, and cleaned up at startup and shutdown.
"""

import os
import sys
import tempfile
import shutil
import logging
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_output_manager import (
    cleanup_test_output,
    get_test_output_path,
    ensure_test_output_dir,
    GENERATED_TEST_FILES,
)


class TestFileClassification:
    """Test that the original four files are classified correctly."""

    def test_all_four_files_are_in_generated_list(self):
        """All four identified test-output files should be in GENERATED_TEST_FILES."""
        expected = [
            "test_lm_output.txt",
            "test_output.txt",
            "test_results.txt",
            "test_run_output.txt",
        ]
        for filename in expected:
            assert filename in GENERATED_TEST_FILES, f"{filename} not in generated list"

    def test_requirements_txt_not_in_generated_list(self):
        """requirements.txt is a dependency manifest, not generated test output."""
        assert "requirements.txt" not in GENERATED_TEST_FILES


class TestCleanupFunction:
    """Test the shared cleanup function behavior."""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cleanup_removes_generated_files(self):
        """Cleanup should remove all generated test-output files."""
        # Create fake generated files
        for filename in GENERATED_TEST_FILES:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, "w") as f:
                f.write("test output")

        deleted = cleanup_test_output(self.test_dir)

        assert len(deleted) == 4
        for filename in GENERATED_TEST_FILES:
            filepath = os.path.join(self.test_dir, filename)
            assert not os.path.exists(filepath), f"{filename} should be deleted"

    def test_cleanup_preserves_unrelated_files(self):
        """Cleanup should not delete files that are not generated test output."""
        # Create unrelated file
        unrelated_path = os.path.join(self.test_dir, "requirements.txt")
        with open(unrelated_path, "w") as f:
            f.write("dependencies")

        # Create one generated file
        gen_path = os.path.join(self.test_dir, "test_output.txt")
        with open(gen_path, "w") as f:
            f.write("test output")

        deleted = cleanup_test_output(self.test_dir)

        assert len(deleted) == 1
        assert os.path.exists(unrelated_path), "requirements.txt should be preserved"
        assert not os.path.exists(gen_path), "test_output.txt should be deleted"

    def test_cleanup_safe_when_no_files_exist(self):
        """Cleanup should work even when no generated files exist."""
        deleted = cleanup_test_output(self.test_dir)
        assert len(deleted) == 0

    def test_cleanup_idempotent(self):
        """Calling cleanup multiple times should be safe."""
        # Create a generated file
        gen_path = os.path.join(self.test_dir, "test_output.txt")
        with open(gen_path, "w") as f:
            f.write("test output")

        deleted1 = cleanup_test_output(self.test_dir)
        assert len(deleted1) == 1

        # Second call should not fail and delete nothing
        deleted2 = cleanup_test_output(self.test_dir)
        assert len(deleted2) == 0

    def test_cleanup_logs_successful_deletions(self, caplog):
        """Successful deletions should be logged."""
        gen_path = os.path.join(self.test_dir, "test_output.txt")
        with open(gen_path, "w") as f:
            f.write("test output")

        with caplog.at_level(logging.INFO):
            cleanup_test_output(self.test_dir)

        assert any("Deleted leftover test output" in record.message for record in caplog.records)

    def test_cleanup_logs_deletion_failures(self, caplog):
        """Failed deletions should be logged as warnings."""
        gen_path = os.path.join(self.test_dir, "test_output.txt")
        with open(gen_path, "w") as f:
            f.write("test output")

        # Make file unreadable/unremovable (on Unix) or use a mock to simulate failure
        with patch("os.remove", side_effect=OSError("Permission denied")):
            with caplog.at_level(logging.WARNING):
                cleanup_test_output(self.test_dir)

        assert any("Failed to delete" in record.message for record in caplog.records)

    def test_cleanup_continues_on_failure(self):
        """If one deletion fails, others should still be attempted."""
        # Create two generated files
        gen1 = os.path.join(self.test_dir, "test_output.txt")
        gen2 = os.path.join(self.test_dir, "test_results.txt")
        with open(gen1, "w") as f:
            f.write("output 1")
        with open(gen2, "w") as f:
            f.write("output 2")

        # Make first file fail to delete
        original_remove = os.remove

        def failing_remove(path):
            if path == gen1:
                raise OSError("Permission denied")
            return original_remove(path)

        with patch("os.remove", side_effect=failing_remove):
            deleted = cleanup_test_output(self.test_dir)

        # Only the second file should be deleted
        assert len(deleted) == 1
        assert gen2 in [d for d in deleted]


class TestPathSafety:
    """Test that cleanup only deletes files within the approved directory."""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cleanup_validates_path_is_inside_directory(self):
        """Cleanup should verify target paths are inside the approved directory."""
        # Create a file outside the test dir with same name as generated file
        outside_file = os.path.join(tempfile.gettempdir(), "test_output.txt")
        try:
            with open(outside_file, "w") as f:
                f.write("outside")

            deleted = cleanup_test_output(self.test_dir)

            # Should not delete the outside file
            assert len(deleted) == 0
            assert os.path.exists(outside_file), "File outside approved dir should be preserved"
        finally:
            if os.path.exists(outside_file):
                os.remove(outside_file)


class TestStartupCleanupIntegration:
    """Test that startup cleanup is integrated correctly."""

    def test_run_frontend_imports_cleanup(self):
        """run_frontend.py should import and use cleanup_test_output."""
        with open("f:/Code/Jarvis/run_frontend.py", "r") as f:
            content = f.read()

        assert "cleanup_test_output" in content, "run_frontend.py should use cleanup function"

    def test_startup_cleanup_called_before_main(self):
        """Cleanup should be called before the frontend main loop starts."""
        with open("f:/Code/Jarvis/run_frontend.py", "r") as f:
            lines = f.readlines()

        # Find line numbers for cleanup call and main() call
        cleanup_line = None
        main_line = None
        for i, line in enumerate(lines):
            if "cleanup_test_output()" in line:
                cleanup_line = i
            if "main()" in line and "def" not in line:
                main_line = i

        assert cleanup_line is not None, "Cleanup call not found"
        assert main_line is not None, "Main call not found"
        assert cleanup_line < main_line, "Cleanup should be called before main()"


class TestShutdownCleanupIntegration:
    """Test that shutdown cleanup is integrated correctly."""

    def test_main_window_connects_cleanup_to_about_to_quit(self):
        """Frontend should connect cleanup to the aboutToQuit signal."""
        with open("f:/Code/Jarvis/frontend/main_window.py", "r") as f:
            content = f.read()

        assert "aboutToQuit" in content, "Should use aboutToQuit signal for shutdown cleanup"
        assert "cleanup_test_output" in content, "Should call cleanup on shutdown"


class TestOutputLocation:
    """Test that test output is written to the approved location."""

    def test_get_test_output_path_returns_tests_directory(self):
        """get_test_output_path should return a path within tests/ directory."""
        path = get_test_output_path("test_output.txt")
        assert "tests" in path, f"Path {path} should be within tests/ directory"

    def test_ensure_test_output_dir_creates_directory(self):
        """ensure_test_output_dir should create the tests/ directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change TEST_OUTPUT_DIR for this test
            import tests.test_output_manager as tom
            original = tom.TEST_OUTPUT_DIR
            try:
                new_dir = os.path.join(tmpdir, "tests")
                tom.TEST_OUTPUT_DIR = new_dir

                result = ensure_test_output_dir()

                assert os.path.exists(result), "Directory should be created"
                assert result == new_dir
            finally:
                tom.TEST_OUTPUT_DIR = original


class TestConcurrentRuns:
    """Test that concurrent test runs don't overwrite or corrupt output."""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cleanup_does_not_affect_other_files_during_concurrent_runs(self):
        """Cleanup should only affect generated test files, not other concurrent output."""
        # Simulate two concurrent runs creating different output files
        run1_file = os.path.join(self.test_dir, "test_output.txt")
        run2_file = os.path.join(self.test_dir, "other_test_output.txt")

        with open(run1_file, "w") as f:
            f.write("run 1")
        with open(run2_file, "w") as f:
            f.write("run 2")

        # Cleanup should only delete the known generated file
        deleted = cleanup_test_output(self.test_dir)

        assert len(deleted) == 1
        assert run1_file in [d for d in deleted]
        assert os.path.exists(run2_file), "Other concurrent output should be preserved"


class TestFileReduction:
    """Test that the number of generated test-output files is reduced."""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cleanup_reduces_file_count(self):
        """Cleanup should reduce the number of generated .txt files to zero."""
        # Create all four generated files
        for filename in GENERATED_TEST_FILES:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, "w") as f:
                f.write("test output")

        initial_count = len([f for f in os.listdir(self.test_dir) if f.endswith(".txt")])
        assert initial_count == 4

        cleanup_test_output(self.test_dir)

        final_count = len([f for f in os.listdir(self.test_dir) if f.endswith(".txt")])
        assert final_count == 0, "All generated test files should be removed"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
