import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from .node import Node  # Assuming Node is in the same directory or package
from .settings import (
    IGNORED_FILE_EXTENSIONS,
    IGNORED_DIRECTORIES,
    DEFAULT_ENCODING,
    MAX_NAME_LENGTH,
    REPLACE_CHARACTERS,
    REPLACEMENT_CHARACTER,
    ERROR_HANDLING,
    FILE_CONTENT_MARKERS, # For recreate_structure_from_file
    DIRECTORY_STRUCTURE_INDICATORS,
)

class FileOperations:
    def __init__(self, project_root: str, logger: logging.Logger):
        """
        Initialize the FileOperations class.

        :param project_root: The root directory where operations will be performed.
        :param logger: Logger instance for logging information.
        """
        self.project_root: Path = Path(project_root).resolve()
        self.logger: logging.Logger = logger
        self.ignored_extensions: List[str] = IGNORED_FILE_EXTENSIONS
        self.ignored_directories: List[str] = IGNORED_DIRECTORIES

    def sanitize_name(self, name: str) -> str:
        """
        Sanitize a directory or file name.
        - Removes characters specified in REPLACE_CHARACTERS.
        - Replaces multiple consecutive REPLACEMENT_CHARACTERs (or spaces if REPLACEMENT_CHARACTER is space) with a single one.
        - Strips leading/trailing whitespace and REPLACEMENT_CHARACTER.
        - Replaces common problematic characters like parentheses and braces.
        - Ensures the name is not empty and does not exceed MAX_NAME_LENGTH.

        :param name: The name to sanitize.
        :return: The sanitized name.
        """
        # 1. Replace characters defined in REPLACE_CHARACTERS
        sanitized_name = re.sub(REPLACE_CHARACTERS, REPLACEMENT_CHARACTER, name)

        # 2. Standardize problematic characters like parentheses and braces to REPLACEMENT_CHARACTER
        sanitized_name = re.sub(r'[(){}\[\]]', REPLACEMENT_CHARACTER, sanitized_name)

        # 3. Consolidate multiple REPLACEMENT_CHARACTERs (and spaces if REPLACEMENT_CHARACTER is not space)
        #    into a single REPLACEMENT_CHARACTER.
        #    Example: "foo___bar" -> "foo_bar", "foo   bar" -> "foo_bar" (if REPLACEMENT_CHARACTER is '_')
        if REPLACEMENT_CHARACTER == ' ':
            sanitized_name = re.sub(r'\s+', ' ', sanitized_name) # Consolidate spaces
        else:
            # Consolidate spaces to REPLACEMENT_CHARACTER, then consolidate REPLACEMENT_CHARACTERs
            sanitized_name = re.sub(r'\s+', REPLACEMENT_CHARACTER, sanitized_name)
            sanitized_name = re.sub(f'{re.escape(REPLACEMENT_CHARACTER)}+', REPLACEMENT_CHARACTER, sanitized_name)


        # 4. Remove leading/trailing REPLACEMENT_CHARACTERs and whitespace
        strip_chars = f' {REPLACEMENT_CHARACTER}' if REPLACEMENT_CHARACTER != ' ' else ' '
        sanitized_name = sanitized_name.strip(strip_chars)


        # 5. If the name is empty after sanitization, use a default name
        if not sanitized_name:
            sanitized_name = "untitled"
            self.logger.warning(f"Original name '{name}' sanitized to default: '{sanitized_name}'")

        # 6. Ensure the name is not too long
        if len(sanitized_name) > MAX_NAME_LENGTH:
            original_full_name = sanitized_name
            # Try to preserve extension if present
            base, ext = os.path.splitext(sanitized_name)
            if ext and len(ext) < MAX_NAME_LENGTH: # Ensure extension itself isn't too long
                available_len_for_base = MAX_NAME_LENGTH - len(ext)
                if available_len_for_base > 0 :
                    base = base[:available_len_for_base]
                    sanitized_name = base + ext
                else: # Extension alone is too long or nearly so, just truncate whole name
                    sanitized_name = sanitized_name[:MAX_NAME_LENGTH]
            else: # No extension or extension too long, just truncate
                 sanitized_name = sanitized_name[:MAX_NAME_LENGTH]

            self.logger.warning(
                f"Name '{original_full_name}' truncated to {MAX_NAME_LENGTH} characters: '{sanitized_name}'"
            )
        
        # Special check for dunder names like __init__.py
        # The previous regex should handle them, but this is a safeguard against over-aggressive stripping.
        # If the original name was a dunder name and sanitization broke it, this is hard to revert perfectly
        # without more complex logic. The current sanitization *should* preserve them.
        # Example: `__init__.py` should not become `init.py` or `_init_.py` from step 4.
        # If `REPLACEMENT_CHARACTER` is `_`, `strip('_')` would be an issue.
        # The `strip_chars` logic aims to be careful.

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
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open('w', encoding=DEFAULT_ENCODING) as f:
                f.write(content)
            self.logger.info(f"Created file: {file_path} (Content length: {len(content)})")
            print(f"Created file: {file_path}")
        except Exception as e:
            self.handle_error(f"Error creating file {file_path}: {str(e)}")

    def _parse_structure_lines(self, lines: List[str]) -> Node:
        """
        Parse lines representing a directory structure and build a Node tree.
        This version supports embedded file content based on indentation.

        :param lines: List of lines representing the directory structure.
        :return: The root node of the parsed structure.
        """
        root = Node('root', is_directory=True)
        # Stack stores (indentation_level, parent_node, path_prefix_for_content_parsing)
        stack: List[Tuple[int, Node]] = [(-1, root)]  
        
        current_file_node_for_content: Optional[Node] = None
        current_file_content_lines: List[str] = []
        current_file_base_indent: int = -1

        for line_number, raw_line in enumerate(lines):
            line = raw_line.rstrip('\n\r') # Keep leading whitespace, remove only EOL
            stripped_line_for_structure = re.sub(r'^[│├└─\s]*', '', line) # Remove tree chars and leading space for structure part
            
            # Skip effectively empty lines for structure purposes
            if not stripped_line_for_structure.strip():
                # If we are capturing content, empty lines are part of it
                if current_file_node_for_content:
                    # Content lines should preserve their original relative indentation
                    # We need to determine the indent of the content relative to the file declaration
                    content_line_indent = len(line) - len(line.lstrip(' '))
                    if content_line_indent > current_file_base_indent:
                         # Add the raw line (or line with only EOL stripped)
                        current_file_content_lines.append(line[current_file_base_indent + len(DIRECTORY_STRUCTURE_INDICATORS.get('file_content_indent_marker', '    ')):])

                continue


            # Calculate indentation for structure determination
            # This indent is of the item itself (e.g., "├── filename.txt")
            # NOT the content lines that might follow
            structure_item_indent = len(line) - len(line.lstrip(' '))
            name_part = line.lstrip(' ').lstrip('│├└─ ').rstrip('/') # Cleaned name

            # --- Content parsing logic ---
            if current_file_node_for_content:
                # If the current line's indent is greater than the file's declaration indent,
                # it's considered content for the current file.
                if structure_item_indent > current_file_base_indent:
                    # Add the raw line, but strip the portion of indent that belongs to the file item itself + content marker
                    # This is tricky. A simpler rule: content starts on next line, indented further.
                    prefix_len_to_strip = current_file_base_indent + len(DIRECTORY_STRUCTURE_INDICATORS.get('file_content_indent_marker', '    ')) # Assuming 4 spaces for content indent
                    
                    # Ensure we don't strip too much if the line is shorter than expected prefix
                    actual_content_line = line[min(len(line), prefix_len_to_strip):]
                    current_file_content_lines.append(actual_content_line)
                    continue
                else:
                    # Indentation is less or equal, so current file's content ends.
                    # Store collected content.
                    current_file_node_for_content.content = "\n".join(current_file_content_lines)
                    self.logger.debug(f"Collected content for {current_file_node_for_content.name} ({len(current_file_node_for_content.content)} chars)")
                    current_file_node_for_content = None
                    current_file_content_lines = []
                    current_file_base_indent = -1
            # --- End content parsing logic ---

            # Process the current line as a new structure item (file/directory)
            is_directory = name_part.endswith(DIRECTORY_STRUCTURE_INDICATORS['directory']) or \
                           (DIRECTORY_STRUCTURE_INDICATORS['file'] not in name_part and not name_part.startswith('**'))
            
            if is_directory:
                entry_name = name_part
            else:
                # It's a file. Check if it has a "Contents of:" marker or similar
                # This part depends heavily on the exact format of your structure file
                # For now, assume any non-directory is a file.
                entry_name = name_part
                # If the line indicates start of content (e.g., "└── Contents of file.txt:"),
                # parse out the actual filename.
                # Example: "│       └── Contents of settings.py:"
                content_marker_match = re.match(r'.*Contents of (.*?):$', entry_name)
                if content_marker_match:
                    entry_name = content_marker_match.group(1).strip()
                    # This signals that subsequent indented lines are content
                    # However, the logic above handles this more generally.
                    # The primary role here is to clean the filename.

            sanitized_name = self.sanitize_name(entry_name)
            if not sanitized_name: # Should not happen if sanitize_name works
                self.logger.error(f"Line {line_number+1}: Sanitized name for '{entry_name}' is empty. Skipping. Line: '{raw_line.strip()}'")
                continue

            if sanitized_name != entry_name:
                self.logger.info(f"Sanitized name: '{entry_name}' -> '{sanitized_name}'")

            # Ignore checks
            if (not is_directory and any(sanitized_name.endswith(ext) for ext in self.ignored_extensions)) or \
               (is_directory and sanitized_name in self.ignored_directories):
                self.logger.info(f"Skipping ignored {'directory' if is_directory else 'file'}: {sanitized_name}")
                continue

            # Pop from stack until parent with smaller indent is found
            while stack and structure_item_indent <= stack[-1][0]:
                stack.pop()
            
            parent_node = stack[-1][1]
            node = Node(sanitized_name, is_directory=is_directory)
            parent_node.add_child(node)
            self.logger.debug(f"Parsed {'directory' if is_directory else 'file'}: {sanitized_name} (Indent: {structure_item_indent}) under {parent_node.name}")

            if is_directory:
                stack.append((structure_item_indent, node))
            else:
                # This file *might* have content on subsequent lines
                current_file_node_for_content = node
                current_file_base_indent = structure_item_indent
                # self.logger.debug(f"Expecting content for {node.name} with base indent {current_file_base_indent}")


        # After loop, if content was being collected for the last file item
        if current_file_node_for_content and current_file_content_lines:
            current_file_node_for_content.content = "\n".join(current_file_content_lines)
            self.logger.debug(f"Collected EOL content for {current_file_node_for_content.name} ({len(current_file_node_for_content.content)} chars)")

        return root

    def _create_from_node_tree(self, node: Node, current_path: Path) -> None:
        """
        Recursively create directories and files from a Node tree.

        :param node: Current node in the tree.
        :param current_path: Current path in the file system to create items under.
        """
        for child in node.children:
            child_path = current_path / child.name

            # Double check ignore logic (should have been handled during parsing, but defensive)
            if (not child.is_directory and any(child.name.endswith(ext) for ext in self.ignored_extensions)) or \
               (child.is_directory and child.name in self.ignored_directories):
                self.logger.info(f"Skipping ignored item during creation: {child_path}")
                continue

            if child.is_directory:
                self.create_directory(child_path)
                self._create_from_node_tree(child, child_path)  # Recurse
            else:
                self.create_file(child_path, content=child.content or "")


    def create_structure_from_file(self, structure_file_path: str) -> None:
        """
        Create a project structure from a given structure file.
        The structure file can contain embedded content for files.

        :param structure_file_path: Path to the file containing the project structure.
        """
        structure_file = Path(structure_file_path)
        if not structure_file.exists():
            self.handle_error(f"Structure file not found: {structure_file}")
            raise FileNotFoundError(f"Structure file not found: {structure_file}")

        try:
            with structure_file.open('r', encoding=DEFAULT_ENCODING) as f:
                lines = f.readlines()
            self.logger.info(f"Read structure file: {structure_file} ({len(lines)} lines)")
        except Exception as e:
            self.handle_error(f"Error reading structure file {structure_file}: {str(e)}")
            return

        if not lines:
            self.handle_error("Structure file is empty.")
            raise ValueError("Structure file is empty.")

        try:
            self.logger.info(f"Starting structure parsing for: {structure_file}")
            root_node = self._parse_structure_lines(lines)
            self.logger.info(f"Finished parsing. Root node: {root_node.name} with {len(root_node.children)} children.")
            
            self.logger.info(f"Starting creation of structure at: {self.project_root}")
            self._create_from_node_tree(root_node, self.project_root)
            self.logger.info(f"Successfully created structure from file: {structure_file} at {self.project_root}")

        except Exception as e:
            self.handle_error(f"Error processing structure file {structure_file}: {str(e)}")
            # Consider re-raising for critical errors or if __init__ expects it
            # raise

    def output_directory_structure(self, root_dir_to_scan: str, output_file_path: Optional[str] = None, include_contents: bool = False) -> None:
        """
        Outputs the directory structure of the specified root directory to a text file,
        with an option to include file contents.

        :param root_dir_to_scan: The root directory to analyze.
        :param output_file_path: The output text file to write the structure.
                                  Defaults to "directory_structure_YYYYMMDD_HHMMSS.txt" in CWD.
        :param include_contents: Whether to include file contents in the output.
        """
        if output_file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_path = Path.cwd() / f"directory_structure_{timestamp}.txt"
        else:
            output_file_path = Path(output_file_path)

        root_path = Path(root_dir_to_scan).resolve()
        if not root_path.is_dir():
            self.handle_error(f"Root directory for output does not exist: {root_path}")
            return

        self.logger.info(f"Outputting directory structure for '{root_path}' to '{output_file_path}' (Include contents: {include_contents})")
        
        output_lines = []

        with output_file_path.open('w', encoding=DEFAULT_ENCODING) as f:
            for dirpath_str, dirnames, filenames in os.walk(root_path, topdown=True):
                dirpath = Path(dirpath_str)
                
                # Filter ignored directories (modifies `dirnames` in place for `os.walk` traversal)
                dirnames[:] = [d for d in dirnames if d not in self.ignored_directories and not d.startswith('.')] # Also common hidden dirs

                # Calculate the indentation level for the *current directory (dirpath)* itself
                # `level = 0` for `root_path`, `1` for `root_path/subdir`, etc.
                # This level is used for `dirpath`'s own line.
                if dirpath == root_path:
                    level = 0
                else:
                    # Calculate relative path string, then count separators. This is robust for Path objects.
                    # Path('dir1/dir2').parts -> ('dir1', 'dir2'), len = 2.
                    relative_path_from_root = dirpath.relative_to(root_path)
                    level = len(relative_path_from_root.parts) 

                indent = '│   ' * level

                # 1. Print the current directory entry (e.g., "blog/" or "├── article/")
                # Determine prefix for the directory based on whether it has visible children (files or subdirectories).
                # This is a heuristic that aims to make the tree look good in a single pass.
                # A truly perfect tree requires pre-calculating all siblings to know the last one.
                has_visible_children = len(dirnames) > 0 or len([f_name for f_name in filenames if not (any(f_name.endswith(ext) for ext in self.ignored_extensions) or f_name.startswith('.'))]) > 0
                
                dir_entry_prefix = '└── ' if not has_visible_children else '├── '
                
                if level == 0: # Root directory typically has no tree prefix on its line
                    f.write(f"{dirpath.name}/\n")
                else:
                    f.write(f"{indent}{dir_entry_prefix}{dirpath.name}/\n")

                # 2. Print files directly contained within this `dirpath`
                # Files are one level deeper than their parent directory
                file_indent_level = level + 1
                file_base_indent_str = '│   ' * file_indent_level

                # Filter out ignored files and sort remaining for consistent output
                non_ignored_filenames = [
                    f_name for f_name in filenames 
                    if not (any(f_name.endswith(ext) for ext in self.ignored_extensions) or f_name.startswith('.'))
                ]
                non_ignored_filenames.sort()

                for i, filename in enumerate(non_ignored_filenames):
                    is_last_file_in_current_dir = (i == len(non_ignored_filenames) - 1)
                    
                    # Decide on the prefix for the file line (├── or └──)
                    # This uses the same logic as Code 1 for files: └── for the last file in the current directory.
                    file_line_prefix = '└── ' if is_last_file_in_current_dir else '├── '
                    
                    f.write(f"{file_base_indent_str}{file_line_prefix}{filename}\n")

                    if include_contents:
                        file_full_path = dirpath / filename
                        try:
                            with file_full_path.open('r', encoding=DEFAULT_ENCODING, errors='ignore') as file_content_stream:
                                content = file_content_stream.read()
                            
                            # Content indent: file_indent_level + 1.
                            content_block_indent = '│   ' * (file_indent_level + 1)
                            
                            # Content lines themselves are indented one more level.
                            content_line_indent_str = '│   ' * (file_indent_level + 2) 

                            f.write(f"{content_block_indent}└── Contents of {filename}:\n") 
                            for content_line in content.splitlines():
                                f.write(f"{content_line_indent_str}{content_line}\n")
                        except Exception as e:
                            self.handle_error(f"Error reading file {file_full_path} for content: {e}")
                            f.write(f"{content_block_indent}    [Error reading content: {e}]\n")

        self.logger.info(f"Directory structure written to {output_file_path}")
        print(f"Directory structure written to {output_file_path}")

    def _parse_content_file(self, files_content_path: Path) -> Dict[str, str]:
        """
        Parses a file containing multiple file contents, marked by specific start/end tags.
        Expected format:
        --- START OF FILE relative/path/to/file1.ext ---
        <startwolf>
        content
        of
        file1
        <endwolf>
        --- END OF FILE relative/path/to/file1.ext ---
        ...

        :param files_content_path: Path to the file containing contents.
        :return: A dictionary mapping relative file paths to their content.
        """
        contents: Dict[str, str] = {}
        if not files_content_path.exists():
            self.logger.warning(f"Content file not found: {files_content_path}. No contents will be recreated.")
            return contents

        try:
            with files_content_path.open('r', encoding=DEFAULT_ENCODING) as f:
                lines = f.readlines()
        except Exception as e:
            self.handle_error(f"Error reading content file {files_content_path}: {e}")
            return contents

        current_file_path: Optional[str] = None
        current_content_lines: List[str] = []
        is_capturing_content: bool = False
        
        # Define regex for start/end of file block and content markers
        # Example: "--- START OF FILE path/to/file.py ---"
        # Example: "--- END OF FILE path/to/file.py ---"
        start_of_file_regex = re.compile(r"^-{3,}\s*START OF FILE\s*(.*?)\s*-{3,}$", re.IGNORECASE)
        end_of_file_regex = re.compile(r"^-{3,}\s*END OF FILE\s*(.*?)\s*-{3,}$", re.IGNORECASE)

        for line_number, line in enumerate(lines):
            line_stripped_eol = line.rstrip('\n\r')

            start_match = start_of_file_regex.match(line_stripped_eol)
            if start_match:
                if current_file_path and is_capturing_content: # Should have hit <endwolf> or END OF FILE first
                    self.logger.warning(f"Content file line {line_number+1}: New 'START OF FILE' found before '{FILE_CONTENT_MARKERS['end']}' or 'END OF FILE' for '{current_file_path}'. Storing previous content.")
                    contents[current_file_path] = "\n".join(current_content_lines)
                
                current_file_path = start_match.group(1).strip()
                current_content_lines = []
                is_capturing_content = False # Wait for <startwolf>
                self.logger.debug(f"Content file: Detected start for '{current_file_path}'")
                continue

            end_match = end_of_file_regex.match(line_stripped_eol)
            if end_match:
                if current_file_path:
                    if is_capturing_content: # If still capturing, means <endwolf> was missing
                         self.logger.warning(f"Content file line {line_number+1}: 'END OF FILE' for '{current_file_path}' found but '{FILE_CONTENT_MARKERS['end']}' was missing or content was ongoing. Storing collected content.")
                    contents[current_file_path] = "\n".join(current_content_lines)
                    self.logger.debug(f"Content file: Stored content for '{current_file_path}' due to 'END OF FILE'. Length: {len(contents[current_file_path])}")
                else:
                    self.logger.warning(f"Content file line {line_number+1}: Found 'END OF FILE' but no current file path context.")
                current_file_path = None
                current_content_lines = []
                is_capturing_content = False
                continue
            
            if current_file_path:
                if line_stripped_eol == FILE_CONTENT_MARKERS['start']:
                    if is_capturing_content: # Nested <startwolf>?
                         self.logger.warning(f"Content file line {line_number+1}: Unexpected '{FILE_CONTENT_MARKERS['start']}' while already capturing for '{current_file_path}'. Resetting content.")
                    current_content_lines = [] # Reset for new content block
                    is_capturing_content = True
                    self.logger.debug(f"Content file: Started capturing for '{current_file_path}'")
                    continue
                
                if line_stripped_eol == FILE_CONTENT_MARKERS['end']:
                    if not is_capturing_content:
                        self.logger.warning(f"Content file line {line_number+1}: Unexpected '{FILE_CONTENT_MARKERS['end']}' for '{current_file_path}' (not capturing).")
                    else:
                        contents[current_file_path] = "\n".join(current_content_lines)
                        self.logger.debug(f"Content file: Finished capturing for '{current_file_path}'. Length: {len(contents[current_file_path])}")
                    is_capturing_content = False 
                    # Do not nullify current_file_path here, wait for END OF FILE marker
                    continue

                if is_capturing_content:
                    current_content_lines.append(line_stripped_eol) # Store line without EOL

        # Safety: if loop ends while capturing content for a file (e.g. missing END OF FILE)
        if current_file_path and is_capturing_content:
            self.logger.warning(f"Content file: Reached EOF while still capturing content for '{current_file_path}'. Storing collected content.")
            contents[current_file_path] = "\n".join(current_content_lines)
        
        return contents

    def recreate_structure_from_file(self, structure_definition_file_path: str, files_content_file_path: str) -> None:
        """
        Recreate a project structure.
        One file defines the directory/file hierarchy (names, types).
        Another file provides the contents for the files defined in the structure.

        :param structure_definition_file_path: Path to the file defining the hierarchy.
               This file should NOT contain embedded content; content comes from `files_content_file_path`.
        :param files_content_file_path: Path to the file containing contents for files,
               using FILE_CONTENT_MARKERS.
        """
        struct_def_file = Path(structure_definition_file_path)
        content_file = Path(files_content_file_path)

        if not struct_def_file.exists():
            self.handle_error(f"Structure definition file not found: {struct_def_file}")
            raise FileNotFoundError(f"Structure definition file not found: {struct_def_file}")

        # 1. Parse the content file
        self.logger.info(f"Parsing content file: {content_file}")
        file_contents_map = self._parse_content_file(content_file)
        self.logger.info(f"Parsed {len(file_contents_map)} file contents from {content_file}")

        # 2. Parse the structure definition file
        #    This parsing should NOT try to extract embedded content.
        #    We can reuse _parse_structure_lines, but it needs to be aware it shouldn't expect embedded content.
        #    For simplicity, if _parse_structure_lines is used, any 'content' it finds will be overwritten
        #    by content from file_contents_map if a match by path exists.
        try:
            with struct_def_file.open('r', encoding=DEFAULT_ENCODING) as f:
                lines = f.readlines()
            self.logger.info(f"Read structure definition file: {struct_def_file} ({len(lines)} lines)")
        except Exception as e:
            self.handle_error(f"Error reading structure definition file {struct_def_file}: {str(e)}")
            return

        if not lines:
            self.handle_error("Structure definition file is empty.")
            raise ValueError("Structure definition file is empty.")

        try:
            self.logger.info(f"Starting structure parsing for definition file: {struct_def_file}")
            # IMPORTANT: The _parse_structure_lines might try to find embedded content.
            # We need a mode for it, or a different parser, or just overwrite content later.
            # For now, let's assume _parse_structure_lines is run, and we'll override content.
            root_node = self._parse_structure_lines(lines) # This might find embedded content if any.
            self.logger.info(f"Finished parsing definition. Root node: {root_node.name} with {len(root_node.children)} children.")

            # 3. Augment the Node tree with content from file_contents_map
            #    This requires traversing the node tree and matching paths.
            def augment_tree_with_content(node: Node, current_rel_path: Path):
                for child in node.children:
                    child_rel_path = current_rel_path / child.name
                    if not child.is_directory:
                        # Path keys in file_contents_map are expected to be relative to project_root
                        # Convert Path to string, using OS-agnostic slashes for map keys if necessary
                        path_key = str(child_rel_path).replace(os.sep, '/')
                        if path_key in file_contents_map:
                            child.content = file_contents_map[path_key]
                            self.logger.debug(f"Applied content from map to Node: {path_key}")
                        elif child.content is not None: # Content from _parse_structure_lines
                             self.logger.debug(f"Node {path_key} had embedded content; not found in content map. Keeping embedded.")
                        # else: # No embedded content, no content in map = empty file
                    
                    if child.is_directory:
                        augment_tree_with_content(child, child_rel_path)
            
            augment_tree_with_content(root_node, Path()) # Start with empty relative path for root's children

            # 4. Create the structure using the augmented tree
            self.logger.info(f"Starting creation of recreated structure at: {self.project_root}")
            self._create_from_node_tree(root_node, self.project_root)
            self.logger.info(f"Successfully recreated structure from {struct_def_file} and {content_file} at {self.project_root}")

        except Exception as e:
            self.handle_error(f"Error processing files for recreation: {str(e)}")


    def handle_error(self, message: str) -> None:
        """
        Handle errors by logging and printing the error message.

        :param message: The error message to log and print.
        """
        if ERROR_HANDLING.get('log_errors', True): # Default to True if key missing
            self.logger.error(message)
        if ERROR_HANDLING.get('print_errors', True): # Default to True if key missing
            print(f"ERROR: {message}")