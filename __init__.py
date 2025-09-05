# filesystemtool/__init__.py
import os
from pathlib import Path
from typing import Optional

# Assuming logger setup is desired when the package is imported,
# or it's handled per-operation.
# from .src.logger import setup_logger
# logger = setup_logger('FileSystemToolLogger', 'filesystemtool.log') # Or configure path better

from .src.file_operations import FileOperations
from .src.package_manager import PackageManager
from .src.node import Node
from .src.logger import setup_logger # Keep for explicit setup if needed

# Expose the main functions
def create_structure_from_file(structure_file: str, project_root: Optional[str] = None, logger_instance=None) -> None:
    if project_root is None:
        project_root = os.getcwd()
    if logger_instance is None:
        # Default logger if none provided for this specific operation
        logger_instance = setup_logger('FSOpsCreate', 'fsops_create.log')
    file_ops = FileOperations(project_root, logger_instance)
    file_ops.create_structure_from_file(structure_file)

def output_directory_structure(root_directory: str, output_file: Optional[str] = None, include_contents: bool = False, logger_instance=None) -> None:
    if logger_instance is None:
        logger_instance = setup_logger('FSOpsOutput', 'fsops_output.log')
    file_ops = FileOperations(root_directory, logger_instance) # root_directory for FileOps might be different here
    file_ops.output_directory_structure(root_dir_to_scan=root_directory, output_file_path=output_file, include_contents=include_contents)

def recreate_structure_from_file(root_directory: str, structure_definition_file: str, files_content_file: str, logger_instance=None) -> None:
    if logger_instance is None:
        logger_instance = setup_logger('FSOpsRecreate', 'fsops_recreate.log')
    file_ops = FileOperations(root_directory, logger_instance)
    file_ops.recreate_structure_from_file(structure_definition_file_path=structure_definition_file, files_content_file_path=files_content_file)

def install_package(package_name: str, package_manager_type: str, logger_instance=None) -> None:
    if logger_instance is None:
        logger_instance = setup_logger('FSPkgInstall', 'fspkg_install.log')
    package_manager = PackageManager(logger_instance)
    package_manager.install_package(package_name, package_manager_type)


__all__ = [
    "FileOperations", # If you want to expose the class itself
    "PackageManager", # If you want to expose the class itself
    "Node",           # If you want to expose the class itself
    "create_structure_from_file",
    "install_package",
    "output_directory_structure",
    "recreate_structure_from_file",
    "setup_logger" # Expose if users need to create custom loggers
]

# Consider where logger is initialized. If it's module-global,
# its file path needs careful consideration (e.g., user's home dir, temp dir).
# For a CLI tool, logging might be configured per command.