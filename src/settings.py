import os
from pathlib import Path

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'file_system_tool.log'),
            'encoding': 'utf-8',
            'formatter': 'default',
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'loggers': {
        'MyLogger': {  # Add this logger configuration
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'FileSystemTool': {  # Example of another logger
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
# List of file extensions to ignore
IGNORED_FILE_EXTENSIONS = [
    '.pyc', '.log', '.tmp', '.lnk', '.inf', '.jpg', '.zip', '.webp', '.jpeg', '.bat','.png','.drawio',
    '.sqlite3', '.gitignore', 'package-lock.json', 'package.json', '.dockerignore',
    '404.html','500.html','css.css','js.js','Dockerfile','manage.py',
]

# List of directory names to ignore
IGNORED_DIRECTORIES = [
    'interface','node_modules', '__pycache__', '.git','Dockerfile', '.vscode', 'venv', 'migrations', 'staticfiles','search','theme','media','ffmpeg-7.1-essentials_build',
]
IGNORED_PATH=[]

# List of packages to ignore during installation
IGNORED_PACKAGES = [
    'package1', 'package2',
]

# Default output file for directory structure
DEFAULT_OUTPUT_FILE = os.path.join(BASE_DIR, 'directory_structure.txt')

# Default structure file for creating directories
DEFAULT_STRUCTURE_FILE = os.path.join(BASE_DIR, 'structure', 'directory_structure.txt')

# Default file for recreating file contents
DEFAULT_CONTENTS_FILE = os.path.join(BASE_DIR, 'structure', 'file_contents_output.txt')

# Package manager settings
PACKAGE_MANAGERS = {
    'pip': {
        'command': 'pip',
        'install_command': 'install',
    },
    'npm': {
        'command': 'npm',
        'install_command': 'install',
    },
}

# Maximum length for file/directory names (Windows has a limit of 255 characters)
MAX_NAME_LENGTH = 255

# Default encoding for file operations
DEFAULT_ENCODING = 'utf-8'

# Default root directory for project operations
DEFAULT_ROOT_DIRECTORY = os.path.join(BASE_DIR, 'project_root')

# Settings for file content parsing
FILE_CONTENT_MARKERS = {
    'start': '<startwolf>',
    'end': '<endwolf>',
}

# Settings for directory structure parsing
DIRECTORY_STRUCTURE_INDICATORS = {
    'directory': '/',
    'file': '.',
}

# List of allowed characters in file/directory names
ALLOWED_CHARACTERS = r'[a-zA-Z0-9_\-\.]'

# List of characters to replace in file/directory names
REPLACE_CHARACTERS = r'[\\/:*?"<>|#]'

# Default replacement character for invalid characters in file/directory names
REPLACEMENT_CHARACTER = '_'

# Settings for error handling
ERROR_HANDLING = {
    'log_errors': True,
    'print_errors': True,
}

# Settings for testing
TEST_SETTINGS = {
    'test_root_directory': os.path.join(BASE_DIR, 'tests', 'test_root'),
    'test_structure_file': os.path.join(BASE_DIR, 'tests', 'test_structure.txt'),
    'test_contents_file': os.path.join(BASE_DIR, 'tests', 'test_contents.txt'),
}