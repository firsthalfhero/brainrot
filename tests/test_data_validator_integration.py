"""
Integration tests for the DataValidator class.
"""

import unittest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from card_generator.data_validator import DataValidator
from card_generator.data_models import CharacterData


class TestDataValidatorIntegration(unittest.TestCase):
    """Integration test cases for DataValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DataValidator(strict_mode=False, timeout=10)
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample character data with various issues
        self.test_characters = [
            # Valid character
            CharacterData(
                name="Fluriflura",
                tier="Common",
                cost=100,
                income=5,
                variant="Standard",
                image_url="https://static.wikia.nocookie.net/stealabrainrot/images/test.png"
            ),
            
            # Character with name normalization needed
            CharacterData(
                name="  Test   Character  ",  # Extra spaces
                tier="rare",  # Wrong case
                cost=200,
                income=10,
                variant="standard"  # Wrong case
            ),
            
            # Character with numeric issues (bypass validation for testing)
            self._create_test_character(
                name="Expensive Character",
                tier="Legendary",
                cost=-50,  # Negative cost (should be normalized)
                income=2000000,  # Too high income (should be capped)
                variant="Special"
            ),
            
            # Character with invalid tier (should be handled gracefully)
            CharacterData(
                name="Unknown Tier Character",
                tier="SuperRare",  # Invalid tier
                cost=300,
                income=15,
                variant="Standard"
            ),
            
            # Duplicate character (exact)
            CharacterData(
                name="Fluriflura",
                tier="Common",
                cost=100,
                income=5,
                variant="Standard"
            ),
            
            # Similar character (potential duplicate)
            CharacterData(
                name="Fluriflora",  # Similar name
                tier="Common",
                cost=100,
                income=5,
                variant="Standard"
            ),
            
            # Character with problematic name (bypass validation for testing)
            self._create_test_character(
                name="Character@#$%^&*()",  # Special characters
                tier="Epic",
                cost=500,
                income=25,
                variant="Standard"
            ),
            
            # Character with missing/empty fields
            CharacterData(
                name="Minimal Character",
                tier="Common",
                cost=0,  # Zero cost (suspicious)
                income=0,  # Zero income (suspicious)
                variant="Standard"
            )
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        self.validator.close()
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_character(self, name, tier, cost, income, variant, **kwargs):
        """Create a test character bypassing validation."""
        char = CharacterData.__new__(CharacterData)
        char.name = name
        char.tier = tier
        char.cost = cost
        char.income = income
        char.variant = variant
        char.image_path = kwargs.get('image_path')
        char.wiki_url = kwargs.get('wiki_url')
        char.image_url = kwargs.get('image_url')
        char.extraction_timestamp = kwargs.get('extraction_timestamp')
        char.extraction_success = kwargs.get('extraction_success', True)
        char.extraction_errors = kwargs.get('extraction_errors', [])
        return char
    
    def test_comprehensive_character_list_validation(self):
        """Test comprehensive validation of a character list with various issues."""
        result = self.validator.validate_character_list(self.test_characters)
        
        # Should have some validation issues but not necessarily fail completely
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.normalized_data)
        
        # Check that we have the same number of characters
        self.assertEqual(len(result.normalized_data), len(self.test_characters))
        
        # Should have found duplicates
        self.assertGreater(len(result.metadata.get('duplicate_info', [])), 0)
        
        # Should have some warnings
        self.assertGreater(len(result.warnings), 0)
        
        # Print results for manual inspection
        print(f"\nValidation Results:")
        print(f"Valid: {result.is_valid}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"Duplicates found: {len(result.metadata.get('duplicate_info', []))}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings[:5]:  # Show first 5 warnings
                print(f"  - {warning}")
    
    def test_name_normalization_integration(self):
        """Test name normalization across multiple characters."""
        characters_with_name_issues = [
            CharacterData("  Spaced Name  ", "Common", 100, 5, "Standard"),
            CharacterData("Multiple   Spaces   Here", "Rare", 200, 10, "Standard"),
            self._create_test_character("Name@#$%", "Epic", 300, 15, "Standard"),
            self._create_test_character("a" * 60, "Legendary", 400, 20, "Standard"),  # Too long
            CharacterData("123", "Common", 50, 2, "Standard"),  # Numeric only
        ]
        
        result = self.validator.validate_character_list(characters_with_name_issues)
        
        # Check that names were normalized
        normalized_characters = result.normalized_data
        self.assertIsNotNone(normalized_characters)
        
        # First character should have trimmed spaces
        self.assertEqual(normalized_characters[0].name, "Spaced Name")
        
        # Second character should have normalized spaces
        self.assertEqual(normalized_characters[1].name, "Multiple Spaces Here")
        
        # Fourth character should be truncated (in non-strict mode)
        self.assertLessEqual(len(normalized_characters[3].name), 50)
        
        # Should have warnings about name issues
        self.assertGreater(len(result.warnings), 0)
        
        print(f"\nName normalization results:")
        for i, (original, normalized) in enumerate(zip(characters_with_name_issues, normalized_characters)):
            if original.name != normalized.name:
                print(f"  {i}: '{original.name}' -> '{normalized.name}'")
    
    def test_numeric_validation_integration(self):
        """Test numeric field validation and normalization."""
        characters_with_numeric_issues = [
            self._create_test_character("Negative Cost", "Common", -100, 5, "Standard"),
            self._create_test_character("Negative Income", "Rare", 200, -10, "Standard"),
            CharacterData("Zero Values", "Epic", 0, 0, "Standard"),
            self._create_test_character("High Values", "Legendary", 2000000, 500000, "Standard"),
            self._create_test_character("Float Values", "Common", 100.5, 5.7, "Standard"),
        ]
        
        result = self.validator.validate_character_list(characters_with_numeric_issues)
        normalized_characters = result.normalized_data
        
        # Check numeric normalizations
        self.assertGreaterEqual(normalized_characters[0].cost, 0)  # Negative cost fixed
        self.assertGreaterEqual(normalized_characters[1].income, 0)  # Negative income fixed
        self.assertLessEqual(normalized_characters[3].cost, 1000000)  # High cost capped
        self.assertLessEqual(normalized_characters[3].income, 100000)  # High income capped
        
        # Float values should be converted to integers
        self.assertIsInstance(normalized_characters[4].cost, int)
        self.assertIsInstance(normalized_characters[4].income, int)
        
        # Should have warnings about numeric issues
        self.assertGreater(len(result.warnings), 0)
        
        print(f"\nNumeric validation results:")
        for i, (original, normalized) in enumerate(zip(characters_with_numeric_issues, normalized_characters)):
            if original.cost != normalized.cost or original.income != normalized.income:
                print(f"  {i}: Cost {original.cost} -> {normalized.cost}, Income {original.income} -> {normalized.income}")
    
    def test_tier_validation_integration(self):
        """Test tier validation and normalization."""
        characters_with_tier_issues = [
            CharacterData("Lower Case", "common", 100, 5, "Standard"),
            CharacterData("Upper Case", "RARE", 200, 10, "Standard"),
            CharacterData("Mixed Case", "ePiC", 300, 15, "Standard"),
            CharacterData("Brainrot God", "brainrot god", 400, 20, "Standard"),
            CharacterData("OG Character", "og", 500, 25, "Standard"),
            CharacterData("Invalid Tier", "SuperLegendary", 600, 30, "Standard"),
            CharacterData("Close Match", "Legandary", 700, 35, "Standard"),  # Typo
        ]
        
        result = self.validator.validate_character_list(characters_with_tier_issues)
        normalized_characters = result.normalized_data
        
        # Check tier normalizations
        self.assertEqual(normalized_characters[0].tier, "Common")
        self.assertEqual(normalized_characters[1].tier, "Rare")
        self.assertEqual(normalized_characters[2].tier, "Epic")
        self.assertEqual(normalized_characters[3].tier, "Brainrot God")
        self.assertEqual(normalized_characters[4].tier, "OG")
        
        # Close match should be corrected
        self.assertEqual(normalized_characters[6].tier, "Legendary")
        
        print(f"\nTier validation results:")
        for i, (original, normalized) in enumerate(zip(characters_with_tier_issues, normalized_characters)):
            if original.tier != normalized.tier:
                print(f"  {i}: '{original.tier}' -> '{normalized.tier}'")
    
    def test_duplicate_detection_integration(self):
        """Test comprehensive duplicate detection."""
        characters_with_duplicates = [
            # Exact duplicates
            CharacterData("Exact Duplicate", "Common", 100, 5, "Standard"),
            CharacterData("Exact Duplicate", "Common", 100, 5, "Standard"),
            
            # Similar names
            CharacterData("Similar Name", "Rare", 200, 10, "Standard"),
            CharacterData("Similar Nme", "Rare", 200, 10, "Standard"),  # Typo
            
            # Same stats, different names
            CharacterData("Character A", "Epic", 300, 15, "Standard"),
            CharacterData("Character B", "Epic", 300, 15, "Standard"),
            
            # Unique characters
            CharacterData("Unique One", "Legendary", 400, 20, "Standard"),
            CharacterData("Unique Two", "Mythic", 500, 25, "Standard"),
        ]
        
        result = self.validator.validate_character_list(characters_with_duplicates)
        
        # Should find duplicates
        duplicates = result.metadata.get('duplicate_info', [])
        self.assertGreater(len(duplicates), 0)
        
        # Should have errors for exact duplicates
        exact_duplicate_errors = [error for error in result.errors if "Exact duplicate" in error]
        self.assertGreater(len(exact_duplicate_errors), 0)
        
        # Should have warnings for similar characters
        similar_warnings = [warning for warning in result.warnings if "Similar characters" in warning]
        self.assertGreater(len(similar_warnings), 0)
        
        print(f"\nDuplicate detection results:")
        print(f"Duplicate groups found: {len(duplicates)}")
        for i, dup in enumerate(duplicates):
            print(f"  Group {i}: Original index {dup.original_index}, "
                  f"Duplicates {dup.duplicate_indices}, Type: {dup.duplicate_type}")
    
    def test_image_path_validation_integration(self):
        """Test image path validation with real files."""
        # Create temporary image files
        valid_image = Path(self.temp_dir) / "valid_image.png"
        valid_image.write_bytes(b"fake png data")
        
        empty_image = Path(self.temp_dir) / "empty_image.png"
        empty_image.write_bytes(b"")
        
        characters_with_image_paths = [
            CharacterData("Valid Image", "Common", 100, 5, "Standard", image_path=str(valid_image)),
            CharacterData("Missing Image", "Rare", 200, 10, "Standard", image_path="/nonexistent/image.png"),
            CharacterData("Empty Image", "Epic", 300, 15, "Standard", image_path=str(empty_image)),
            CharacterData("No Extension", "Legendary", 400, 20, "Standard", image_path=str(Path(self.temp_dir) / "no_ext")),
            CharacterData("No Image Path", "Common", 100, 5, "Standard"),
        ]
        
        result = self.validator.validate_character_list(characters_with_image_paths)
        
        # Should have warnings about image issues
        image_warnings = [warning for warning in result.warnings if "image" in warning.lower()]
        self.assertGreater(len(image_warnings), 0)
        
        print(f"\nImage path validation results:")
        print(f"Image-related warnings: {len(image_warnings)}")
        for warning in image_warnings:
            print(f"  - {warning}")
    
    def test_validation_statistics_integration(self):
        """Test validation statistics collection."""
        # Perform various validations
        result = self.validator.validate_character_list(self.test_characters)
        
        # Get statistics
        stats = self.validator.get_validation_statistics()
        
        # Check that statistics were collected
        self.assertGreater(stats['validation_stats']['total_validated'], 0)
        
        # Should have some normalizations
        total_normalizations = (
            stats['validation_stats']['names_normalized'] +
            stats['validation_stats']['numeric_corrections']
        )
        self.assertGreater(total_normalizations, 0)
        
        # Should have found duplicates
        self.assertGreater(stats['validation_stats']['duplicates_found'], 0)
        
        print(f"\nValidation statistics:")
        for key, value in stats['validation_stats'].items():
            print(f"  {key}: {value}")
        
        print(f"\nCache statistics:")
        for key, value in stats['cache_stats'].items():
            print(f"  {key}: {value}")
    
    def test_strict_vs_non_strict_mode(self):
        """Test differences between strict and non-strict validation modes."""
        problematic_character = CharacterData(
            name="Character@#$%",  # Invalid characters
            tier="InvalidTier",   # Invalid tier
            cost=-100,           # Negative cost
            income=2000000,      # Too high income
            variant="InvalidVariant"  # Invalid variant
        )
        
        # Test non-strict mode
        non_strict_result = self.validator.validate_character(problematic_character)
        
        # Test strict mode
        strict_validator = DataValidator(strict_mode=True)
        try:
            strict_result = strict_validator.validate_character(problematic_character)
            
            # Strict mode should have more errors
            self.assertGreaterEqual(len(strict_result.errors), len(non_strict_result.errors))
            
            # Non-strict mode should have more warnings (issues converted to warnings)
            self.assertGreaterEqual(len(non_strict_result.warnings), len(strict_result.warnings))
            
            print(f"\nStrict vs Non-strict comparison:")
            print(f"Non-strict - Errors: {len(non_strict_result.errors)}, Warnings: {len(non_strict_result.warnings)}")
            print(f"Strict - Errors: {len(strict_result.errors)}, Warnings: {len(strict_result.warnings)}")
            
        finally:
            strict_validator.close()
    
    def test_real_world_data_simulation(self):
        """Test with data that simulates real-world scraping results."""
        real_world_characters = [
            # Good data
            CharacterData("Fluriflura", "Common", 100, 5, "Standard"),
            CharacterData("Tralalero Tralala", "Rare", 250, 12, "Standard"),
            
            # Data with extraction issues
            CharacterData("Partial Data", "Epic", 0, 0, "Standard"),  # Missing numeric data
            CharacterData("", "Common", 100, 5, "Standard"),  # Missing name
            
            # Data with formatting issues
            CharacterData("  UPPERCASE NAME  ", "LEGENDARY", 500, 25, "STANDARD"),
            CharacterData("name with numbers 123", "mythic", 750, 37, "special"),
            
            # Suspicious data
            CharacterData("Test Character", "Common", 1, 1000, "Standard"),  # Unrealistic ratio
            CharacterData("Duplicate Name", "Rare", 200, 10, "Standard"),
            CharacterData("Duplicate Name", "Rare", 200, 10, "Standard"),
        ]
        
        # Add extraction metadata to simulate real scraping
        for i, char in enumerate(real_world_characters):
            char.extraction_timestamp = datetime.now()
            if i in [2, 3]:  # Simulate extraction failures
                char.extraction_success = False
                char.extraction_errors = ["Failed to parse infobox", "Missing data"]
            else:
                char.extraction_success = True
        
        result = self.validator.validate_character_list(real_world_characters)
        
        # Should handle the mixed data gracefully
        self.assertIsNotNone(result.normalized_data)
        
        # Should have found various issues
        self.assertGreater(len(result.warnings), 0)
        
        # Should have normalized the data
        normalized = result.normalized_data
        self.assertEqual(normalized[4].name, "UPPERCASE NAME")  # Trimmed spaces
        self.assertEqual(normalized[4].tier, "Legendary")  # Normalized case
        self.assertEqual(normalized[5].tier, "Mythic")  # Normalized case
        
        print(f"\nReal-world simulation results:")
        print(f"Characters processed: {len(real_world_characters)}")
        print(f"Validation successful: {result.is_valid}")
        print(f"Issues found: {len(result.errors)} errors, {len(result.warnings)} warnings")
        
        # Show some normalized data
        print(f"\nSample normalizations:")
        for i, (original, normalized) in enumerate(zip(real_world_characters[:3], normalized[:3])):
            if (original.name != normalized.name or 
                original.tier != normalized.tier or 
                original.variant != normalized.variant):
                print(f"  Character {i}:")
                print(f"    Name: '{original.name}' -> '{normalized.name}'")
                print(f"    Tier: '{original.tier}' -> '{normalized.tier}'")
                print(f"    Variant: '{original.variant}' -> '{normalized.variant}'")


if __name__ == '__main__':
    unittest.main()