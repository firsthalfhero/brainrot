"""
Database builder orchestrator for the Steal a Brainrot wiki scraping system.

This module provides the main DatabaseBuilder class that coordinates all components
to scrape character data from the wiki, download images, and generate CSV databases.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field

from .config import DatabaseBuilderConfig
from .wiki_scraper import WikiScraper
from .character_data_extractor import CharacterDataExtractor
from .image_downloader import ImageDownloader
from .csv_generator import CSVGenerator
from .data_models import CharacterData
from .error_handling import ErrorHandler, ErrorCategory, ErrorSeverity


@dataclass
class DatabaseBuildResult:
    """
    Result object containing comprehensive information about a database build operation.
    """
    total_characters: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    csv_file_path: str = ""
    images_downloaded: int = 0
    images_failed: int = 0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tier_statistics: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate as percentage."""
        if self.total_characters == 0:
            return 0.0
        return (self.successful_extractions / self.total_characters) * 100
    
    def get_image_success_rate(self) -> float:
        """Calculate image download success rate as percentage."""
        total_image_attempts = self.images_downloaded + self.images_failed
        if total_image_attempts == 0:
            return 0.0
        return (self.images_downloaded / total_image_attempts) * 100


@dataclass
class ProcessingProgress:
    """
    Progress tracking for database building operations.
    """
    current_tier: str = ""
    current_character: str = ""
    characters_processed: int = 0
    total_characters: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    def get_progress_percentage(self) -> float:
        """Calculate progress as percentage."""
        if self.total_characters == 0:
            return 0.0
        return (self.characters_processed / self.total_characters) * 100
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_estimated_remaining_time(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        if self.characters_processed == 0:
            return None
        
        elapsed = self.get_elapsed_time()
        rate = self.characters_processed / elapsed
        remaining_characters = self.total_characters - self.characters_processed
        
        if rate > 0:
            return remaining_characters / rate
        return None


class DatabaseBuilder:
    """
    Main orchestrator class for building character databases from wiki data.
    
    This class coordinates all components of the database building process:
    - Scraping the main wiki page for character lists
    - Extracting detailed data from individual character pages
    - Downloading character images
    - Generating CSV database files
    
    The class provides comprehensive progress tracking, error handling, and
    recovery mechanisms to ensure robust operation even with network issues
    or partial failures.
    """
    
    def __init__(self, config: Optional[DatabaseBuilderConfig] = None):
        """
        Initialize the DatabaseBuilder with configuration and components.
        
        Args:
            config: Database builder configuration. Uses default if None.
        """
        self.config = config or DatabaseBuilderConfig()
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(__name__)
        
        # Initialize components
        self.wiki_scraper = WikiScraper(self.config.base_url)
        self.character_extractor = CharacterDataExtractor(self.config.base_url)
        self.image_downloader = ImageDownloader(self.config)
        self.csv_generator = CSVGenerator(self.config)
        
        # Progress tracking
        self.progress = ProcessingProgress()
        
        # Results tracking
        self.build_result = DatabaseBuildResult()
        
        self.logger.info("DatabaseBuilder initialized with configuration")
    
    def build_database(self) -> DatabaseBuildResult:
        """
        Main entry point for database building process.
        
        Coordinates the complete workflow:
        1. Scrape main wiki page for character lists by tier
        2. Process each tier and extract character data
        3. Download character images
        4. Generate CSV database file
        5. Provide comprehensive results and statistics
        
        Returns:
            DatabaseBuildResult with comprehensive build information
            
        Raises:
            Exception: If critical errors prevent database building
        """
        start_time = time.time()
        self.logger.info("Starting database build process")
        
        try:
            # Initialize progress tracking
            self.progress = ProcessingProgress()
            self.build_result = DatabaseBuildResult()
            
            # Step 1: Scrape main wiki page for character lists
            self.logger.info("Step 1: Scraping main wiki page for character lists")
            tier_data = self._scrape_character_lists()
            
            if not tier_data:
                raise Exception("No character data found on main wiki page")
            
            # Calculate total characters for progress tracking
            total_characters = sum(len(characters) for characters in tier_data.values())
            self.progress.total_characters = total_characters
            self.build_result.total_characters = total_characters
            
            self.logger.info(f"Found {total_characters} characters across {len(tier_data)} tiers")
            
            # Step 2: Process each tier and extract character data
            self.logger.info("Step 2: Processing tiers and extracting character data")
            all_characters = self._process_all_tiers(tier_data)
            
            # Step 3: Download character images
            self.logger.info("Step 3: Downloading character images")
            self._download_character_images(all_characters)
            
            # Step 4: Generate CSV database file
            self.logger.info("Step 4: Generating CSV database file")
            csv_path = self._generate_csv_database(all_characters)
            self.build_result.csv_file_path = csv_path
            
            # Calculate final statistics
            self.build_result.processing_time = time.time() - start_time
            self._calculate_final_statistics(all_characters)
            
            self.logger.info(f"Database build completed successfully in {self.build_result.processing_time:.1f}s")
            self.logger.info(f"Generated database: {csv_path}")
            self.logger.info(f"Success rate: {self.build_result.get_success_rate():.1f}%")
            
            return self.build_result
            
        except Exception as e:
            self.build_result.processing_time = time.time() - start_time
            self.build_result.errors.append(f"Critical error: {str(e)}")
            
            self.error_handler.handle_error(
                e, ErrorCategory.DATABASE_BUILDING, ErrorSeverity.HIGH,
                context={'processing_time': self.build_result.processing_time}
            )
            
            self.logger.error(f"Database build failed after {self.build_result.processing_time:.1f}s: {e}")
            raise
        
        finally:
            # Clean up resources
            self._cleanup_resources()
    
    def _scrape_character_lists(self) -> Dict[str, List[str]]:
        """
        Scrape the main wiki page to get character lists by tier.
        
        Returns:
            Dictionary mapping tier names to character name lists
            
        Raises:
            Exception: If scraping fails completely
        """
        try:
            tier_data = self.wiki_scraper.scrape_brainrots_page()
            
            if not tier_data:
                raise Exception("Wiki scraper returned empty tier data")
            
            # Log tier statistics
            for tier, characters in tier_data.items():
                self.logger.info(f"Tier '{tier}': {len(characters)} characters")
                
                # Initialize tier statistics
                self.build_result.tier_statistics[tier] = {
                    'total': len(characters),
                    'successful': 0,
                    'failed': 0,
                    'images_downloaded': 0,
                    'images_failed': 0
                }
            
            return tier_data
            
        except Exception as e:
            self.build_result.errors.append(f"Failed to scrape character lists: {str(e)}")
            raise Exception(f"Could not scrape main wiki page: {str(e)}")
    
    def _process_all_tiers(self, tier_data: Dict[str, List[str]]) -> List[CharacterData]:
        """
        Process all tiers and extract character data with error recovery.
        
        Args:
            tier_data: Dictionary mapping tier names to character lists
            
        Returns:
            List of successfully extracted CharacterData objects
        """
        all_characters = []
        
        for tier_name, character_names in tier_data.items():
            self.logger.info(f"Processing tier: {tier_name} ({len(character_names)} characters)")
            self.progress.current_tier = tier_name
            
            tier_characters = self._process_tier_section(tier_name, character_names)
            all_characters.extend(tier_characters)
            
            # Update tier statistics
            successful_count = len([c for c in tier_characters if c.extraction_success])
            failed_count = len(character_names) - successful_count
            
            self.build_result.tier_statistics[tier_name]['successful'] = successful_count
            self.build_result.tier_statistics[tier_name]['failed'] = failed_count
            
            self.logger.info(f"Tier {tier_name} completed: {successful_count}/{len(character_names)} successful")
        
        self.build_result.successful_extractions = len([c for c in all_characters if c.extraction_success])
        self.build_result.failed_extractions = self.build_result.total_characters - self.build_result.successful_extractions
        
        return all_characters
    
    def _process_tier_section(self, tier: str, characters: List[str]) -> List[CharacterData]:
        """
        Process all characters in a specific tier with proper error recovery.
        
        Args:
            tier: Name of the tier being processed
            characters: List of character names in this tier
            
        Returns:
            List of CharacterData objects (may include failed extractions)
        """
        tier_characters = []
        
        for character_name in characters:
            try:
                self.progress.current_character = character_name
                self.logger.debug(f"Processing character: {character_name} ({tier})")
                
                # Extract character data
                character_data = self.character_extractor.extract_character_data(character_name, tier)
                
                if character_data:
                    tier_characters.append(character_data)
                    
                    if character_data.extraction_success:
                        self.logger.debug(f"Successfully extracted: {character_name}")
                    else:
                        self.logger.warning(f"Partial extraction for: {character_name}")
                        self.build_result.warnings.append(f"Partial data for {character_name}: {character_data.extraction_errors}")
                else:
                    # Create failed character entry for tracking
                    failed_character = CharacterData(
                        name=character_name,
                        tier=tier,
                        cost=0,
                        income=0,
                        variant="Standard"
                    )
                    failed_character.extraction_success = False
                    failed_character.extraction_errors = ["Complete extraction failure"]
                    tier_characters.append(failed_character)
                    
                    self.logger.warning(f"Failed to extract data for: {character_name}")
                    self.build_result.warnings.append(f"Failed to extract data for {character_name}")
                
                # Update progress
                self.progress.characters_processed += 1
                
                # Log progress periodically
                if self.progress.characters_processed % 10 == 0:
                    progress_pct = self.progress.get_progress_percentage()
                    remaining_time = self.progress.get_estimated_remaining_time()
                    
                    if remaining_time:
                        self.logger.info(f"Progress: {progress_pct:.1f}% ({self.progress.characters_processed}/{self.progress.total_characters}) - ETA: {remaining_time:.0f}s")
                    else:
                        self.logger.info(f"Progress: {progress_pct:.1f}% ({self.progress.characters_processed}/{self.progress.total_characters})")
                
                # Apply rate limiting between characters
                time.sleep(self.config.rate_limit_delay)
                
            except Exception as e:
                # Handle individual character extraction errors
                self.error_handler.handle_error(
                    e, ErrorCategory.CHARACTER_EXTRACTION, ErrorSeverity.MEDIUM,
                    context={'character': character_name, 'tier': tier}
                )
                
                # Create failed character entry
                failed_character = CharacterData(
                    name=character_name,
                    tier=tier,
                    cost=0,
                    income=0,
                    variant="Standard"
                )
                failed_character.extraction_success = False
                failed_character.extraction_errors = [f"Exception during extraction: {str(e)}"]
                tier_characters.append(failed_character)
                
                self.build_result.errors.append(f"Error processing {character_name}: {str(e)}")
                self.progress.characters_processed += 1
                
                # Continue with next character
                continue
        
        return tier_characters
    
    def _download_character_images(self, characters: List[CharacterData]) -> None:
        """
        Download images for all characters with proper error handling.
        
        Args:
            characters: List of CharacterData objects to download images for
        """
        characters_with_images = [c for c in characters if c.image_url and c.extraction_success]
        
        if not characters_with_images:
            self.logger.warning("No characters have image URLs for download")
            return
        
        self.logger.info(f"Downloading images for {len(characters_with_images)} characters")
        
        for character in characters_with_images:
            try:
                self.logger.debug(f"Downloading image for: {character.name}")
                
                image_path = self.image_downloader.download_character_image(
                    character.name, character.image_url
                )
                
                if image_path:
                    character.image_path = image_path
                    self.build_result.images_downloaded += 1
                    
                    # Update tier statistics
                    if character.tier in self.build_result.tier_statistics:
                        self.build_result.tier_statistics[character.tier]['images_downloaded'] += 1
                    
                    self.logger.debug(f"Image downloaded: {character.name} -> {image_path}")
                else:
                    self.build_result.images_failed += 1
                    
                    # Update tier statistics
                    if character.tier in self.build_result.tier_statistics:
                        self.build_result.tier_statistics[character.tier]['images_failed'] += 1
                    
                    self.logger.warning(f"Failed to download image for: {character.name}")
                    self.build_result.warnings.append(f"Image download failed for {character.name}")
                
                # Apply rate limiting between downloads
                time.sleep(self.config.rate_limit_delay)
                
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.IMAGE_DOWNLOAD, ErrorSeverity.MEDIUM,
                    context={'character': character.name, 'image_url': character.image_url}
                )
                
                self.build_result.images_failed += 1
                self.build_result.errors.append(f"Image download error for {character.name}: {str(e)}")
                
                # Update tier statistics
                if character.tier in self.build_result.tier_statistics:
                    self.build_result.tier_statistics[character.tier]['images_failed'] += 1
                
                # Continue with next character
                continue
        
        self.logger.info(f"Image downloads completed: {self.build_result.images_downloaded} successful, {self.build_result.images_failed} failed")
    
    def _generate_csv_database(self, characters: List[CharacterData]) -> str:
        """
        Generate the final CSV database file.
        
        Args:
            characters: List of all CharacterData objects
            
        Returns:
            Path to generated CSV file
            
        Raises:
            Exception: If CSV generation fails
        """
        try:
            # Filter to only include successfully extracted characters
            valid_characters = [c for c in characters if c.extraction_success]
            
            if not valid_characters:
                raise Exception("No valid characters to include in CSV database")
            
            self.logger.info(f"Generating CSV database with {len(valid_characters)} characters")
            
            csv_path = self.csv_generator.generate_csv(valid_characters)
            
            # Validate the generated CSV
            if self.config.validate_csv_output:
                self.csv_generator.validate_csv_format(csv_path)
                self.logger.info("CSV format validation passed")
            
            return csv_path
            
        except Exception as e:
            self.build_result.errors.append(f"CSV generation failed: {str(e)}")
            raise Exception(f"Could not generate CSV database: {str(e)}")
    
    def _calculate_final_statistics(self, characters: List[CharacterData]) -> None:
        """
        Calculate final statistics for the build result.
        
        Args:
            characters: List of all processed characters
        """
        # Overall statistics are already calculated
        # Add any additional statistics here if needed
        
        # Log comprehensive results
        self.logger.info("=== Database Build Results ===")
        self.logger.info(f"Total characters processed: {self.build_result.total_characters}")
        self.logger.info(f"Successful extractions: {self.build_result.successful_extractions}")
        self.logger.info(f"Failed extractions: {self.build_result.failed_extractions}")
        self.logger.info(f"Success rate: {self.build_result.get_success_rate():.1f}%")
        self.logger.info(f"Images downloaded: {self.build_result.images_downloaded}")
        self.logger.info(f"Image download failures: {self.build_result.images_failed}")
        self.logger.info(f"Image success rate: {self.build_result.get_image_success_rate():.1f}%")
        self.logger.info(f"Processing time: {self.build_result.processing_time:.1f} seconds")
        self.logger.info(f"CSV database: {self.build_result.csv_file_path}")
        
        # Log tier-by-tier statistics
        self.logger.info("=== Tier Statistics ===")
        for tier, stats in self.build_result.tier_statistics.items():
            success_rate = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0
            image_rate = (stats['images_downloaded'] / (stats['images_downloaded'] + stats['images_failed'])) * 100 if (stats['images_downloaded'] + stats['images_failed']) > 0 else 0
            self.logger.info(f"{tier}: {stats['successful']}/{stats['total']} characters ({success_rate:.1f}%), {stats['images_downloaded']} images ({image_rate:.1f}%)")
        
        # Log errors and warnings summary
        if self.build_result.errors:
            self.logger.warning(f"Total errors: {len(self.build_result.errors)}")
        
        if self.build_result.warnings:
            self.logger.warning(f"Total warnings: {len(self.build_result.warnings)}")
    
    def _cleanup_resources(self) -> None:
        """
        Clean up resources and close connections.
        """
        try:
            if hasattr(self.wiki_scraper, 'close'):
                self.wiki_scraper.close()
            
            if hasattr(self.character_extractor, 'close'):
                self.character_extractor.close()
            
            self.logger.debug("Resources cleaned up successfully")
            
        except Exception as e:
            self.logger.warning(f"Error during resource cleanup: {e}")
    
    def get_progress_info(self) -> Dict[str, Any]:
        """
        Get current progress information.
        
        Returns:
            Dictionary with current progress details
        """
        return {
            'current_tier': self.progress.current_tier,
            'current_character': self.progress.current_character,
            'characters_processed': self.progress.characters_processed,
            'total_characters': self.progress.total_characters,
            'progress_percentage': self.progress.get_progress_percentage(),
            'elapsed_time': self.progress.get_elapsed_time(),
            'estimated_remaining_time': self.progress.get_estimated_remaining_time(),
            'successful_extractions': self.build_result.successful_extractions,
            'failed_extractions': self.build_result.failed_extractions,
            'images_downloaded': self.build_result.images_downloaded,
            'images_failed': self.build_result.images_failed
        }
    
    def cancel_build(self) -> None:
        """
        Cancel the current build operation.
        
        This method can be called from another thread to gracefully stop
        the build process. The build will complete the current character
        and then stop.
        """
        # Implementation for cancellation would go here
        # For now, just log the request
        self.logger.warning("Build cancellation requested")
        # In a full implementation, this would set a flag that the main loop checks