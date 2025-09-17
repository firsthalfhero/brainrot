"""
CSV data loading functionality for the Trading Card Generator.
"""

import csv
import os
import glob
import re
import logging
from typing import List, Optional, Set, Callable
from .data_models import CharacterData
from .error_handling import ErrorHandler, ErrorCategory, ErrorSeverity


class CSVDataLoader:
    """
    Handles loading character data from CSV files and matching with image files.
    """
    
    def __init__(self, csv_path: str = 'steal_a_brainrot_complete_database.csv', 
                 images_dir: str = 'images/'):
        """
        Initialize the CSV data loader.
        
        Args:
            csv_path: Path to the CSV file containing character data
            images_dir: Directory containing character images
        """
        self.csv_path = csv_path
        self.images_dir = images_dir
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(__name__)
        self._failed_characters = []  # Track characters that failed to load
    
    def load_characters(self) -> List[CharacterData]:
        """
        Load all characters from the CSV file and match with available images.
        
        Returns:
            List of CharacterData objects with image paths populated where available
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV data is invalid or corrupted
        """
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        characters = []
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as csvfile:
                # Use csv.Sniffer to detect delimiter and quote character
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 since header is row 1
                    try:
                        character = self._parse_character_row(row)
                        # Find and set image path
                        character.image_path = self.find_character_image(character.name)
                        characters.append(character)
                    except ValueError as e:
                        error_msg = f"Invalid character data at row {row_num}: {e}"
                        self.logger.warning(error_msg)
                        self._failed_characters.append({
                            'row': row_num,
                            'data': row,
                            'error': str(e)
                        })
                        continue
                    except Exception as e:
                        error_msg = f"Unexpected error processing row {row_num}: {e}"
                        self.logger.error(error_msg)
                        self._failed_characters.append({
                            'row': row_num,
                            'data': row,
                            'error': str(e)
                        })
                        continue
                        
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(self.csv_path, 'r', encoding='latin-1') as csvfile:
                    sample = csvfile.read(1024)
                    csvfile.seek(0)
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
                    
                    reader = csv.DictReader(csvfile, delimiter=delimiter)
                    
                    for row_num, row in enumerate(reader, start=2):
                        try:
                            character = self._parse_character_row(row)
                            character.image_path = self.find_character_image(character.name)
                            characters.append(character)
                        except ValueError as e:
                            error_msg = f"Invalid character data at row {row_num}: {e}"
                            self.logger.warning(error_msg)
                            self._failed_characters.append({
                                'row': row_num,
                                'data': row,
                                'error': str(e)
                            })
                            continue
                        except Exception as e:
                            error_msg = f"Unexpected error processing row {row_num}: {e}"
                            self.logger.error(error_msg)
                            self._failed_characters.append({
                                'row': row_num,
                                'data': row,
                                'error': str(e)
                            })
                            continue
            except Exception as e:
                raise ValueError(f"Failed to read CSV file with multiple encodings: {e}")
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
        
        if not characters:
            raise ValueError("No valid character data found in CSV file")
            
        return characters
    
    def _parse_character_row(self, row: dict) -> CharacterData:
        """
        Parse a single CSV row into a CharacterData object.
        
        Args:
            row: Dictionary representing a CSV row
            
        Returns:
            CharacterData object
            
        Raises:
            ValueError: If row data is invalid
        """
        try:
            # Handle different possible column names
            name = row.get('Character Name', '').strip().strip('"')
            tier = row.get('Tier', '').strip().strip('"')
            cost_str = row.get('Cost', '').strip().strip('"')
            income_str = row.get('Income per Second', '').strip().strip('"')
            variant = row.get('Variant Type', '').strip().strip('"')
            
            if not name:
                raise ValueError("Character name is required")
            
            if not tier:
                raise ValueError(f"Tier is required for character: {name}")
            
            # Parse numeric values
            try:
                cost = int(cost_str)
            except ValueError:
                raise ValueError(f"Invalid cost value '{cost_str}' for character: {name}")
            
            try:
                income = int(income_str)
            except ValueError:
                raise ValueError(f"Invalid income value '{income_str}' for character: {name}")
            
            if not variant:
                variant = "Standard"  # Default variant if not specified
            
            return CharacterData(
                name=name,
                tier=tier,
                cost=cost,
                income=income,
                variant=variant
            )
            
        except KeyError as e:
            raise ValueError(f"Missing required column in CSV: {e}")
    
    def find_character_image(self, character_name: str) -> Optional[str]:
        """
        Find the first available image file for a character.
        
        Args:
            character_name: Name of the character to find image for
            
        Returns:
            Path to the character's image file, or None if not found
        """
        if not os.path.exists(self.images_dir):
            return None
        
        # Supported image extensions
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp']
        
        # Try to find images with the exact character name
        for ext in extensions:
            # Pattern: "Character Name_*.extension"
            pattern = os.path.join(self.images_dir, f"{character_name}_*{ext[1:]}")
            matches = glob.glob(pattern)
            
            if matches:
                # Sort to get consistent results (prefer _1 over _2, etc.)
                matches.sort()
                return matches[0]
        
        # If no exact match, try case-insensitive search
        all_files = []
        for ext in extensions:
            pattern = os.path.join(self.images_dir, ext)
            all_files.extend(glob.glob(pattern))
        
        # Look for files that start with the character name (case-insensitive)
        character_name_lower = character_name.lower()
        for file_path in all_files:
            filename = os.path.basename(file_path)
            if filename.lower().startswith(character_name_lower.lower()):
                return file_path
        
        return None
    
    def get_characters_with_images(self) -> List[CharacterData]:
        """
        Load characters and return only those with available images.
        
        Returns:
            List of CharacterData objects that have associated image files
        """
        all_characters = self.load_characters()
        return [char for char in all_characters if char.has_image()]
    
    def get_characters_without_images(self) -> List[CharacterData]:
        """
        Load characters and return only those without available images.
        
        Returns:
            List of CharacterData objects that don't have associated image files
        """
        all_characters = self.load_characters()
        return [char for char in all_characters if not char.has_image()]
    
    def get_character_count(self) -> int:
        """
        Get the total number of characters in the CSV file.
        
        Returns:
            Number of characters loaded from CSV
        """
        return len(self.load_characters())
    
    def get_image_coverage_stats(self) -> dict:
        """
        Get statistics about image coverage for characters.
        
        Returns:
            Dictionary with coverage statistics
        """
        all_characters = self.load_characters()
        total = len(all_characters)
        with_images = len([char for char in all_characters if char.has_image()])
        without_images = total - with_images
        
        return {
            'total_characters': total,
            'characters_with_images': with_images,
            'characters_without_images': without_images,
            'image_coverage_percentage': (with_images / total * 100) if total > 0 else 0
        }
    
    def filter_characters_by_name(self, characters: List[CharacterData], 
                                  names: List[str], case_sensitive: bool = False) -> List[CharacterData]:
        """
        Filter characters by exact name matches.
        
        Args:
            characters: List of characters to filter
            names: List of character names to include
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List of characters matching the specified names
        """
        if not names:
            return characters
        
        if case_sensitive:
            name_set = set(names)
            return [char for char in characters if char.name in name_set]
        else:
            name_set = set(name.lower() for name in names)
            return [char for char in characters if char.name.lower() in name_set]
    
    def filter_characters_by_name_pattern(self, characters: List[CharacterData], 
                                          pattern: str, case_sensitive: bool = False) -> List[CharacterData]:
        """
        Filter characters by name pattern (supports wildcards and regex).
        
        Args:
            characters: List of characters to filter
            pattern: Pattern to match (supports * wildcards or regex)
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List of characters matching the pattern
        """
        if not pattern:
            return characters
        
        # Convert simple wildcards to regex if pattern contains *
        if '*' in pattern and not any(c in pattern for c in r'[]{}()^$+?.\|'):
            # Simple wildcard pattern
            regex_pattern = pattern.replace('*', '.*')
        else:
            # Assume it's already a regex pattern
            regex_pattern = pattern
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            compiled_pattern = re.compile(regex_pattern, flags)
            return [char for char in characters if compiled_pattern.search(char.name)]
        except re.error as e:
            raise ValueError(f"Invalid pattern '{pattern}': {e}")
    
    def filter_characters_by_tier(self, characters: List[CharacterData], 
                                  tiers: List[str], case_sensitive: bool = False) -> List[CharacterData]:
        """
        Filter characters by tier.
        
        Args:
            characters: List of characters to filter
            tiers: List of tiers to include
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List of characters matching the specified tiers
        """
        if not tiers:
            return characters
        
        if case_sensitive:
            tier_set = set(tiers)
            return [char for char in characters if char.tier in tier_set]
        else:
            tier_set = set(tier.lower() for tier in tiers)
            return [char for char in characters if char.tier.lower() in tier_set]
    
    def filter_characters_by_cost_range(self, characters: List[CharacterData], 
                                        min_cost: Optional[int] = None, 
                                        max_cost: Optional[int] = None) -> List[CharacterData]:
        """
        Filter characters by cost range.
        
        Args:
            characters: List of characters to filter
            min_cost: Minimum cost (inclusive), None for no minimum
            max_cost: Maximum cost (inclusive), None for no maximum
            
        Returns:
            List of characters within the cost range
        """
        filtered = characters
        
        if min_cost is not None:
            filtered = [char for char in filtered if char.cost >= min_cost]
        
        if max_cost is not None:
            filtered = [char for char in filtered if char.cost <= max_cost]
        
        return filtered
    
    def filter_characters_by_income_range(self, characters: List[CharacterData], 
                                          min_income: Optional[int] = None, 
                                          max_income: Optional[int] = None) -> List[CharacterData]:
        """
        Filter characters by income range.
        
        Args:
            characters: List of characters to filter
            min_income: Minimum income (inclusive), None for no minimum
            max_income: Maximum income (inclusive), None for no maximum
            
        Returns:
            List of characters within the income range
        """
        filtered = characters
        
        if min_income is not None:
            filtered = [char for char in filtered if char.income >= min_income]
        
        if max_income is not None:
            filtered = [char for char in filtered if char.income <= max_income]
        
        return filtered
    
    def filter_characters_by_variant(self, characters: List[CharacterData], 
                                     variants: List[str], case_sensitive: bool = False) -> List[CharacterData]:
        """
        Filter characters by variant type.
        
        Args:
            characters: List of characters to filter
            variants: List of variants to include
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List of characters matching the specified variants
        """
        if not variants:
            return characters
        
        if case_sensitive:
            variant_set = set(variants)
            return [char for char in characters if char.variant in variant_set]
        else:
            variant_set = set(variant.lower() for variant in variants)
            return [char for char in characters if char.variant.lower() in variant_set]
    
    def filter_characters_with_images_only(self, characters: List[CharacterData]) -> List[CharacterData]:
        """
        Filter characters to include only those with available images.
        
        Args:
            characters: List of characters to filter
            
        Returns:
            List of characters that have associated image files
        """
        return [char for char in characters if char.has_image()]
    
    def filter_characters_without_images_only(self, characters: List[CharacterData]) -> List[CharacterData]:
        """
        Filter characters to include only those without available images.
        
        Args:
            characters: List of characters to filter
            
        Returns:
            List of characters that don't have associated image files
        """
        return [char for char in characters if not char.has_image()]
    
    def apply_custom_filter(self, characters: List[CharacterData], 
                           filter_func: Callable[[CharacterData], bool]) -> List[CharacterData]:
        """
        Apply a custom filter function to characters.
        
        Args:
            characters: List of characters to filter
            filter_func: Function that takes a CharacterData and returns bool
            
        Returns:
            List of characters that pass the filter function
        """
        return [char for char in characters if filter_func(char)]
    
    def get_available_tiers(self) -> List[str]:
        """
        Get all unique tiers from the loaded characters.
        
        Returns:
            Sorted list of unique tier names
        """
        characters = self.load_characters()
        tiers = set(char.tier for char in characters)
        return sorted(list(tiers))
    
    def get_available_variants(self) -> List[str]:
        """
        Get all unique variants from the loaded characters.
        
        Returns:
            Sorted list of unique variant names
        """
        characters = self.load_characters()
        variants = set(char.variant for char in characters)
        return sorted(list(variants))
    
    def get_character_names(self) -> List[str]:
        """
        Get all character names from the loaded characters.
        
        Returns:
            Sorted list of character names
        """
        characters = self.load_characters()
        return sorted([char.name for char in characters])
    
    def get_failed_characters(self) -> List[dict]:
        """
        Get information about characters that failed to load.
        
        Returns:
            List of dictionaries containing failed character information
        """
        return self._failed_characters.copy()
    
    def get_loading_summary(self) -> dict:
        """
        Get summary of the loading process including successes and failures.
        
        Returns:
            Dictionary with loading statistics
        """
        try:
            successful_count = len(self.load_characters())
        except Exception:
            successful_count = 0
        
        return {
            'successful_characters': successful_count,
            'failed_characters': len(self._failed_characters),
            'total_processed': successful_count + len(self._failed_characters),
            'success_rate': (successful_count / (successful_count + len(self._failed_characters)) * 100) 
                           if (successful_count + len(self._failed_characters)) > 0 else 0,
            'failures': self._failed_characters.copy()
        }
    
    def validate_csv_structure(self) -> dict:
        """
        Validate the CSV file structure without loading all data.
        
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'required_columns': ['Character Name', 'Tier', 'Cost', 'Income per Second'],
            'found_columns': [],
            'missing_columns': [],
            'extra_columns': []
        }
        
        try:
            if not os.path.exists(self.csv_path):
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"CSV file not found: {self.csv_path}")
                return validation_result
            
            # Check file permissions
            if not os.access(self.csv_path, os.R_OK):
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"No read permission for CSV file: {self.csv_path}")
                return validation_result
            
            with open(self.csv_path, 'r', encoding='utf-8') as csvfile:
                # Read first few lines to detect structure
                sample = csvfile.read(2048)
                csvfile.seek(0)
                
                if not sample.strip():
                    validation_result['is_valid'] = False
                    validation_result['errors'].append("CSV file is empty")
                    return validation_result
                
                # Detect delimiter
                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except csv.Error:
                    delimiter = ','
                    validation_result['warnings'].append("Could not detect CSV delimiter, assuming comma")
                
                # Read header
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                validation_result['found_columns'] = list(reader.fieldnames or [])
                
                # Check for required columns
                for required_col in validation_result['required_columns']:
                    if required_col not in validation_result['found_columns']:
                        validation_result['missing_columns'].append(required_col)
                        validation_result['is_valid'] = False
                
                # Check for extra columns
                for found_col in validation_result['found_columns']:
                    if found_col not in validation_result['required_columns'] and found_col != 'Variant Type':
                        validation_result['extra_columns'].append(found_col)
                
                if validation_result['missing_columns']:
                    validation_result['errors'].append(
                        f"Missing required columns: {', '.join(validation_result['missing_columns'])}"
                    )
                
                if validation_result['extra_columns']:
                    validation_result['warnings'].append(
                        f"Extra columns found: {', '.join(validation_result['extra_columns'])}"
                    )
                
        except UnicodeDecodeError as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"CSV file encoding error: {e}")
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Error validating CSV file: {e}")
        
        return validation_result