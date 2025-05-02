import os  # Import the os module
from pathlib import Path
from typing import List, Optional

from .src.file_operations import FileOperations
from .src.package_manager import PackageManager
from .src.node import Node
from .src.logger import setup_logger

# Set up the logger for the package
logger = setup_logger('MyLogger', 'my_log.log')

__all__ = [
    "FileOperations",
    "PackageManager",
    "Node",
    "create_structure_from_file",
    "install_package",
    "output_directory_structure",
    "recreate_structure_from_file",
    "logger"
]

def create_structure_from_file(structure_file: str, project_root: Optional[str] = None, logger=logger) -> None:
    """
    Create a project structure from a given structure file.

    :param structure_file: Path to the file containing the project structure.
    :param project_root: Root directory where the project structure will be created.
                         Defaults to the current working directory if not provided.
    :param logger: Logger instance for logging information.
    """
    if project_root is None:
        project_root = os.getcwd()

    file_ops = FileOperations(project_root, logger)
    file_ops.create_structure_from_file(structure_file)

def install_package(package_name: str, package_manager_type: str, logger=logger) -> None:
    """
    Install a package using the specified package manager.
    
    :param package_name: Name of the package to install.
    :param package_manager_type: Type of package manager (e.g., 'pip', 'npm').
    :param logger: Logger instance for logging information.
    """
    package_manager = PackageManager(logger)
    package_manager.install_package(package_name, package_manager_type)

def output_directory_structure(root_directory: str, output_file: str = None, include_contents: bool = False, logger=logger) -> None:
    """
    Outputs the directory structure of the specified root directory to a text file,
    with an option to include file contents.
    
    :param root_directory: The root directory to analyze.
    :param output_file: The output text file to write the structure.
                        Defaults to "directory_structure.txt" in the current directory if not provided.
    :param include_contents: Whether to include file contents in the output. Defaults to False.
    :param logger: Logger instance for logging information.
    """
    file_ops = FileOperations(root_directory, logger)
    file_ops.output_directory_structure(root_directory, output_file, include_contents)
def recreate_structure_from_file(root_directory: str, structure_file: str, files: str, logger=logger) -> None:
    """
    Recreate the directory structure from a given structure file.
    
    :param root_directory: The root directory where the structure will be recreated.
    :param structure_file: Path to the file containing the project structure to recreate.
    :param files: Path to the file containing the contents of the files to recreate.
    :param logger: Logger instance for logging information.
    """
    file_ops = FileOperations(root_directory, logger)
    file_ops.recreate_structure_from_file(structure_file=structure_file, files=files)