#!/usr/bin/env python3
"""
Main entry point for the Trading Card Generator.

This script orchestrates the entire card generation process, providing
a command-line interface for generating printable A5 trading cards from
Brainrot character data and images.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

# Add the project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from card_generator.cli import main as cli_main
from card_generator import __version__


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        verbose: Enable debug-level logging
        quiet: Suppress most logging output
    """
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def check_environment() -> bool:
    """
    Check if the environment is properly set up for card generation.
    
    Returns:
        True if environment is ready, False otherwise
    """
    issues = []
    
    # Get current working directory for relative paths
    current_dir = Path.cwd()
    
    # Check for required data file
    csv_file = current_dir / 'steal_a_brainrot_complete_database.csv'
    if not csv_file.exists():
        issues.append(f"Missing character data file: {csv_file}")
    
    # Check for images directory
    images_dir = current_dir / 'images'
    if not images_dir.exists():
        issues.append(f"Missing images directory: {images_dir}")
    elif not any(images_dir.iterdir()):
        issues.append(f"Images directory is empty: {images_dir}")
    
    # Check write permissions for output directory
    output_dir = current_dir / 'output'
    try:
        output_dir.mkdir(exist_ok=True)
        test_file = output_dir / '.write_test'
        test_file.write_text('test')
        test_file.unlink()
    except Exception as e:
        issues.append(f"Cannot write to output directory: {e}")
    
    if issues:
        print("Environment check failed:")
        for issue in issues:
            print(f"  ✗ {issue}")
        print("\nPlease resolve these issues before running the card generator.")
        return False
    
    return True


def show_welcome_message() -> None:
    """Show welcome message and basic information."""
    print(f"Trading Card Generator v{__version__}")
    print("=" * 50)
    print("Generate printable A5 trading cards from Brainrot character data")
    print()


def show_quick_help() -> None:
    """Show quick help for common usage patterns."""
    print("Quick start examples:")
    print("  python main.py --all                    # Generate cards for all characters")
    print("  python main.py --names \"Tim Cheese\"     # Generate card for specific character")
    print("  python main.py --tiers Common Rare      # Generate cards for specific tiers")
    print("  python main.py --build-database         # Build database from wiki")
    print("  python main.py --list-characters        # List all available characters")
    print("  python main.py --help                   # Show full help")
    print()


def main() -> int:
    """
    Main entry point for the Trading Card Generator application.
    
    This function orchestrates the entire card generation workflow:
    1. Environment validation
    2. Command-line argument processing
    3. Component initialization and integration
    4. Progress reporting and error handling
    5. Results summary and cleanup
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Show welcome message for interactive usage
        if len(sys.argv) == 1:
            show_welcome_message()
            show_quick_help()
            return 0
        
        # Quick help for common help requests
        if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', 'help']:
            show_welcome_message()
        
        # Check environment before proceeding with any operations
        # Skip environment check for database builder and help commands
        skip_env_check = any(arg in sys.argv for arg in ['--help', '-h', '--version', '--build-database'])
        if not skip_env_check:
            if not check_environment():
                return 1
        
        # Delegate to CLI main function
        return cli_main()
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.exception("Unexpected error in main")
        return 1


if __name__ == "__main__":
    sys.exit(main())