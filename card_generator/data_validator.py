"""
Data validation and quality assurance module for the database builder.

This module provides comprehensive validation functionality for character data,
including name normalization, numeric validation, image URL validation, and
duplicate detection.
"""

import re
import logging
import requests
from typing import List, Dict, Set, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from .data_models import CharacterData
from .error_handling import ErrorHandler, ErrorCategory, ErrorSeverity


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Result of data validation operations.
    
    Attributes:
        is_valid: Whether the validation passed
        errors: List of validation errors
        warnings: List of validation warnings
        normalized_data: Normalized/corrected data if applicable
        metadata: Additional validation metadata
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    normalized_data: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DuplicateInfo:
    """
    Information about duplicate characters.
    
    Attributes:
        original_index: Index of the original character
        duplicate_indices: List of indices of duplicate characters
        similarity_score: Similarity score between duplicates (0.0 to 1.0)
        duplicate_type: Type of duplication (exact, similar, etc.)
    """
    original_index: int
    duplicate_indices: List[int]
    similarity_score: float
    duplicate_type: str


class DataValidator:
    """
    Comprehensive data validation and quality assurance for character data.
    
    Provides validation for character names, numeric fields, image URLs,
    and duplicate detection with configurable validation rules.
    """
    
    # Valid tier names (case-insensitive)
    VALID_TIERS = {
        'common', 'rare', 'epic', 'legendary', 'mythic', 
        'brainrot god', 'secret', 'og', 'divine', 'celestial'
    }
    
    # Valid variant types
    VALID_VARIANTS = {'standard', 'special', 'limited', 'exclusive'}
    
    # Character name validation patterns
    NAME_PATTERNS = {
        'valid_chars': re.compile(r'^[a-zA-Z0-9\s\-\.\'\(\)&]+$'),
        'excessive_spaces': re.compile(r'\s{2,}'),
        'leading_trailing_space': re.compile(r'^\s+|\s+$'),
        'special_sequences': re.compile(r'[^\w\s]'),
    }
    
    # Numeric validation limits
    NUMERIC_LIMITS = {
        'cost': {'min': 0, 'max': 1000000},
        'income': {'min': 0, 'max': 100000}
    }
    
    def __init__(self, strict_mode: bool = False, timeout: int = 10):
        """
        Initialize the DataValidator.
        
        Args:
            strict_mode: Whether to use strict validation rules
            timeout: Timeout for URL validation requests
        """
        self.strict_mode = strict_mode
        self.timeout = timeout
        self.error_handler = ErrorHandler(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Brainrot Database Validator 1.0'
        })
        
        # Cache for URL validation results
        self._url_cache: Dict[str, bool] = {}
        
        # Statistics tracking
        self.validation_stats = {
            'total_validated': 0,
            'names_normalized': 0,
            'numeric_corrections': 0,
            'url_validations': 0,
            'duplicates_found': 0
        }
    
    def validate_character_list(self, characters: List[CharacterData]) -> ValidationResult:
        """
        Validate a complete list of character data.
        
        Args:
            characters: List of CharacterData objects to validate
            
        Returns:
            ValidationResult with overall validation status
        """
        if not characters:
            return ValidationResult(
                is_valid=False,
                errors=["Character list is empty"]
            )
        
        result = ValidationResult(is_valid=True)
        validated_characters = []
        
        # Validate each character individually
        for i, character in enumerate(characters):
            char_result = self.validate_character(character)
            
            if not char_result.is_valid:
                result.is_valid = False
                for error in char_result.errors:
                    result.errors.append(f"Character {i} ({character.name}): {error}")
            
            # Collect warnings
            for warning in char_result.warnings:
                result.warnings.append(f"Character {i} ({character.name}): {warning}")
            
            # Use normalized data if available
            if char_result.normalized_data:
                validated_characters.append(char_result.normalized_data)
            else:
                validated_characters.append(character)
        
        # Check for duplicates across the entire list
        duplicate_result = self.detect_duplicates(validated_characters)
        if duplicate_result.errors:
            result.is_valid = False
            result.errors.extend(duplicate_result.errors)
        result.warnings.extend(duplicate_result.warnings)
        
        # Store validated characters
        result.normalized_data = validated_characters
        result.metadata = {
            'total_characters': len(characters),
            'validation_stats': self.validation_stats.copy(),
            'duplicate_info': duplicate_result.metadata.get('duplicates', [])
        }
        
        self.validation_stats['total_validated'] += len(characters)
        
        logger.info(f"Validated {len(characters)} characters: "
                   f"{len(result.errors)} errors, {len(result.warnings)} warnings")
        
        return result
    
    def validate_character(self, character: CharacterData) -> ValidationResult:
        """
        Validate a single character's data.
        
        Args:
            character: CharacterData object to validate
            
        Returns:
            ValidationResult for the character
        """
        result = ValidationResult(is_valid=True)
        
        # Create normalized character by copying the original (bypass validation)
        normalized_character = CharacterData.__new__(CharacterData)
        normalized_character.name = character.name
        normalized_character.tier = character.tier
        normalized_character.cost = character.cost
        normalized_character.income = character.income
        normalized_character.variant = character.variant
        normalized_character.image_path = character.image_path
        normalized_character.wiki_url = character.wiki_url
        normalized_character.image_url = character.image_url
        normalized_character.extraction_timestamp = character.extraction_timestamp
        normalized_character.extraction_success = character.extraction_success
        normalized_character.extraction_errors = character.extraction_errors.copy() if character.extraction_errors else []
        
        # Validate and normalize character name
        name_result = self.validate_and_normalize_name(character.name)
        if not name_result.is_valid:
            result.is_valid = False
            result.errors.extend(name_result.errors)
        result.warnings.extend(name_result.warnings)
        
        if name_result.normalized_data:
            normalized_character.name = name_result.normalized_data
            if name_result.normalized_data != character.name:
                self.validation_stats['names_normalized'] += 1
        
        # Validate tier
        tier_result = self.validate_tier(character.tier)
        if not tier_result.is_valid:
            result.is_valid = False
            result.errors.extend(tier_result.errors)
        result.warnings.extend(tier_result.warnings)
        
        if tier_result.normalized_data:
            normalized_character.tier = tier_result.normalized_data
        
        # Validate numeric fields
        cost_result = self.validate_numeric_field(character.cost, 'cost')
        if not cost_result.is_valid:
            result.is_valid = False
            result.errors.extend(cost_result.errors)
        result.warnings.extend(cost_result.warnings)
        
        if cost_result.normalized_data is not None:
            normalized_character.cost = cost_result.normalized_data
            if cost_result.normalized_data != character.cost:
                self.validation_stats['numeric_corrections'] += 1
        
        income_result = self.validate_numeric_field(character.income, 'income')
        if not income_result.is_valid:
            result.is_valid = False
            result.errors.extend(income_result.errors)
        result.warnings.extend(income_result.warnings)
        
        if income_result.normalized_data is not None:
            normalized_character.income = income_result.normalized_data
            if income_result.normalized_data != character.income:
                self.validation_stats['numeric_corrections'] += 1
        
        # Validate variant
        variant_result = self.validate_variant(character.variant)
        if not variant_result.is_valid:
            result.is_valid = False
            result.errors.extend(variant_result.errors)
        result.warnings.extend(variant_result.warnings)
        
        if variant_result.normalized_data:
            normalized_character.variant = variant_result.normalized_data
        
        # Validate image URL if present
        if character.image_url:
            url_result = self.validate_image_url(character.image_url)
            if not url_result.is_valid:
                if self.strict_mode:
                    result.is_valid = False
                    result.errors.extend(url_result.errors)
                else:
                    result.warnings.extend([f"Image URL issue: {error}" for error in url_result.errors])
            result.warnings.extend(url_result.warnings)
        
        # Validate image path if present
        if character.image_path:
            path_result = self.validate_image_path(character.image_path)
            if not path_result.is_valid:
                if self.strict_mode:
                    result.is_valid = False
                    result.errors.extend(path_result.errors)
                else:
                    result.warnings.extend([f"Image path issue: {error}" for error in path_result.errors])
            result.warnings.extend(path_result.warnings)
        
        result.normalized_data = normalized_character
        return result
    
    def validate_and_normalize_name(self, name: str) -> ValidationResult:
        """
        Validate and normalize a character name.
        
        Args:
            name: Character name to validate
            
        Returns:
            ValidationResult with normalized name
        """
        result = ValidationResult(is_valid=True)
        
        if not name or not isinstance(name, str):
            result.is_valid = False
            result.errors.append("Name must be a non-empty string")
            return result
        
        original_name = name
        normalized_name = name
        
        # Remove leading/trailing whitespace
        normalized_name = normalized_name.strip()
        if not normalized_name:
            result.is_valid = False
            result.errors.append("Name cannot be empty after removing whitespace")
            return result
        
        # Normalize excessive whitespace
        if self.NAME_PATTERNS['excessive_spaces'].search(normalized_name):
            normalized_name = re.sub(r'\s+', ' ', normalized_name)
            result.warnings.append("Normalized excessive whitespace in name")
        
        # Check for valid characters
        if not self.NAME_PATTERNS['valid_chars'].match(normalized_name):
            if self.strict_mode:
                result.is_valid = False
                result.errors.append("Name contains invalid characters")
            else:
                # Remove invalid characters
                clean_name = re.sub(r'[^a-zA-Z0-9\s\-\.\'\(\)&]', '', normalized_name)
                if clean_name != normalized_name:
                    normalized_name = clean_name
                    result.warnings.append("Removed invalid characters from name")
        
        # Check name length
        if len(normalized_name) < 2:
            result.is_valid = False
            result.errors.append("Name must be at least 2 characters long")
        elif len(normalized_name) > 50:
            if self.strict_mode:
                result.is_valid = False
                result.errors.append("Name must be 50 characters or less")
            else:
                normalized_name = normalized_name[:50].strip()
                result.warnings.append("Truncated name to 50 characters")
        
        # Check for common naming issues
        if normalized_name.lower() in ['unknown', 'unnamed', 'null', 'none', '']:
            result.warnings.append("Name appears to be a placeholder")
        
        # Check for numeric-only names
        if normalized_name.isdigit():
            result.warnings.append("Name is numeric-only, may be an ID rather than a name")
        
        # Store normalized name if it changed
        if normalized_name != original_name:
            result.normalized_data = normalized_name
        
        return result
    
    def validate_tier(self, tier: str) -> ValidationResult:
        """
        Validate and normalize a character tier.
        
        Args:
            tier: Character tier to validate
            
        Returns:
            ValidationResult with normalized tier
        """
        result = ValidationResult(is_valid=True)
        
        if not tier or not isinstance(tier, str):
            result.is_valid = False
            result.errors.append("Tier must be a non-empty string")
            return result
        
        original_tier = tier
        normalized_tier = tier.strip().lower()
        
        # Check if tier is valid
        if normalized_tier not in self.VALID_TIERS:
            # Try to find a close match
            close_match = self._find_closest_tier(normalized_tier)
            if close_match:
                result.warnings.append(f"Tier '{tier}' normalized to '{close_match}'")
                normalized_tier = close_match
            else:
                if self.strict_mode:
                    result.is_valid = False
                    result.errors.append(f"Invalid tier '{tier}'. Valid tiers: {', '.join(sorted(self.VALID_TIERS))}")
                else:
                    result.warnings.append(f"Unknown tier '{tier}', keeping as-is")
                    normalized_tier = tier.strip()
        
        # Convert back to proper case
        if normalized_tier in self.VALID_TIERS:
            # Convert to title case for consistency
            if normalized_tier == 'brainrot god':
                result.normalized_data = 'Brainrot God'
            elif normalized_tier == 'og':
                result.normalized_data = 'OG'
            else:
                result.normalized_data = normalized_tier.title()
        elif normalized_tier != original_tier:
            result.normalized_data = normalized_tier
        
        return result
    
    def validate_numeric_field(self, value: int, field_name: str) -> ValidationResult:
        """
        Validate a numeric field (cost or income).
        
        Args:
            value: Numeric value to validate
            field_name: Name of the field being validated
            
        Returns:
            ValidationResult with normalized value
        """
        result = ValidationResult(is_valid=True)
        
        if not isinstance(value, (int, float)):
            result.is_valid = False
            result.errors.append(f"{field_name.title()} must be a number")
            return result
        
        # Convert to integer
        normalized_value = int(value)
        
        # Check limits
        limits = self.NUMERIC_LIMITS.get(field_name, {'min': 0, 'max': float('inf')})
        
        if normalized_value < limits['min']:
            if self.strict_mode:
                result.is_valid = False
                result.errors.append(f"{field_name.title()} cannot be less than {limits['min']}")
            else:
                result.warnings.append(f"{field_name.title()} {normalized_value} is below minimum {limits['min']}, setting to minimum")
                normalized_value = limits['min']
        
        if normalized_value > limits['max']:
            if self.strict_mode:
                result.is_valid = False
                result.errors.append(f"{field_name.title()} cannot be greater than {limits['max']}")
            else:
                result.warnings.append(f"{field_name.title()} {normalized_value} exceeds maximum {limits['max']}, setting to maximum")
                normalized_value = limits['max']
        
        # Check for suspicious values
        if field_name == 'cost' and normalized_value == 0:
            result.warnings.append("Cost is 0, which may indicate missing data")
        
        if field_name == 'income' and normalized_value == 0:
            result.warnings.append("Income is 0, which may indicate missing data")
        
        # Check for unrealistic ratios
        if field_name == 'income' and hasattr(self, '_current_cost'):
            if self._current_cost > 0 and normalized_value > 0:
                ratio = normalized_value / self._current_cost
                if ratio > 0.1:  # Income > 10% of cost per second
                    result.warnings.append(f"Income/cost ratio ({ratio:.3f}) seems unusually high")
                elif ratio < 0.001:  # Income < 0.1% of cost per second
                    result.warnings.append(f"Income/cost ratio ({ratio:.6f}) seems unusually low")
        
        if normalized_value != value:
            result.normalized_data = normalized_value
        
        return result
    
    def validate_variant(self, variant: str) -> ValidationResult:
        """
        Validate and normalize a character variant.
        
        Args:
            variant: Character variant to validate
            
        Returns:
            ValidationResult with normalized variant
        """
        result = ValidationResult(is_valid=True)
        
        if not variant or not isinstance(variant, str):
            result.is_valid = False
            result.errors.append("Variant must be a non-empty string")
            return result
        
        normalized_variant = variant.strip().lower()
        
        if normalized_variant not in self.VALID_VARIANTS:
            if self.strict_mode:
                result.is_valid = False
                result.errors.append(f"Invalid variant '{variant}'. Valid variants: {', '.join(sorted(self.VALID_VARIANTS))}")
            else:
                result.warnings.append(f"Unknown variant '{variant}', keeping as-is")
                result.normalized_data = variant.strip()
                return result
        
        # Convert to proper case
        result.normalized_data = normalized_variant.title()
        return result
    
    def validate_image_url(self, url: str) -> ValidationResult:
        """
        Validate an image URL for accessibility and format.
        
        Args:
            url: Image URL to validate
            
        Returns:
            ValidationResult for the URL
        """
        result = ValidationResult(is_valid=True)
        
        if not url or not isinstance(url, str):
            result.is_valid = False
            result.errors.append("Image URL must be a non-empty string")
            return result
        
        url = url.strip()
        
        # Check if URL is cached
        if url in self._url_cache:
            if not self._url_cache[url]:
                result.is_valid = False
                result.errors.append("Image URL is not accessible (cached result)")
            return result
        
        # Basic URL format validation
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                result.is_valid = False
                result.errors.append("Invalid URL format")
                return result
            
            if parsed.scheme not in ['http', 'https']:
                result.is_valid = False
                result.errors.append("URL must use http or https scheme")
        
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"URL parsing error: {str(e)}")
            return result
        
        # Check file extension
        path_lower = parsed.path.lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        if not any(path_lower.endswith(ext) for ext in valid_extensions):
            result.warnings.append("URL does not have a standard image file extension")
        
        # Test URL accessibility
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if content_type and not content_type.startswith('image/'):
                    result.warnings.append(f"URL content-type is '{content_type}', not an image")
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length:
                    try:
                        size = int(content_length)
                        if size < 1024:  # Less than 1KB
                            result.warnings.append("Image appears to be very small (< 1KB)")
                        elif size > 10 * 1024 * 1024:  # Greater than 10MB
                            result.warnings.append("Image appears to be very large (> 10MB)")
                    except ValueError:
                        pass
                
                self._url_cache[url] = True
                self.validation_stats['url_validations'] += 1
                
            elif response.status_code == 404:
                result.is_valid = False
                result.errors.append("Image URL returns 404 (not found)")
                self._url_cache[url] = False
                
            elif response.status_code == 403:
                result.warnings.append("Image URL returns 403 (forbidden), may require authentication")
                self._url_cache[url] = True  # Consider accessible but restricted
                
            else:
                result.warnings.append(f"Image URL returns HTTP {response.status_code}")
                self._url_cache[url] = True  # Consider accessible but with issues
        
        except requests.exceptions.Timeout:
            result.warnings.append("Image URL validation timed out")
            self._url_cache[url] = True  # Don't fail on timeout
            
        except requests.exceptions.RequestException as e:
            result.warnings.append(f"Image URL validation failed: {str(e)}")
            self._url_cache[url] = False
        
        return result
    
    def validate_image_path(self, path: str) -> ValidationResult:
        """
        Validate a local image file path.
        
        Args:
            path: Local image file path to validate
            
        Returns:
            ValidationResult for the path
        """
        result = ValidationResult(is_valid=True)
        
        if not path or not isinstance(path, str):
            result.is_valid = False
            result.errors.append("Image path must be a non-empty string")
            return result
        
        path = path.strip()
        
        try:
            file_path = Path(path)
            
            # Check if file exists
            if not file_path.exists():
                result.warnings.append("Image file does not exist")
            else:
                # Check if it's a file (not directory)
                if not file_path.is_file():
                    result.is_valid = False
                    result.errors.append("Image path points to a directory, not a file")
                    return result
                
                # Check file extension
                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
                if file_path.suffix.lower() not in valid_extensions:
                    result.warnings.append(f"File extension '{file_path.suffix}' is not a standard image format")
                
                # Check file size
                try:
                    size = file_path.stat().st_size
                    if size == 0:
                        result.is_valid = False
                        result.errors.append("Image file is empty")
                    elif size < 1024:  # Less than 1KB
                        result.warnings.append("Image file is very small (< 1KB)")
                    elif size > 10 * 1024 * 1024:  # Greater than 10MB
                        result.warnings.append("Image file is very large (> 10MB)")
                except OSError as e:
                    result.warnings.append(f"Could not check file size: {str(e)}")
        
        except Exception as e:
            result.warnings.append(f"Path validation error: {str(e)}")
        
        return result
    
    def detect_duplicates(self, characters: List[CharacterData]) -> ValidationResult:
        """
        Detect duplicate characters in the list.
        
        Args:
            characters: List of CharacterData objects to check
            
        Returns:
            ValidationResult with duplicate information
        """
        result = ValidationResult(is_valid=True)
        duplicates = []
        
        if len(characters) < 2:
            return result
        
        # Track characters we've already processed
        processed_indices = set()
        
        for i, char1 in enumerate(characters):
            if i in processed_indices:
                continue
            
            duplicate_indices = []
            
            for j, char2 in enumerate(characters[i + 1:], start=i + 1):
                if j in processed_indices:
                    continue
                
                similarity = self._calculate_similarity(char1, char2)
                
                if similarity['is_duplicate']:
                    duplicate_indices.append(j)
                    processed_indices.add(j)
            
            if duplicate_indices:
                # Check the type of duplication for the first duplicate to determine overall type
                first_duplicate_similarity = self._calculate_similarity(char1, characters[duplicate_indices[0]])
                
                duplicate_info = DuplicateInfo(
                    original_index=i,
                    duplicate_indices=duplicate_indices,
                    similarity_score=first_duplicate_similarity['score'],
                    duplicate_type=first_duplicate_similarity['type']
                )
                duplicates.append(duplicate_info)
                
                # Add error or warning
                char_names = [characters[idx].name for idx in [i] + duplicate_indices]
                if first_duplicate_similarity['type'] in ['exact', 'exact_name']:
                    result.errors.append(f"Exact duplicate characters found: {', '.join(char_names)}")
                    result.is_valid = False
                else:
                    result.warnings.append(f"Similar characters found ({first_duplicate_similarity['type']}): {', '.join(char_names)}")
        
        if duplicates:
            self.validation_stats['duplicates_found'] += len(duplicates)
        
        result.metadata['duplicates'] = duplicates
        
        logger.info(f"Duplicate detection: found {len(duplicates)} duplicate groups")
        
        return result
    
    def _calculate_similarity(self, char1: CharacterData, char2: CharacterData) -> Dict[str, Any]:
        """
        Calculate similarity between two characters.
        
        Args:
            char1: First character
            char2: Second character
            
        Returns:
            Dictionary with similarity information
        """
        # Exact name match
        if char1.name.lower().strip() == char2.name.lower().strip():
            return {
                'is_duplicate': True,
                'type': 'exact_name',
                'score': 1.0
            }
        
        # Exact match on all fields
        if (char1.name == char2.name and 
            char1.tier == char2.tier and 
            char1.cost == char2.cost and 
            char1.income == char2.income):
            return {
                'is_duplicate': True,
                'type': 'exact',
                'score': 1.0
            }
        
        # Similar names (fuzzy matching)
        name_similarity = self._calculate_string_similarity(char1.name, char2.name)
        if name_similarity > 0.9:  # 90% similarity threshold
            return {
                'is_duplicate': True,
                'type': 'similar_name',
                'score': name_similarity
            }
        
        # Same stats but different names (possible data entry error)
        if (char1.tier == char2.tier and 
            char1.cost == char2.cost and 
            char1.income == char2.income and
            name_similarity > 0.7):  # Some name similarity required
            return {
                'is_duplicate': True,
                'type': 'same_stats',
                'score': 0.8
            }
        
        return {
            'is_duplicate': False,
            'type': 'unique',
            'score': name_similarity
        }
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein distance.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if str1 == str2:
            return 1.0
        
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        if s1 == s2:
            return 1.0
        
        # Calculate Levenshtein distance
        len1, len2 = len(s1), len(s2)
        
        # Create matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        # Calculate similarity score
        max_len = max(len1, len2)
        distance = matrix[len1][len2]
        similarity = 1.0 - (distance / max_len)
        
        return similarity
    
    def _find_closest_tier(self, tier: str) -> Optional[str]:
        """
        Find the closest valid tier to the given tier string.
        
        Args:
            tier: Tier string to match
            
        Returns:
            Closest valid tier or None if no close match
        """
        tier_lower = tier.lower()
        
        # Direct substring matches
        for valid_tier in self.VALID_TIERS:
            if tier_lower in valid_tier or valid_tier in tier_lower:
                return valid_tier
        
        # Fuzzy matching
        best_match = None
        best_score = 0.0
        
        for valid_tier in self.VALID_TIERS:
            score = self._calculate_string_similarity(tier_lower, valid_tier)
            if score > best_score and score > 0.7:  # 70% similarity threshold
                best_score = score
                best_match = valid_tier
        
        return best_match
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Dictionary with validation statistics
        """
        return {
            'validation_stats': self.validation_stats.copy(),
            'cache_stats': {
                'url_cache_size': len(self._url_cache),
                'cached_valid_urls': sum(1 for v in self._url_cache.values() if v),
                'cached_invalid_urls': sum(1 for v in self._url_cache.values() if not v)
            },
            'validation_rules': {
                'valid_tiers': sorted(self.VALID_TIERS),
                'valid_variants': sorted(self.VALID_VARIANTS),
                'numeric_limits': self.NUMERIC_LIMITS.copy(),
                'strict_mode': self.strict_mode
            }
        }
    
    def close(self):
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()
            logger.debug("DataValidator session closed")