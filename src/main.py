import logging
from .logger import setup_logger
from .file_operations import FileOperations
from .package_manager import PackageManager
from .settings import DEFAULT_ROOT_DIRECTORY, DEFAULT_STRUCTURE_FILE, LOGGING

def main(project_root: str = DEFAULT_ROOT_DIRECTORY, structure_file: str = DEFAULT_STRUCTURE_FILE, packages: dict = None):
    """
    Main function to set up the project structure and install packages.

    :param project_root: Root directory for the project.
    :param structure_file: Path to the structure file.
    :param packages: Dictionary of packages to install (e.g., {'package_name': 'pip'}).
    """
    # Set up the logger
    logger = setup_logger('FileSystemTool', LOGGING['handlers']['file']['filename'])

    # Instantiate FileOperations and create the project structure
    file_ops = FileOperations(project_root, logger)
    file_ops.create_structure_from_file(structure_file)

    # Install packages if provided
    if packages:
        package_manager = PackageManager(logger)
        for package, manager in packages.items():
            package_manager.install_package(package, manager)

if __name__ == "__main__":
    # Example usage
    packages_to_install = {
        'requests': 'pip',
        'express': 'npm',
    }
    main(packages=packages_to_install)