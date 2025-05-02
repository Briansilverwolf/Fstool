import unittest
from pathlib import Path
from project.src.file_operations import FileOperations
from project.src.settings import IGNORED_FILE_EXTENSIONS, IGNORED_DIRECTORIES
import logging

class TestFileOperations(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.project_root = Path("test_project")
        self.logger = logging.getLogger('TestLogger')
        self.file_ops = FileOperations(self.project_root, self.logger)

    def test_sanitize_name(self):
        """Test the sanitize_name method."""
        test_name = "invalid/name*file?.txt"
        sanitized_name = self.file_ops.sanitize_name(test_name)
        self.assertNotIn('/', sanitized_name)
        self.assertNotIn('*', sanitized_name)
        self.assertNotIn('?', sanitized_name)

    def test_create_directory(self):
        """Test the create_directory method."""
        test_dir = self.project_root / "test_dir"
        self.file_ops.create_directory(test_dir)
        self.assertTrue(test_dir.exists())

    def test_ignored_files_and_directories(self):
        """Test that ignored files and directories are skipped."""
        ignored_file = self.project_root / "ignored_file.pyc"
        ignored_dir = self.project_root / "node_modules"
        self.file_ops.create_file(ignored_file)
        self.file_ops.create_directory(ignored_dir)
        self.assertFalse(ignored_file.exists())
        self.assertFalse(ignored_dir.exists())

if __name__ == "__main__":
    unittest.main()