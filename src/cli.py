# filesystemtool/src/cli.py
import argparse
import os
import logging # For configuring logging from CLI
from pathlib import Path

# Relative imports for package structure
from .. import (
    create_structure_from_file,
    output_directory_structure,
    recreate_structure_from_file,
    install_package,
    setup_logger # To set up logger based on CLI args
)
from .settings import DEFAULT_ENCODING, LOGGING # For default log path

# Determine a good default log file path
# For a CLI tool, placing logs in a user-specific config/data directory is good practice
# or allowing it to be configured.
DEFAULT_LOG_DIR = Path.home() / ".filesystemtool" / "logs"
DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "filesystemtool_cli.log"


def get_logger(log_level_str="INFO", log_file_path=DEFAULT_LOG_FILE):
    """Helper to get a configured logger for CLI operations."""
    level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Use the setup_logger from your logger.py, adapting its parameters if needed
    # For simplicity here, directly configuring. Your setup_logger might be more complex.
    cli_logger = logging.getLogger("FileSystemToolCLI")
    cli_logger.setLevel(level)
    
    # Prevent adding multiple handlers if called multiple times (e.g. in tests)
    if not cli_logger.handlers:
        # File Handler
        fh = logging.FileHandler(log_file_path, encoding=DEFAULT_ENCODING)
        fh.setLevel(level)
        formatter = logging.Formatter(LOGGING['formatters']['default']['format']) # Use your format
        fh.setFormatter(formatter)
        cli_logger.addHandler(fh)

        # Console Handler (optional, for verbose output)
        ch = logging.StreamHandler()
        ch.setLevel(level) # Or a different level for console, e.g., WARNING
        ch.setFormatter(formatter)
        cli_logger.addHandler(ch)
        
    return cli_logger


def main():
    parser = argparse.ArgumentParser(description="File System Tool: Manage project structures and packages.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the logging level.")
    parser.add_argument("--log-file", default=str(DEFAULT_LOG_FILE), help=f"Set the path for the log file (default: {DEFAULT_LOG_FILE}).")
    
    subparsers = parser.add_subparsers(dest="command", title="Commands", required=True)

    # --- Create command ---
    create_parser = subparsers.add_parser("create", help="Create project structure from a file.")
    create_parser.add_argument("structure_file", help="Path to the structure definition file.")
    create_parser.add_argument("--root", default=os.getcwd(), help="Project root directory where structure will be created (default: current dir).")

    # --- Output command ---
    output_parser = subparsers.add_parser("output", help="Output directory structure to a file.")
    output_parser.add_argument("root_directory", help="Root directory to scan.")
    output_parser.add_argument("--out-file", "-o", help="Output file path for the structure text (default: directory_structure_TIMESTAMP.txt).")
    output_parser.add_argument("--include-contents", "-c", action="store_true", help="Include file contents in the output.")

    # --- Recreate command ---
    recreate_parser = subparsers.add_parser("recreate", help="Recreate project structure from definition and content files.")
    recreate_parser.add_argument("structure_definition_file", help="Path to the structure hierarchy definition file.")
    recreate_parser.add_argument("files_content_file", help="Path to the file containing contents for files.")
    recreate_parser.add_argument("--root", default=os.getcwd(), help="Project root directory where structure will be recreated (default: current dir).")

    # --- Install command ---
    install_parser = subparsers.add_parser("install", help="Install a package.")
    install_parser.add_argument("package_name", help="Name of the package to install.")
    install_parser.add_argument("manager_type", choices=["pip", "npm"], help="Package manager type (pip or npm).")

    args = parser.parse_args()
    
    # Setup logger based on global args
    logger = get_logger(args.log_level, args.log_file)
    logger.info(f"CLI command: {args.command} with args: {vars(args)}")


    try:
        if args.command == "create":
            create_structure_from_file(args.structure_file, args.root, logger_instance=logger)
            logger.info(f"Structure creation command finished for {args.structure_file}.")
        elif args.command == "recreate":
            recreate_structure_from_file(args.root, args.structure_definition_file, args.files_content_file, logger_instance=logger)
            logger.info(f"Structure recreation command finished for {args.structure_definition_file}.")
        elif args.command == "install":
            install_package(args.package_name, args.manager_type, logger_instance=logger)
            logger.info(f"Package install command finished for {args.package_name} ({args.manager_type}).")
        elif args.command == "output":
            root_dir_arg = args.root_directory
            # A potential (but perhaps overly magical) fix:
            if root_dir_arg.startswith('.') and not root_dir_arg.startswith(('./', '.\\')) and len(root_dir_arg) > 1:
                # If it's like ".D:\path" and not "./relpath" or "..\relpath"
                # This is heuristic and might have edge cases.
                possible_absolute_path = root_dir_arg[1:]
                if Path(possible_absolute_path).is_absolute() and Path(possible_absolute_path).exists():
                    logger.warning(f"Interpreting '{root_dir_arg}' as absolute path '{possible_absolute_path}' due to leading '.' before an absolute path.")
                    root_dir_arg = possible_absolute_path
                # Or, if it's meant to be relative to CWD but just missing a separator
                elif Path(os.getcwd(), root_dir_arg).exists():
                    logger.warning(f"Interpreting '{root_dir_arg}' as path relative to current directory: '{Path(os.getcwd(), root_dir_arg)}'")
                    root_dir_arg = Path(os.getcwd(), root_dir_arg)


            output_directory_structure(root_dir_arg, args.out_file, args.include_contents, logger_instance=logger)
            logger.info(f"Directory output command finished for {root_dir_arg}.")
  

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"ERROR: File not found - {e}")
    except ValueError as e:
        logger.error(f"Invalid value or configuration: {e}")
        print(f"ERROR: Invalid value - {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred during command {args.command}:") # .exception includes stack trace
        print(f"ERROR: An unexpected error occurred. Check logs at {args.log_file} for details.")


if __name__ == "__main__": # This allows running cli.py directly for testing
    main()