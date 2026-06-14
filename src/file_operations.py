import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from .node import Node
from .settings import (
    IGNORED_FILE_EXTENSIONS,
    IGNORED_DIRECTORIES,
    DEFAULT_ENCODING,
    MAX_NAME_LENGTH,
    REPLACE_CHARACTERS,
    REPLACEMENT_CHARACTER,
    ERROR_HANDLING,
    FILE_CONTENT_MARKERS,
    DIRECTORY_STRUCTURE_INDICATORS,
)


# =========================================================
# PATH RESOLUTION (NO AMBIGUITY CORE RULE)
# =========================================================

class PathResolver:
    """
    Single source of truth for path interpretation.
    NO heuristics. NO guessing.
    """

    @staticmethod
    def resolve(raw_path: str, base: Optional[Path] = None) -> Path:
        p = Path(raw_path).expanduser()

        if p.is_absolute():
            return p

        base = base or Path.cwd()
        return (base / p).resolve()


# =========================================================
# FILE OPERATIONS ENGINE
# =========================================================

class FileOperations:
    """
    Deterministic filesystem engine:
    - No path guessing
    - No silent corrections
    - Strict parsing rules
    """

    def __init__(self, project_root: str, logger: logging.Logger):
        self.project_root: Path = PathResolver.resolve(project_root)
        self.logger = logger

        self.ignored_extensions = IGNORED_FILE_EXTENSIONS
        self.ignored_directories = IGNORED_DIRECTORIES

    # =====================================================
    # SAFE FILE SYSTEM PRIMITIVES
    # =====================================================

    def create_directory(self, dir_path: Path) -> None:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {dir_path}")
        except Exception as e:
            self.handle_error(f"Directory creation failed: {dir_path} -> {e}")

    def create_file(self, file_path: Path, content: str = "") -> None:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding=DEFAULT_ENCODING)
            self.logger.info(f"Created file: {file_path}")
        except Exception as e:
            self.handle_error(f"File creation failed: {file_path} -> {e}")

    # =====================================================
    # NAME SANITIZATION (DETERMINISTIC ONLY)
    # =====================================================

    def sanitize_name(self, name: str) -> str:
        sanitized = re.sub(REPLACE_CHARACTERS, REPLACEMENT_CHARACTER, name)
        sanitized = re.sub(r'[(){}\[\]]', REPLACEMENT_CHARACTER, sanitized)
        sanitized = re.sub(r'\s+', REPLACEMENT_CHARACTER, sanitized)

        sanitized = sanitized.strip(REPLACEMENT_CHARACTER)

        if not sanitized:
            return "untitled"

        if len(sanitized) > MAX_NAME_LENGTH:
            base, ext = os.path.splitext(sanitized)
            allowed = MAX_NAME_LENGTH - len(ext)
            sanitized = base[:allowed] + ext

        return sanitized

    # =====================================================
    # STRUCTURE PARSING (NO SIDE EFFECTS)
    # =====================================================

    def _parse_structure_lines(self, lines: List[str]) -> Node:
        root = Node("root", is_directory=True)
        stack: List[Tuple[int, Node]] = [(-1, root)]

        current_file = None
        current_content = []
        base_indent = -1

        for line in lines:
            raw = line.rstrip("\n\r")
            stripped = re.sub(r'^[│├└─\s]*', '', raw)

            if not stripped.strip():
                continue

            indent = len(raw) - len(raw.replace(' ',""))
         
            name = raw.lstrip(' ').lstrip('│├└─ ').rstrip('/')

            # -----------------------------
            # CONTENT MODE
            # -----------------------------
            if current_file:
                if indent > base_indent:
                    current_content.append(raw)
                    continue
                else:
                    current_file.content = "\n".join(current_content)
                    current_file = None
                    current_content = []
                    base_indent = -1

            # -----------------------------
            # NODE TYPE
            # -----------------------------
            is_dir = raw.endswith(DIRECTORY_STRUCTURE_INDICATORS['directory'])

            

            if is_dir:
                node = Node(name, is_directory=True)
            else:
                node = Node(name, is_directory=False)
            

            # stack unwind
            while stack and indent <= stack[-1][0]:
                stack.pop()

            parent = stack[-1][1]
            parent.add_child(node)

            if is_dir:
                stack.append((indent, node))
                
            else:
                current_file = node
                base_indent = indent

        # flush last file
        if current_file and current_content:
            current_file.content = "\n".join(current_content)

        return root

    # =====================================================
    # TREE CREATION (SIDE EFFECT LAYER)
    # =====================================================

    def _create_from_node_tree(self, node: Node, base: Path) -> None:
        
        for child in node.children:
            target = base / child.name

            if child.is_directory:
                self.create_directory(target)
                self._create_from_node_tree(child, target)
            else:
                self.create_file(target, child.content or "")

    # =====================================================
    # PUBLIC API: CREATE STRUCTURE
    # =====================================================

    def create_structure_from_file(self, structure_file_path: str) -> None:
       
        path = PathResolver.resolve(structure_file_path)

        if not path.exists():
            raise FileNotFoundError(f"Structure file not found: {path}")

        lines = path.read_text(encoding=DEFAULT_ENCODING).splitlines()

        root = self._parse_structure_lines(lines)
        self._create_from_node_tree(root, self.project_root)

    # =====================================================
    # OUTPUT STRUCTURE (READ ONLY)
    # =====================================================

    def output_directory_structure(
        self,
        root_dir_to_scan: str,
        output_file_path: Optional[str] = None,
        include_contents: bool = False
    ) -> None:

        root = PathResolver.resolve(root_dir_to_scan)

        if not root.is_dir():
            raise ValueError(f"Invalid directory: {root}")

        if output_file_path:
            out = PathResolver.resolve(output_file_path)
        else:
            out = Path.cwd() / f"structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with out.open("w", encoding=DEFAULT_ENCODING) as f:

            for dirpath, dirnames, filenames in os.walk(root):

                dirpath = Path(dirpath)

                dirnames[:] = [
                    d for d in dirnames
                    if d not in self.ignored_directories
                ]

                rel = dirpath.relative_to(root)
                level = len(rel.parts)

                indent = "│   " * level

                f.write(f"{indent}{dirpath.name}/\n")

                for file in filenames:
                    if any(file.endswith(ext) for ext in self.ignored_extensions):
                        continue

                    f.write(f"{indent}├── {file}\n")

                    if include_contents:
                        try:
                            content = (dirpath / file).read_text(
                                encoding=DEFAULT_ENCODING,
                                errors="ignore"
                            )
                            for line in content.splitlines():
                                f.write(f"{indent}│   {line}\n")
                        except Exception as e:
                            self.handle_error(str(e))

    # =====================================================
    # ERROR HANDLING (SINGLE GATEWAY)
    # =====================================================

    def handle_error(self, message: str) -> None:
        if ERROR_HANDLING.get("log_errors"):
            self.logger.error(message)

        if ERROR_HANDLING.get("print_errors"):
            print(f"ERROR: {message}")