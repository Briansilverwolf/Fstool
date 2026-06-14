import argparse
import logging
from pathlib import Path

from src import (
    create_structure_from_file,
    output_directory_structure,
    recreate_structure_from_file,
)

from src.settings import DEFAULT_ENCODING, LOGGING


# =========================================================
# LOGGING (UNCHANGED BUT CLEANED)
# =========================================================

DEFAULT_LOG_DIR = Path.home() / ".filesystemtool" / "logs"
DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "filesystemtool_cli.log"


def get_logger(level_str="INFO", log_file=DEFAULT_LOG_FILE):
    level = getattr(logging, level_str.upper(), logging.INFO)

    logger = logging.getLogger("FileSystemToolCLI")
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(LOGGING["formatters"]["default"]["format"])

        file_handler = logging.FileHandler(log_file, encoding=DEFAULT_ENCODING)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# =========================================================
# STRICT COMMAND DISPATCH (NO LOGIC HERE)
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description="Filesystem Tool - deterministic filesystem engine"
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    parser.add_argument(
        "--log-file",
        default=str(DEFAULT_LOG_FILE),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -----------------------------------------------------
    # blueprint (was create)
    # -----------------------------------------------------
    p_blueprint = subparsers.add_parser(
        "blueprint",
        help="Create project structure from blueprint file"
    )
    p_blueprint.add_argument("structure_file")
    p_blueprint.add_argument("--root", default=Path.cwd())

    # -----------------------------------------------------
    # snapshoot (was output)
    # -----------------------------------------------------
    p_snap = subparsers.add_parser(
        "snapshoot",
        help="Export directory structure snapshot"
    )
    p_snap.add_argument("root_directory")
    p_snap.add_argument("-o", "--out-file")
    p_snap.add_argument("-c", "--include-contents", action="store_true")

    # -----------------------------------------------------
    # recreate
    # -----------------------------------------------------
    p_recreate = subparsers.add_parser(
        "recreate",
        help="Rebuild project from structure + content files"
    )
    p_recreate.add_argument("structure_definition_file")
    p_recreate.add_argument("files_content_file")
    p_recreate.add_argument("--root", default=Path.cwd())



    args = parser.parse_args()

    logger = get_logger(args.log_level, args.log_file)

    logger.info(f"Command: {args.command}")
    logger.debug(f"Args: {vars(args)}")

    # =====================================================
    # COMMAND ROUTER (PURE DELEGATION ONLY)
    # =====================================================

    try:

        # -------------------------
        # BLUEPRINT
        # -------------------------
        if args.command == "blueprint":
            create_structure_from_file(
                args.structure_file,
                args.root,
                logger_instance=logger
            )

        # -------------------------
        # SNAPSHOT (NO PATH FIXES)
        # -------------------------
        elif args.command == "snapshoot":
            output_directory_structure(
                args.root_directory,
                args.out_file,
                args.include_contents,
                logger_instance=logger
            )

        # -------------------------
        # RECREATE
        # -------------------------
        elif args.command == "recreate":
            recreate_structure_from_file(
                args.structure_definition_file,
                args.files_content_file,
                args.root,
                logger_instance=logger
            )

        # -------------------------
        # INSTALL (delegated)
        # -------------------------
        elif args.command == "install":
            # intentionally not implemented here
            # should be moved to engine/service layer
            raise NotImplementedError(
                "Install should be handled in engine layer (not CLI)"
            )

        logger.info(f"Completed: {args.command}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"ERROR: {e}")

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        print(f"ERROR: {e}")

    except Exception as e:
        logger.exception("Unhandled CLI error")
        print(f"ERROR: unexpected error (check logs at {args.log_file})")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()