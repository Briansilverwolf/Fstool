import unittest
from unittest.mock import patch
from project.src.package_manager import PackageManager
from project.src.settings import IGNORED_PACKAGES
import logging

class TestPackageManager(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.logger = logging.getLogger('TestLogger')
        self.manager = PackageManager(self.logger)

    @patch('subprocess.run')
    def test_install_package_success(self, mock_run):
        """Test successful package installation."""
        self.manager.install_package('requests', 'pip')
        mock_run.assert_called_once_with(['pip', 'install', 'requests'], check=True)

    @patch('subprocess.run')
    def test_install_ignored_package(self, mock_run):
        """Test that ignored packages are skipped."""
        ignored_package = IGNORED_PACKAGES[0]
        self.manager.install_package(ignored_package, 'pip')
        mock_run.assert_not_called()

if __name__ == "__main__":
    unittest.main()