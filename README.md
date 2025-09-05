# FileSystemTool (fstool)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A versatile Python tool for scaffolding, documenting, and recreating project structures. `FileSystemTool` simplifies project setup by generating directories and files from a simple text definition. It can also reverse the process, scanning an existing project into a structured text file, optionally including all file contents.

Beyond project scaffolding, it includes a powerful **CI/CD Impact Analyzer** to intelligently determine which tests and build jobs need to run based on code changes, saving valuable CI minutes.

## Table of Contents

-   [Features](#features)
-   [Installation](#installation)
-   [Usage](#usage)
    -   [As a Command-Line Tool (CLI)](#as-a-command-line-tool-cli)
    -   [As a Python Library](#as-a-python-library)
-   [Advanced Feature: CI/CD Impact Analysis](#advanced-feature-cicd-impact-analysis)
-   [Structure File Format](#structure-file-format)
    -   [Basic Structure](#basic-structure)
    -   [Structure with Embedded Content](#structure-with-embedded-content)
-   [Configuration](#configuration)
-   [Contributing](#contributing)
-   [License](#license)

## Features

-   **Project Scaffolding**: Create entire project directory structures and files from a single, human-readable text file.
-   **Structure Exporting**: Scan an existing directory and generate a tree-like text file representing its structure.
-   **Content Preservation**: Optionally embed file contents directly into the structure file for complete, portable project blueprints.
-   **Project Recreation**: Rebuild a project from a structure file and a separate contents file, ensuring a clean and reproducible setup.
-   **Package Management**: A simple wrapper to install `pip` and `npm` packages programmatically.
-   **CI/CD Optimization**: Analyze git commit history and code dependencies to suggest the minimal set of CI jobs that need to run.
-   **Customizable**: Configure ignored file types, directories, and other settings in a central `settings.py` file.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/filesystemtool.git
    cd filesystemtool
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    This project requires `PyYAML` for the CI/CD analyzer. Create a `requirements.txt` file with the following content:
    ```
    PyYAML
    ```
    Then, install it:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

`FileSystemTool` can be used both as a command-line tool for quick operations and as a Python library for integration into other scripts.

### As a Command-Line Tool (CLI)

The CLI is the primary way to interact with the tool. Use the `cli.py` script as the entry point.

```bash
# General command structure
python -m filesystemtool.src.cli <command> [options]
```

#### `output` - Scan a directory and create a structure file

This command scans a directory and prints its structure to a file or the console.

**Example:** Scan the current directory, include file contents, and save to `project_blueprint.txt`.
```bash
python -m filesystemtool.src.cli output . --include-contents -o project_blueprint.txt
```
*   `output`: The command to run.
*   `.`: The root directory to scan.
*   `--include-contents` or `-c`: Flag to embed file contents in the output.
*   `--out-file` or `-o`: The path to the output file.

#### `create` - Create a project from a structure file

This command reads a structure file (which can contain embedded content) and builds the corresponding directories and files.

**Example:** Create a project in the `./new-project-dir` folder from the blueprint file.
```bash
python -m filesystemtool.src.cli create project_blueprint.txt --root ./new-project-dir
```
*   `create`: The command to run.
*   `project_blueprint.txt`: The input file defining the structure.
*   `--root`: The directory where the project will be created (defaults to the current directory).

#### `recreate` - Recreate a project from separate structure and content files

This is useful when the `output` command was run without `--include-contents`, producing two separate files.

**Example:**
```bash
# First, generate the structure and content files
python -m filesystemtool.src.cli output . -o structure.txt
# (Assuming a separate mechanism generates a file_contents.txt)

# Then, recreate the project
python -m filesystemtool.src.cli recreate structure.txt file_contents.txt --root ./recreated-app
```
*   `recreate`: The command to run.
*   `structure.txt`: The file defining the directory hierarchy.
*   `file_contents.txt`: The file containing the content of all files.
*   `--root`: The target directory for recreation.

#### `install` - Install a package

A simple helper to install packages.

**Example:** Install the `requests` library using `pip`.
```bash
python -m filesystemtool.src.cli install requests pip
```

### As a Python Library

You can also import and use the core functions in your own Python scripts.

**Example:**
```python
import filesystemtool
import os

# Define a project root
project_dir = "./my-library"
os.makedirs(project_dir, exist_ok=True)

# 1. Output the structure of an existing directory
filesystemtool.output_directory_structure(
    root_directory=".", 
    output_file=os.path.join(project_dir, "structure_output.txt"),
    include_contents=True
)
print(f"Project structure saved to {project_dir}/structure_output.txt")

# 2. Create a new structure from a definition file
structure_definition_path = "path/to/your/structure.txt"
filesystemtool.create_structure_from_file(
    structure_file=structure_definition_path,
    project_root=project_dir
)
print(f"Project created at {project_dir}")

# 3. Install a package
filesystemtool.install_package("express", "npm")
```

## Advanced Feature: CI/CD Impact Analysis

This powerful feature helps optimize your CI/CD pipelines by identifying the precise tests impacted by a code change. Instead of running your entire test suite on every commit, you can run only what's necessary.

**How it works:**
1.  It uses `git` to find which files have changed in a given commit range.
2.  It parses all Python files in your project to build a dependency graph (i.e., which modules import which other modules).
3.  It maps test files to the source code modules they import.
4.  Given the changed files, it traverses the dependency graph to find all impacted modules and, subsequently, all relevant tests that should be run.
5.  It also parses your `.github/workflows` files to suggest which CI job names (e.g., jobs containing "test") should be triggered.

**Example Usage:**

```python
from pathlib import Path
from filesystemtool.src.ci_cd_analyzer import CICDAnalyzer

# 1. Point the analyzer to your project root
project_root = Path(__file__).parent.resolve()
analyzer = CICDAnalyzer(project_root=str(project_root))

# 2. Get files changed in the last commit
changed_files = analyzer.get_changed_files('HEAD~1..HEAD')
print("Changed files:", changed_files)

# 3. Find which test files are impacted by these changes
impacted_tests = analyzer.get_impacted_tests(changed_files)
print("Impacted tests to run:", impacted_tests)

# 4. Get suggestions for which CI jobs to run
job_suggestions = analyzer.suggest_jobs_to_run(changed_files)
print("Suggested CI jobs:", job_suggestions)
```

## Structure File Format

The structure file uses indentation to define the hierarchy.

### Basic Structure

Directories are denoted with a trailing slash (`/`). Files are listed by their name.

```
my-project/
│   ├── .gitignore
│   ├── README.md
│   └── src/
│       ├── __init__.py
│       └── main.py
└── tests/
    └── test_main.py
```

### Structure with Embedded Content

To include a file's content, add it on subsequent lines with greater indentation. The tool will automatically detect and associate the content block with the preceding file.

```
my-project/
│   ├── .gitignore
│   │   └── Contents of .gitignore:
│   │   │   __pycache__/
│   │   │   venv/
│   │   │   *.pyc
│   ├── README.md
│   │   └── Contents of README.md:
│   │   │   # My Project
│   │   │   
│   │   │   This is a sample project.
│   └── src/
│       ├── __init__.py
│       └── main.py
│           └── Contents of main.py:
│           │   def hello():
│           │       print("Hello, World!")
│           │   
│           │   if __name__ == "__main__":
│           │       hello()
```

## Configuration

You can customize the tool's behavior by modifying `filesystemtool/src/settings.py`. This file allows you to define:
-   `IGNORED_FILE_EXTENSIONS`: File types to skip during scanning and creation.
-   `IGNORED_DIRECTORIES`: Directory names (like `__pycache__` or `.git`) to ignore.
-   `LOGGING`: Configuration for logging behavior.
-   And other operational constants.

## Contributing

Contributions are welcome! If you have suggestions for improvements or find a bug, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
