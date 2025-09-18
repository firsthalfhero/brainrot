"""
CSV generation functionality for the database builder.
"""

import csv
import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from .config import DatabaseBuilderConfig
from .data_models import CharacterData
from .output_manager import OutputManager
from .error_handling import ErrorHandler, ErrorCategory, ErrorSeverity


logger = logging.getLogger(__name__)


class CSVGenerator:
    """
    Handles the generation of CSV database files from character data.
    
    This class creates properly formatted CSV files with character information
    that can be used by the existing card generation system. It integrates with
    the OutputManager for consistent file handling and includes timestamp-based
    filename generation for version control.
    """
    
    def __init__(self, config: Optional[DatabaseBuilderConfig] = None):
        """
        Initialize the CSVGenerator with configuration.
        
        Args:
            config: Database builder configuration. Uses default if None.
        """
        self.config = config or DatabaseBuilderConfig()
        self.output_manager = OutputManager()
        self.error_handler = ErrorHandler(__name__)
        self._ensure_output_directory()
    
    def generate_csv(self, characters: List[CharacterData]) -> str:
        """
        Generate a CSV file from character data.
        
        Args:
            characters: List of CharacterData objects to include in CSV
            
        Returns:
            Path to the generated CSV file
            
        Raises:
            ValueError: If characters list is empty or invalid
            IOError: If CSV file cannot be created
        """
        if not characters:
            raise ValueError("Cannot generate CSV from empty character list")
        
        # Validate character data
        self._validate_character_data(characters)
        
        # Generate filename with timestamp
        filename = self._generate_filename()
        filepath = Path(self.config.output_dir) / filename
        
        try:
            # Create CSV headers
            headers = self._create_csv_headers()
            
            # Write CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                writer.writerow(headers)
                
                # Write character data
                for character in characters:
                    row = self._character_to_csv_row(character)
                    writer.writerow(row)
            
            # Verify file was created successfully
            if not filepath.exists():
                raise IOError("CSV file was not created successfully")
            
            file_size = filepath.stat().st_size
            if file_size == 0:
                filepath.unlink()  # Remove empty file
                raise IOError("Created CSV file is empty")
            
            logger.info(f"Generated CSV database: {filepath} ({len(characters)} characters, {file_size} bytes)")
            return str(filepath)
            
        except PermissionError as e:
            logger.error(f"Permission denied creating CSV file: {e}")
            raise IOError(f"Permission denied: {e}")
        except OSError as e:
            if e.errno == 28:  # No space left on device
                logger.error("Disk full while creating CSV file")
                raise IOError("Disk full - cannot create CSV file")
            else:
                logger.error(f"OS error creating CSV file: {e}")
                raise IOError(f"File system error: {e}")
        except Exception as e:
            logger.error(f"Failed to generate CSV file: {e}")
            raise IOError(f"Could not create CSV file: {e}")
    
    def append_to_existing_csv(self, characters: List[CharacterData], csv_path: str) -> str:
        """
        Append character data to an existing CSV file.
        
        Args:
            characters: List of CharacterData objects to append
            csv_path: Path to existing CSV file
            
        Returns:
            Path to the updated CSV file
            
        Raises:
            ValueError: If characters list is empty or CSV file doesn't exist
            IOError: If CSV file cannot be updated
        """
        if not characters:
            raise ValueError("Cannot append empty character list to CSV")
        
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise ValueError(f"CSV file does not exist: {csv_path}")
        
        # Validate character data
        self._validate_character_data(characters)
        
        try:
            # Append to existing file
            with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write character data
                for character in characters:
                    row = self._character_to_csv_row(character)
                    writer.writerow(row)
            
            logger.info(f"Appended {len(characters)} characters to CSV: {csv_path}")
            return str(csv_file)
            
        except PermissionError as e:
            logger.error(f"Permission denied updating CSV file: {e}")
            raise IOError(f"Permission denied: {e}")
        except Exception as e:
            logger.error(f"Failed to append to CSV file: {e}")
            raise IOError(f"Could not update CSV file: {e}")
    
    def validate_csv_format(self, csv_path: str) -> bool:
        """
        Validate that a CSV file has the correct format for the card generation system.
        
        Args:
            csv_path: Path to CSV file to validate
            
        Returns:
            True if CSV format is valid
            
        Raises:
            ValueError: If CSV format is invalid
            IOError: If CSV file cannot be read
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise IOError(f"CSV file does not exist: {csv_path}")
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                
                # Check headers
                headers = next(reader, None)
                if not headers:
                    raise ValueError("CSV file is empty or has no headers")
                
                expected_headers = self._create_csv_headers()
                if headers != expected_headers:
                    raise ValueError(f"Invalid CSV headers. Expected: {expected_headers}, Got: {headers}")
                
                # Check at least one data row exists
                first_row = next(reader, None)
                if not first_row:
                    raise ValueError("CSV file has no data rows")
                
                # Validate first row format
                if len(first_row) != len(expected_headers):
                    raise ValueError(f"Data row has {len(first_row)} columns, expected {len(expected_headers)}")
                
                logger.info(f"CSV format validation passed: {csv_path}")
                return True
                
        except PermissionError as e:
            logger.error(f"Permission denied reading CSV file: {e}")
            raise IOError(f"Permission denied: {e}")
        except ValueError as e:
            # Re-raise ValueError as-is for format validation errors
            raise e
        except Exception as e:
            logger.error(f"Failed to validate CSV file: {e}")
            raise IOError(f"Could not read CSV file: {e}")
    
    def get_csv_statistics(self, csv_path: str) -> Dict[str, Any]:
        """
        Get statistics about a CSV database file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Dictionary with statistics about the CSV file
            
        Raises:
            IOError: If CSV file cannot be read
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise IOError(f"CSV file does not exist: {csv_path}")
        
        stats = {
            'file_path': str(csv_file),
            'file_size': 0,
            'total_characters': 0,
            'characters_by_tier': {},
            'characters_with_images': 0,
            'characters_without_images': 0,
            'creation_time': None,
            'modification_time': None
        }
        
        try:
            # Get file statistics
            file_stat = csv_file.stat()
            stats['file_size'] = file_stat.st_size
            stats['creation_time'] = datetime.fromtimestamp(file_stat.st_ctime)
            stats['modification_time'] = datetime.fromtimestamp(file_stat.st_mtime)
            
            # Read and analyze CSV content
            with open(csv_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    stats['total_characters'] += 1
                    
                    # Count by tier
                    tier = row.get('Tier', 'Unknown')
                    stats['characters_by_tier'][tier] = stats['characters_by_tier'].get(tier, 0) + 1
                    
                    # Count images
                    image_path = row.get('Image Path', '')
                    if image_path and image_path.strip():
                        stats['characters_with_images'] += 1
                    else:
                        stats['characters_without_images'] += 1
            
            logger.info(f"CSV statistics generated for: {csv_path}")
            return stats
            
        except PermissionError as e:
            logger.error(f"Permission denied reading CSV file: {e}")
            raise IOError(f"Permission denied: {e}")
        except Exception as e:
            logger.error(f"Failed to get CSV statistics: {e}")
            raise IOError(f"Could not analyze CSV file: {e}")
    
    def _create_csv_headers(self) -> List[str]:
        """
        Define CSV column headers compatible with existing card generation system.
        
        Returns:
            List of CSV header strings
        """
        return [
            'Character Name',
            'Tier',
            'Cost',
            'Income per Second',
            'Variant Type',
            'Image Path'
        ]
    
    def _character_to_csv_row(self, character: CharacterData) -> List[str]:
        """
        Convert a CharacterData object to a CSV row.
        
        Args:
            character: CharacterData object to convert
            
        Returns:
            List of strings representing the CSV row
        """
        return [
            character.name,
            character.tier,
            str(character.cost),
            str(character.income),
            character.variant,
            character.image_path or ''  # Empty string if no image path
        ]
    
    def _generate_filename(self) -> str:
        """
        Generate a timestamp-based filename for the CSV file.
        
        Returns:
            Generated filename string
        """
        if self.config.include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return self.config.get_csv_filename(timestamp)
        else:
            return self.config.get_csv_filename()
    
    def _validate_character_data(self, characters: List[CharacterData]) -> None:
        """
        Validate character data before CSV generation.
        
        Args:
            characters: List of CharacterData objects to validate
            
        Raises:
            ValueError: If any character data is invalid
        """
        if not isinstance(characters, list):
            raise ValueError("Characters must be provided as a list")
        
        for i, character in enumerate(characters):
            if not isinstance(character, CharacterData):
                raise ValueError(f"Item at index {i} is not a CharacterData object")
            
            # Validate required fields
            if not character.name or not character.name.strip():
                raise ValueError(f"Character at index {i} has empty or invalid name")
            
            if not character.tier or not character.tier.strip():
                raise ValueError(f"Character '{character.name}' has empty or invalid tier")
            
            if not isinstance(character.cost, int) or character.cost < 0:
                raise ValueError(f"Character '{character.name}' has invalid cost: {character.cost}")
            
            if not isinstance(character.income, int) or character.income < 0:
                raise ValueError(f"Character '{character.name}' has invalid income: {character.income}")
            
            if not character.variant or not character.variant.strip():
                raise ValueError(f"Character '{character.name}' has empty or invalid variant")
    
    def _ensure_output_directory(self) -> None:
        """
        Ensure that the output directory exists and is writable.
        
        Raises:
            IOError: If directory cannot be created or is not writable
        """
        try:
            output_dir = Path(self.config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = output_dir / '.write_test'
            try:
                test_file.write_text('test')
                test_file.unlink()
            except PermissionError:
                raise IOError(f"Output directory is not writable: {output_dir}")
            except Exception as e:
                raise IOError(f"Cannot write to output directory {output_dir}: {e}")
            
            logger.debug(f"Ensured CSV output directory exists: {output_dir}")
            
        except PermissionError:
            raise IOError(f"Permission denied creating output directory: {self.config.output_dir}")
        except Exception as e:
            raise IOError(f"Cannot create output directory {self.config.output_dir}: {e}")