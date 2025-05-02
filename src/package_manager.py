import subprocess
import logging
from .settings import IGNORED_PACKAGES, PACKAGE_MANAGERS

class PackageManager:
    def __init__(self, logger: logging.Logger):
        """
        Initialize the PackageManager.

        :param logger: Logger instance for logging information.
        """
        self.logger = logger

    def install_package(self, package_name: str, package_manager_type: str) -> None:
        """
        Install a package using the specified package manager.

        :param package_name: Name of the package to install.
        :param package_manager_type: Type of package manager (e.g., 'pip', 'npm').
        """
        # Skip ignored packages
        if package_name in IGNORED_PACKAGES:
            self.logger.info(f"Skipping ignored package: {package_name}")
            return

        # Get the package manager configuration
        if package_manager_type not in PACKAGE_MANAGERS:
            self.logger.error(f"Unsupported package manager: {package_manager_type}")
            return

        manager_config = PACKAGE_MANAGERS[package_manager_type]
        command = [manager_config['command'], manager_config['install_command'], package_name]

        try:
            # Run the package installation command
            subprocess.run(command, check=True)
            self.logger.info(f"Successfully installed package: {package_name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install package {package_name}: {e}")