#!/usr/bin/env python3
"""
Demo script for the DatabaseBuilder orchestrator class.

This script demonstrates how to use the DatabaseBuilder to coordinate
all components of the database building process.
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from card_generator.database_builder import DatabaseBuilder, DatabaseBuildResult
from card_generator.config import DatabaseBuilderConfig
from card_generator.error_handling import setup_logging


def main():
    """Main demo function."""
    # Set up logging
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Also set up a simple console handler for this demo
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    logger.info("DatabaseBuilder Demo Starting")
    
    try:
        # Create configuration for demo (with faster settings)
        config = DatabaseBuilderConfig(
            output_dir="demo_databases",
            images_dir="demo_images", 
            rate_limit_delay=1.0,  # Faster for demo
            max_retries=2,
            skip_existing_images=True,
            validate_images=True,
            continue_on_error=True
        )
        
        logger.info(f"Configuration created:")
        logger.info(f"  Output directory: {config.output_dir}")
        logger.info(f"  Images directory: {config.images_dir}")
        logger.info(f"  Rate limit delay: {config.rate_limit_delay}s")
        logger.info(f"  Max retries: {config.max_retries}")
        
        # Create DatabaseBuilder instance
        logger.info("Creating DatabaseBuilder instance...")
        builder = DatabaseBuilder(config)
        
        # Test progress info before starting
        progress_info = builder.get_progress_info()
        logger.info(f"Initial progress: {progress_info}")
        
        # Note: We won't actually run the build in this demo since it would
        # make real network requests. Instead, we'll just verify the setup.
        logger.info("DatabaseBuilder setup completed successfully!")
        logger.info("To run the actual build process, call: builder.build_database()")
        
        # Show what the build result would look like
        logger.info("\nExample build result structure:")
        example_result = DatabaseBuildResult()
        example_result.total_characters = 50
        example_result.successful_extractions = 45
        example_result.failed_extractions = 5
        example_result.images_downloaded = 40
        example_result.images_failed = 5
        example_result.processing_time = 120.5
        example_result.csv_file_path = "demo_databases/brainrot_database_20250918_120000.csv"
        
        logger.info(f"  Total characters: {example_result.total_characters}")
        logger.info(f"  Successful extractions: {example_result.successful_extractions}")
        logger.info(f"  Failed extractions: {example_result.failed_extractions}")
        logger.info(f"  Success rate: {example_result.get_success_rate():.1f}%")
        logger.info(f"  Images downloaded: {example_result.images_downloaded}")
        logger.info(f"  Images failed: {example_result.images_failed}")
        logger.info(f"  Image success rate: {example_result.get_image_success_rate():.1f}%")
        logger.info(f"  Processing time: {example_result.processing_time:.1f}s")
        logger.info(f"  CSV file: {example_result.csv_file_path}")
        
        logger.info("\nDatabaseBuilder demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    main()