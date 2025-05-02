import os
import re
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .node import Node
from .settings import (
    IGNORED_FILE_EXTENSIONS,
    IGNORED_DIRECTORIES,
    DEFAULT_ENCODING,
    MAX_NAME_LENGTH,
    ALLOWED_CHARACTERS,
    REPLACE_CHARACTERS,
    REPLACEMENT_CHARACTER,
    ERROR_HANDLING,
    FILE_CONTENT_MARKERS,
    DIRECTORY_STRUCTURE_INDICATORS,
)

class FileOperations:
    def __init__(self, project_root: str, logger: logging.Logger):
        """
        Initialize the FileOperations class.

        :param project_root: The root directory where operations will be performed.
        :param logger: Logger instance for logging information.
        """
        self.project_root = Path(project_root).resolve()
        self.logger = logger

        # Load ignored files and directories from settings
        self.ignored_extensions = IGNORED_FILE_EXTENSIONS
        self.ignored_directories = IGNORED_DIRECTORIES

    def sanitize_name(self, name: str) -> str:
        """
        Sanitize a directory or file name by removing invalid characters and ensuring it is valid for the file system.

        :param name: The name to sanitize.
        :return: The sanitized name.
        """
        # Remove invalid characters
        sanitized_name = re.sub(REPLACE_CHARACTERS, REPLACEMENT_CHARACTER, name)

        # Replace multiple spaces or underscores with a single underscore
        sanitized_name = re.sub(r'(?<!_)_+(?!_)', REPLACEMENT_CHARACTER, sanitized_name)

        # Remove leading/trailing whitespace or underscores
        sanitized_name = sanitized_name.strip(' _')

        # Replace parentheses and curly braces with underscores
        sanitized_name = re.sub(r'[(){}\[\]]', REPLACEMENT_CHARACTER, sanitized_name)

        # If the name is empty after sanitization, use a default name
        if not sanitized_name:
            sanitized_name = "untitled"
            self.logger.info(f"Name sanitized to default: {sanitized_name}")

        # Ensure the name is not too long
        if len(sanitized_name) > MAX_NAME_LENGTH:
            sanitized_name = sanitized_name[:MAX_NAME_LENGTH]
            self.logger.info(f"Name truncated to {MAX_NAME_LENGTH} characters: {sanitized_name}")

        return sanitized_name

    def create_directory(self, dir_path: Path) -> None:
        """
        Create a directory at the specified path.

        :param dir_path: Path to the directory to create.
        """
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {dir_path}")
            print(f"Created directory: {dir_path}")
        except Exception as e:
            self.handle_error(f"Error creating directory {dir_path}: {str(e)}")

    def create_file(self, file_path: Path, content: str = "") -> None:
        """
        Create a file at the specified path with optional content.

        :param file_path: Path to the file to create.
        :param content: Content to write to the file.
        """
        try:
            # Ensure the parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open('w', encoding=DEFAULT_ENCODING) as f:
                f.write(content)
            self.logger.info(f"Created file: {file_path}")
            print(f"Created file: {file_path}")
        except Exception as e:
            self.handle_error(f"Error creating file {file_path}: {str(e)}")

    def parse_structure(self, lines: List[str]) -> Node:
        """
        Parse a directory structure from a list of lines and create a tree of Nodes.

        :param lines: List of lines representing the directory structure.
        :return: The root node of the parsed structure.
        """
        root = Node('root', is_directory=True)
        stack = [(-1, root)]  # Stack to track parent nodes and their indentation levels
        current_file = None  # Track the current file being processed
        file_content = []  # Store the content of the current file
        current_path = self.project_root  # Track the current directory path

        for line in lines:
            # Remove special characters and trailing whitespace
            stripped_line = re.sub(r'[│├└─]', '', line).rstrip()

            # Skip empty lines
            if not stripped_line:
                continue

            # Calculate indentation level
            indent = len(stripped_line) - len(stripped_line.lstrip(' '))
            name = stripped_line.strip()

            # If we are currently processing a file's content
            if current_file is not None:
                # Check if the indentation level matches the file's content
                if indent > current_file['indent']:
                    file_content.append(stripped_line)
                    continue
                else:
                    # Write the content to the file
                    self.create_file(current_file['path'], '\n'.join(file_content))
                    current_file = None
                    file_content = []

            # Skip ignored files and directories
            if any(name.endswith(ext) for ext in self.ignored_extensions) or name in self.ignored_directories:
                self.logger.info(f"Skipping ignored file/directory: {name}")
                continue

            # Sanitize the name
            sanitized_name = self.sanitize_name(name)
            if sanitized_name != name:
                self.logger.info(f"Sanitized name: {name} -> {sanitized_name}")

            # Determine if it's a directory or file
            is_directory = name.endswith(DIRECTORY_STRUCTURE_INDICATORS['directory']) or (
                DIRECTORY_STRUCTURE_INDICATORS['file'] not in name and not name.startswith('**')
            )

            # Pop the stack until we find the correct parent
            while stack and indent <= stack[-1][0]:
                stack.pop()
                # Update the current path to the parent directory
                current_path = current_path.parent

            # Add the node to the parent
            parent = stack[-1][1]
            node = Node(sanitized_name, is_directory)
            parent.add_child(node)

            # If it's a directory, push it onto the stack and create the directory
            if is_directory:
                stack.append((indent, node))
                dir_path = current_path / sanitized_name
                self.create_directory(dir_path)
                current_path = dir_path  # Update the current path to the new directory
            else:
                # If it's a file, start capturing its content
                current_file = {
                    'path': current_path / sanitized_name,
                    'indent': indent
                }

            self.logger.info(f"Parsed {'directory' if is_directory else 'file'}: {sanitized_name} (indent: {indent})")

        # Write the content of the last file (if any)
        if current_file is not None:
            self.create_file(current_file['path'], '\n'.join(file_content))

        return root

    def create_structure_from_file(self, structure_file: str) -> None:
        """
        Create a directory structure from a file, skipping invalid or ignored files/directories.

        :param structure_file: Path to the file containing the directory structure.
        :raises FileNotFoundError: If the structure file does not exist.
        :raises ValueError: If the structure file is empty or contains invalid data.
        """
        # Validate the structure file
        if not os.path.exists(structure_file):
            raise FileNotFoundError(f"Structure file not found: {structure_file}")

        # Read the structure file
        try:
            with open(structure_file, 'r', encoding=DEFAULT_ENCODING) as file:
                lines = file.readlines()
                self.logger.info(f"Read structure file: {structure_file}")
        except Exception as e:
            self.handle_error(f"Error reading structure file {structure_file}: {str(e)}")
            return

        # Validate that the file is not empty
        if not lines:
            raise ValueError("Structure file is empty.")

        # Parse the structure and create the directory tree
        try:
            root = self.parse_structure(lines)
            self.logger.info(f"Parsed root node: {root.name}")
            self._create_from_tree(root, self.project_root)
            self.logger.info(f"Successfully created structure from file: {structure_file}")
        except Exception as e:
            self.handle_error(f"Error creating structure from file {structure_file}: {str(e)}")

    def _create_from_tree(self, node: Node, current_path: Path) -> None:
        """
        Recursively create directories and files from a tree structure.

        :param node: Current node in the tree.
        :param current_path: Current path in the file system.
        """
        for child in node.children:
            child_path = current_path / child.name

            # Skip ignored files and directories
            if any(child.name.endswith(ext) for ext in self.ignored_extensions) or child.name in self.ignored_directories:
                self.logger.info(f"Skipping ignored file/directory: {child.name}")
                continue

            if child.is_directory:
                self.logger.info(f"Creating directory: {child_path}")
                self.create_directory(child_path)
                self._create_from_tree(child, child_path)
            else:
                self.logger.info(f"Creating file: {child_path}")
                self.create_file(child_path)

    def output_directory_structure(self, root_directory: str, output_file: Optional[str] = None, include_contents: bool = False) -> None:
        """
        Output the directory structure of the specified root directory to a text file.

        :param root_directory: The root directory to analyze.
        :param output_file: The output text file to write the structure.
        :param include_contents: Whether to include file contents in the output.
        """
        if output_file is None:
            day=str(datetime.now().month)+str(datetime.now().day)+str(datetime.now().hour)+str(datetime.now().second)
            output_file = os.path.join(os.getcwd(), ('directory_structure_'+day+'.txt'))

        root_directory = Path(root_directory).resolve()

        with open(output_file, 'w', encoding=DEFAULT_ENCODING) as f:
            for dirpath, dirnames, filenames in os.walk(root_directory):
                # Remove ignored directories from the list of directories to traverse
                dirnames[:] = [d for d in dirnames if d not in self.ignored_directories]

                level = dirpath.replace(str(root_directory), '').count(os.sep)
                indent = '│   ' * level

                # Write the directory name
                f.write(f"{indent}{'├── ' if dirnames else '└── '}{os.path.basename(dirpath)}/\n")

                # Write each file in the directory
                for filename in filenames:
                    # Skip files with ignored extensions
                    if any(filename.endswith(ext) for ext in self.ignored_extensions):
                        self.logger.info(f"Skipping file {filename} with ignored extension")
                        continue

                    f.write(f"{indent}│   ├── {filename}\n")

                    if include_contents:
                        # Construct the full file path
                        file_path = os.path.join(dirpath, filename)

                        try:
                            # Read the file content
                            with open(file_path, 'r', encoding=DEFAULT_ENCODING) as file_content:
                                content = file_content.read()

                            # Write the file name and content
                            f.write(f"{indent}│       └── Contents of {filename}:\n")
                            for line in content.splitlines():
                                f.write(f"{indent}│           {line}\n")
                        except Exception as e:
                            # Log or print any errors encountered while reading a file
                            self.handle_error(f"Error reading file {file_path}: {e}")

        self.logger.info(f"Directory structure written to {output_file}")

    def handle_error(self, message: str) -> None:
        """
        Handle errors by logging and printing the error message.

        :param message: The error message to log and print.
        """
        if ERROR_HANDLING['log_errors']:
            self.logger.error(message)
        if ERROR_HANDLING['print_errors']:
            print(message)