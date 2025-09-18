"""
Unit tests for the DataValidator class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime
from pathlib import Path
import tempfile
import os

from card_generator.data_validator import DataValidator, ValidationResult, DuplicateInfo
from card_generator.data_models import CharacterData


class TestDataValidator(unittest.TestCase):
    """Test cases for DataValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DataValidator(strict_mode=False, timeout=5)
        self.strict_validator = DataValidator(strict_mode=True, timeout=5)
        
        # Sample valid character data
        self.valid_character = CharacterData(
            name="Test Character",
            tier="Common",
            cost=100,
            income=5,
            variant="Standard",
            image_path="images/test.png",
            image_url="https://example.com/test.png"
        )
        
        # Sample invalid character data (bypass validation for testing)
        self.invalid_character = CharacterData.__new__(CharacterData)
        self.invalid_character.name = ""  # Invalid empty name
        self.invalid_character.tier = "InvalidTier"
        self.invalid_character.cost = -10  # Invalid negative cost
        self.invalid_character.income = -5  # Invalid negative income
        self.invalid_character.variant = "InvalidVariant"
        self.invalid_character.image_path = None
        self.invalid_character.wiki_url = None
        self.invalid_character.image_url = None
        self.invalid_character.extraction_timestamp = None
        self.invalid_character.extraction_success = True
        self.invalid_character.extraction_errors = []
    
    def tearDown(self):
        """Clean up after tests."""
        self.validator.close()
        self.strict_validator.close()
    
    def test_validate_character_list_empty(self):
        """Test validation of empty character list."""
        result = self.validator.validate_character_list([])
        
        self.assertFalse(result.is_valid)
        self.assertIn("Character list is empty", result.errors)
    
    def test_validate_character_list_valid(self):
        """Test validation of valid character list."""
        characters = [self.valid_character]
        result = self.validator.validate_character_list(characters)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertIsNotNone(result.normalized_data)
        self.assertEqual(len(result.normalized_data), 1)
    
    def test_validate_character_list_invalid(self):
        """Test validation of invalid character list."""
        characters = [self.invalid_character]
        result = self.validator.validate_character_list(characters)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_validate_character_valid(self):
        """Test validation of valid character."""
        result = self.validator.validate_character(self.valid_character)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertIsNotNone(result.normalized_data)
    
    def test_validate_character_invalid(self):
        """Test validation of invalid character."""
        result = self.validator.validate_character(self.invalid_character)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_validate_and_normalize_name_valid(self):
        """Test name validation with valid names."""
        test_cases = [
            "Valid Name",
            "Character-123",
            "Test (Special)",
            "Name & Co."
        ]
        
        for name in test_cases:
            with self.subTest(name=name):
                result = self.validator.validate_and_normalize_name(name)
                self.assertTrue(result.is_valid, f"Name '{name}' should be valid")
    
    def test_validate_and_normalize_name_normalization(self):
        """Test name normalization."""
        test_cases = [
            ("  Spaced Name  ", "Spaced Name"),  # Trim whitespace
            ("Multiple   Spaces", "Multiple Spaces"),  # Normalize spaces
            ("a" * 60, "a" * 50),  # Truncate long names (non-strict mode)
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.validator.validate_and_normalize_name(input_name)
                if result.normalized_data:
                    self.assertEqual(result.normalized_data, expected)
    
    def test_validate_and_normalize_name_invalid(self):
        """Test name validation with invalid names."""
        test_cases = [
            "",  # Empty string
            "   ",  # Only whitespace
            None,  # None value
            123,  # Non-string
        ]
        
        for name in test_cases:
            with self.subTest(name=name):
                result = self.validator.validate_and_normalize_name(name)
                self.assertFalse(result.is_valid)
    
    def test_validate_and_normalize_name_strict_mode(self):
        """Test name validation in strict mode."""
        # Test invalid characters in strict mode
        result = self.strict_validator.validate_and_normalize_name("Name@#$%")
        self.assertFalse(result.is_valid)
        
        # Test long name in strict mode
        long_name = "a" * 60
        result = self.strict_validator.validate_and_normalize_name(long_name)
        self.assertFalse(result.is_valid)
    
    def test_validate_tier_valid(self):
        """Test tier validation with valid tiers."""
        valid_tiers = ["Common", "Rare", "Epic", "Legendary", "Mythic", "Brainrot God", "Secret", "OG"]
        
        for tier in valid_tiers:
            with self.subTest(tier=tier):
                result = self.validator.validate_tier(tier)
                self.assertTrue(result.is_valid)
    
    def test_validate_tier_normalization(self):
        """Test tier normalization."""
        test_cases = [
            ("common", "Common"),
            ("RARE", "Rare"),
            ("brainrot god", "Brainrot God"),
            ("og", "OG"),
        ]
        
        for input_tier, expected in test_cases:
            with self.subTest(input_tier=input_tier):
                result = self.validator.validate_tier(input_tier)
                self.assertTrue(result.is_valid)
                if result.normalized_data:
                    self.assertEqual(result.normalized_data, expected)
    
    def test_validate_tier_invalid(self):
        """Test tier validation with invalid tiers."""
        result = self.strict_validator.validate_tier("InvalidTier")
        self.assertFalse(result.is_valid)
        
        # Non-strict mode should warn but not fail
        result = self.validator.validate_tier("InvalidTier")
        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.warnings), 0)
    
    def test_validate_numeric_field_valid(self):
        """Test numeric field validation with valid values."""
        test_cases = [
            (100, "cost"),
            (0, "cost"),
            (50, "income"),
            (1000, "cost"),
        ]
        
        for value, field in test_cases:
            with self.subTest(value=value, field=field):
                result = self.validator.validate_numeric_field(value, field)
                self.assertTrue(result.is_valid)
    
    def test_validate_numeric_field_invalid(self):
        """Test numeric field validation with invalid values."""
        test_cases = [
            ("not_a_number", "cost"),
            (None, "income"),
            ([], "cost"),
        ]
        
        for value, field in test_cases:
            with self.subTest(value=value, field=field):
                result = self.validator.validate_numeric_field(value, field)
                self.assertFalse(result.is_valid)
    
    def test_validate_numeric_field_limits(self):
        """Test numeric field validation with limit enforcement."""
        # Test negative values in strict mode
        result = self.strict_validator.validate_numeric_field(-10, "cost")
        self.assertFalse(result.is_valid)
        
        # Test negative values in non-strict mode (should normalize)
        result = self.validator.validate_numeric_field(-10, "cost")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.normalized_data, 0)
        
        # Test very large values
        result = self.strict_validator.validate_numeric_field(2000000, "cost")
        self.assertFalse(result.is_valid)
        
        result = self.validator.validate_numeric_field(2000000, "cost")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.normalized_data, 1000000)  # Max limit
    
    def test_validate_variant_valid(self):
        """Test variant validation with valid variants."""
        valid_variants = ["Standard", "Special", "Limited", "Exclusive"]
        
        for variant in valid_variants:
            with self.subTest(variant=variant):
                result = self.validator.validate_variant(variant)
                self.assertTrue(result.is_valid)
    
    def test_validate_variant_normalization(self):
        """Test variant normalization."""
        test_cases = [
            ("standard", "Standard"),
            ("SPECIAL", "Special"),
            ("limited", "Limited"),
        ]
        
        for input_variant, expected in test_cases:
            with self.subTest(input_variant=input_variant):
                result = self.validator.validate_variant(input_variant)
                self.assertTrue(result.is_valid)
                self.assertEqual(result.normalized_data, expected)
    
    def test_validate_variant_invalid(self):
        """Test variant validation with invalid variants."""
        result = self.strict_validator.validate_variant("InvalidVariant")
        self.assertFalse(result.is_valid)
        
        # Non-strict mode should warn but not fail
        result = self.validator.validate_variant("InvalidVariant")
        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.warnings), 0)
    
    @patch('requests.Session.head')
    def test_validate_image_url_valid(self, mock_head):
        """Test image URL validation with valid URL."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/png', 'content-length': '5000'}
        mock_head.return_value = mock_response
        
        result = self.validator.validate_image_url("https://example.com/image.png")
        
        self.assertTrue(result.is_valid)
        mock_head.assert_called_once()
    
    @patch('requests.Session.head')
    def test_validate_image_url_not_found(self, mock_head):
        """Test image URL validation with 404 response."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        result = self.validator.validate_image_url("https://example.com/missing.png")
        
        self.assertFalse(result.is_valid)
        self.assertIn("404", result.errors[0])
    
    @patch('requests.Session.head')
    def test_validate_image_url_timeout(self, mock_head):
        """Test image URL validation with timeout."""
        # Mock timeout
        mock_head.side_effect = requests.exceptions.Timeout()
        
        result = self.validator.validate_image_url("https://example.com/slow.png")
        
        # Should not fail on timeout, just warn
        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.warnings), 0)
    
    def test_validate_image_url_invalid_format(self):
        """Test image URL validation with invalid URL format."""
        invalid_urls = [
            "not_a_url",
            "ftp://example.com/image.png",  # Wrong scheme
            "",
            None,
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                result = self.validator.validate_image_url(url)
                self.assertFalse(result.is_valid)
    
    def test_validate_image_path_valid(self):
        """Test image path validation with valid path."""
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(b'fake image data')
            tmp_path = tmp_file.name
        
        try:
            result = self.validator.validate_image_path(tmp_path)
            self.assertTrue(result.is_valid)
        finally:
            os.unlink(tmp_path)
    
    def test_validate_image_path_missing_file(self):
        """Test image path validation with missing file."""
        result = self.validator.validate_image_path("/nonexistent/path/image.png")
        
        # Should not fail for missing file, just warn
        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.warnings), 0)
    
    def test_validate_image_path_invalid(self):
        """Test image path validation with invalid paths."""
        invalid_paths = [
            "",
            None,
            123,
        ]
        
        for path in invalid_paths:
            with self.subTest(path=path):
                result = self.validator.validate_image_path(path)
                self.assertFalse(result.is_valid)
    
    def test_detect_duplicates_exact(self):
        """Test duplicate detection with exact duplicates."""
        char1 = CharacterData("Test", "Common", 100, 5, "Standard")
        char2 = CharacterData("Test", "Common", 100, 5, "Standard")  # Exact duplicate
        char3 = CharacterData("Different", "Rare", 200, 10, "Standard")
        
        characters = [char1, char2, char3]
        result = self.validator.detect_duplicates(characters)
        
        self.assertFalse(result.is_valid)  # Should fail due to exact duplicates
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(len(result.metadata['duplicates']), 1)
    
    def test_detect_duplicates_similar_names(self):
        """Test duplicate detection with similar names."""
        char1 = CharacterData("Test Character", "Common", 100, 5, "Standard")
        char2 = CharacterData("Test Charcter", "Common", 150, 7, "Standard")  # Typo in name
        char3 = CharacterData("Different", "Rare", 200, 10, "Standard")
        
        characters = [char1, char2, char3]
        result = self.validator.detect_duplicates(characters)
        
        # Should warn about similar names but not fail
        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.warnings), 0)
        self.assertEqual(len(result.metadata['duplicates']), 1)
    
    def test_detect_duplicates_no_duplicates(self):
        """Test duplicate detection with no duplicates."""
        char1 = CharacterData("Character One", "Common", 100, 5, "Standard")
        char2 = CharacterData("Character Two", "Rare", 200, 10, "Standard")
        char3 = CharacterData("Character Three", "Epic", 300, 15, "Standard")
        
        characters = [char1, char2, char3]
        result = self.validator.detect_duplicates(characters)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.metadata['duplicates']), 0)
    
    def test_calculate_string_similarity(self):
        """Test string similarity calculation."""
        test_cases = [
            ("identical", "identical", 1.0),
            ("", "", 1.0),
            ("test", "test", 1.0),
            ("test", "tset", 0.5),  # 2 swaps in 4 chars
            ("hello", "world", 0.0),  # Completely different
            ("Test Character", "Test Charcter", 0.9),  # One typo
        ]
        
        for str1, str2, expected_min in test_cases:
            with self.subTest(str1=str1, str2=str2):
                similarity = self.validator._calculate_string_similarity(str1, str2)
                if expected_min == 1.0:
                    self.assertEqual(similarity, expected_min)
                else:
                    self.assertGreaterEqual(similarity, expected_min - 0.1)  # Allow some tolerance
    
    def test_find_closest_tier(self):
        """Test finding closest valid tier."""
        test_cases = [
            ("comm", "common"),  # Partial match
            ("legendary", "legendary"),  # Exact match
            ("brain rot god", "brainrot god"),  # Close match
            ("xyz123", None),  # No match
        ]
        
        for input_tier, expected in test_cases:
            with self.subTest(input_tier=input_tier):
                result = self.validator._find_closest_tier(input_tier)
                self.assertEqual(result, expected)
    
    def test_get_validation_statistics(self):
        """Test getting validation statistics."""
        # Perform some validations to generate stats
        self.validator.validate_character(self.valid_character)
        
        stats = self.validator.get_validation_statistics()
        
        self.assertIn('validation_stats', stats)
        self.assertIn('cache_stats', stats)
        self.assertIn('validation_rules', stats)
        self.assertIsInstance(stats['validation_stats']['total_validated'], int)
    
    def test_url_caching(self):
        """Test URL validation caching."""
        url = "https://example.com/test.png"
        
        with patch('requests.Session.head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'image/png'}
            mock_head.return_value = mock_response
            
            # First call should make HTTP request
            result1 = self.validator.validate_image_url(url)
            self.assertTrue(result1.is_valid)
            self.assertEqual(mock_head.call_count, 1)
            
            # Second call should use cache
            result2 = self.validator.validate_image_url(url)
            self.assertTrue(result2.is_valid)
            self.assertEqual(mock_head.call_count, 1)  # No additional calls
    
    def test_validation_with_extraction_errors(self):
        """Test validation of character with extraction errors."""
        character = CharacterData(
            name="Test Character",
            tier="Common",
            cost=100,
            income=5,
            variant="Standard"
        )
        character.extraction_success = False
        character.extraction_errors = ["Failed to extract cost", "Image not found"]
        
        result = self.validator.validate_character(character)
        
        # Should still validate the character data itself
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.normalized_data)


if __name__ == '__main__':
    unittest.main()