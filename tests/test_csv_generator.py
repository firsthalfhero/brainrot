"""
Unit tests for the CSVGenerator class.
"""

import unittest
import tempfile
import shutil
import csv
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open

from card_generator.csv_generator import CSVGenerator
from card_generator.config import DatabaseBuilderConfig
from card_generator.data_models import CharacterData


class TestCSVGenerator(unittest.TestCase):
    """Test cases for CSVGenerator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configuration
        self.config = DatabaseBuilderConfig(
            output_dir=self.temp_dir,
            include_timestamp=False,
            csv_filename_template="test_database.csv"
        )
        
        # Create CSVGenerator instance
        self.csv_generator = CSVGenerator(self.config)
        
        # Create test character data
        self.test_characters = [
            CharacterData(
                name="Test Character 1",
                tier="Common",
                cost=100,
                income=5,
                variant="Standard",
                image_path="images/Test_Character_1.png"
            ),
            CharacterData(
                name="Test Character 2",
                tier="Rare",
                cost=500,
                income=25,
                variant="Standard",
                image_path="images/Test_Character_2.png"
            ),
            CharacterData(
                name="Special Character",
                tier="Epic",
                cost=1000,
                income=50,
                variant="Special",
                image_path=None  # No image
            )
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_default_config(self):
        """Test CSVGenerator initialization with default config."""
        generator = CSVGenerator()
        self.assertIsInstance(generator.config, DatabaseBuilderConfig)
        self.assertIsNotNone(generator.output_manager)
        self.assertIsNotNone(generator.error_handler)
    
    def test_init_custom_config(self):
        """Test CSVGenerator initialization with custom config."""
        generator = CSVGenerator(self.config)
        self.assertEqual(generator.config.output_dir, self.temp_dir)
        self.assertFalse(generator.config.include_timestamp)
    
    def test_create_csv_headers(self):
        """Test CSV header creation."""
        headers = self.csv_generator._create_csv_headers()
        expected_headers = [
            'Character Name',
            'Tier',
            'Cost',
            'Income per Second',
            'Variant Type',
            'Image Path'
        ]
        self.assertEqual(headers, expected_headers)
    
    def test_character_to_csv_row(self):
        """Test character data to CSV row conversion."""
        character = self.test_characters[0]
        row = self.csv_generator._character_to_csv_row(character)
        expected_row = [
            "Test Character 1",
            "Common",
            "100",
            "5",
            "Standard",
            "images/Test_Character_1.png"
        ]
        self.assertEqual(row, expected_row)
    
    def test_character_to_csv_row_no_image(self):
        """Test character data to CSV row conversion with no image."""
        character = self.test_characters[2]  # Has no image_path
        row = self.csv_generator._character_to_csv_row(character)
        expected_row = [
            "Special Character",
            "Epic",
            "1000",
            "50",
            "Special",
            ""  # Empty string for no image
        ]
        self.assertEqual(row, expected_row)
    
    def test_generate_filename_no_timestamp(self):
        """Test filename generation without timestamp."""
        filename = self.csv_generator._generate_filename()
        self.assertEqual(filename, "test_database.csv")
    
    def test_generate_filename_with_timestamp(self):
        """Test filename generation with timestamp."""
        config = DatabaseBuilderConfig(
            include_timestamp=True,
            csv_filename_template="database_{timestamp}.csv"
        )
        generator = CSVGenerator(config)
        
        with patch('card_generator.csv_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250115_143000"
            filename = generator._generate_filename()
            self.assertEqual(filename, "database_20250115_143000.csv")
    
    def test_validate_character_data_valid(self):
        """Test character data validation with valid data."""
        # Should not raise any exception
        self.csv_generator._validate_character_data(self.test_characters)
    
    def test_validate_character_data_empty_list(self):
        """Test character data validation with empty list."""
        # Empty list should not raise error in _validate_character_data
        # The error is raised in generate_csv instead
        self.csv_generator._validate_character_data([])
    
    def test_validate_character_data_invalid_type(self):
        """Test character data validation with invalid type."""
        with self.assertRaises(ValueError) as context:
            self.csv_generator._validate_character_data(["not a character"])
        self.assertIn("not a CharacterData object", str(context.exception))
    
    def test_validate_character_data_empty_name(self):
        """Test character data validation with empty name."""
        # CharacterData validation happens in __post_init__, so we can't create invalid objects
        # Test that CharacterData itself raises the error
        with self.assertRaises(ValueError) as context:
            CharacterData(
                name="",
                tier="Common",
                cost=100,
                income=5,
                variant="Standard"
            )
        self.assertIn("non-empty string", str(context.exception))
    
    def test_validate_character_data_empty_tier(self):
        """Test character data validation with empty tier."""
        # CharacterData validation happens in __post_init__, so we can't create invalid objects
        # Test that CharacterData itself raises the error
        with self.assertRaises(ValueError) as context:
            CharacterData(
                name="Test",
                tier="",
                cost=100,
                income=5,
                variant="Standard"
            )
        self.assertIn("non-empty string", str(context.exception))
    
    def test_validate_character_data_negative_cost(self):
        """Test character data validation with negative cost."""
        # CharacterData validation happens in __post_init__, so we can't create invalid objects
        # Test that CharacterData itself raises the error
        with self.assertRaises(ValueError) as context:
            CharacterData(
                name="Test",
                tier="Common",
                cost=-100,
                income=5,
                variant="Standard"
            )
        self.assertIn("non-negative integer", str(context.exception))
    
    def test_validate_character_data_negative_income(self):
        """Test character data validation with negative income."""
        # CharacterData validation happens in __post_init__, so we can't create invalid objects
        # Test that CharacterData itself raises the error
        with self.assertRaises(ValueError) as context:
            CharacterData(
                name="Test",
                tier="Common",
                cost=100,
                income=-5,
                variant="Standard"
            )
        self.assertIn("non-negative integer", str(context.exception))
    
    def test_generate_csv_success(self):
        """Test successful CSV generation."""
        csv_path = self.csv_generator.generate_csv(self.test_characters)
        
        # Check file was created
        self.assertTrue(os.path.exists(csv_path))
        
        # Check file content
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Check headers
            headers = next(reader)
            expected_headers = self.csv_generator._create_csv_headers()
            self.assertEqual(headers, expected_headers)
            
            # Check data rows
            rows = list(reader)
            self.assertEqual(len(rows), 3)
            
            # Check first character
            self.assertEqual(rows[0][0], "Test Character 1")
            self.assertEqual(rows[0][1], "Common")
            self.assertEqual(rows[0][2], "100")
            self.assertEqual(rows[0][3], "5")
            self.assertEqual(rows[0][4], "Standard")
            self.assertEqual(rows[0][5], "images/Test_Character_1.png")
            
            # Check character with no image
            self.assertEqual(rows[2][0], "Special Character")
            self.assertEqual(rows[2][5], "")  # Empty image path
    
    def test_generate_csv_empty_list(self):
        """Test CSV generation with empty character list."""
        with self.assertRaises(ValueError) as context:
            self.csv_generator.generate_csv([])
        self.assertIn("empty character list", str(context.exception))
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_generate_csv_permission_error(self, mock_open):
        """Test CSV generation with permission error."""
        with self.assertRaises(IOError) as context:
            self.csv_generator.generate_csv(self.test_characters)
        self.assertIn("Permission denied", str(context.exception))
    
    @patch('builtins.open', side_effect=OSError(28, "No space left on device"))
    def test_generate_csv_disk_full(self, mock_open):
        """Test CSV generation with disk full error."""
        with self.assertRaises(IOError) as context:
            self.csv_generator.generate_csv(self.test_characters)
        self.assertIn("Disk full", str(context.exception))
    
    def test_append_to_existing_csv(self):
        """Test appending to existing CSV file."""
        # First create a CSV file
        csv_path = self.csv_generator.generate_csv(self.test_characters[:2])
        
        # Create additional character
        additional_character = [CharacterData(
            name="Additional Character",
            tier="Legendary",
            cost=2000,
            income=100,
            variant="Standard",
            image_path="images/Additional_Character.png"
        )]
        
        # Append to existing file
        updated_path = self.csv_generator.append_to_existing_csv(additional_character, csv_path)
        self.assertEqual(updated_path, csv_path)
        
        # Check file content
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip headers
            rows = list(reader)
            self.assertEqual(len(rows), 3)  # 2 original + 1 appended
            
            # Check appended character
            self.assertEqual(rows[2][0], "Additional Character")
            self.assertEqual(rows[2][1], "Legendary")
    
    def test_append_to_nonexistent_csv(self):
        """Test appending to non-existent CSV file."""
        with self.assertRaises(ValueError) as context:
            self.csv_generator.append_to_existing_csv(
                self.test_characters, 
                "nonexistent.csv"
            )
        self.assertIn("does not exist", str(context.exception))
    
    def test_append_empty_list(self):
        """Test appending empty character list."""
        csv_path = self.csv_generator.generate_csv(self.test_characters)
        
        with self.assertRaises(ValueError) as context:
            self.csv_generator.append_to_existing_csv([], csv_path)
        self.assertIn("empty character list", str(context.exception))
    
    def test_validate_csv_format_valid(self):
        """Test CSV format validation with valid file."""
        csv_path = self.csv_generator.generate_csv(self.test_characters)
        result = self.csv_generator.validate_csv_format(csv_path)
        self.assertTrue(result)
    
    def test_validate_csv_format_nonexistent(self):
        """Test CSV format validation with non-existent file."""
        with self.assertRaises(IOError) as context:
            self.csv_generator.validate_csv_format("nonexistent.csv")
        self.assertIn("does not exist", str(context.exception))
    
    def test_validate_csv_format_empty_file(self):
        """Test CSV format validation with empty file."""
        empty_csv = Path(self.temp_dir) / "empty.csv"
        empty_csv.write_text("")
        
        with self.assertRaises(ValueError) as context:
            self.csv_generator.validate_csv_format(str(empty_csv))
        self.assertIn("empty or has no headers", str(context.exception))
    
    def test_validate_csv_format_wrong_headers(self):
        """Test CSV format validation with wrong headers."""
        wrong_csv = Path(self.temp_dir) / "wrong.csv"
        with open(wrong_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Wrong", "Headers"])
            writer.writerow(["Data", "Row"])
        
        with self.assertRaises(ValueError) as context:
            self.csv_generator.validate_csv_format(str(wrong_csv))
        self.assertIn("Invalid CSV headers", str(context.exception))
    
    def test_validate_csv_format_no_data(self):
        """Test CSV format validation with headers but no data."""
        headers_only_csv = Path(self.temp_dir) / "headers_only.csv"
        with open(headers_only_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.csv_generator._create_csv_headers())
        
        with self.assertRaises(ValueError) as context:
            self.csv_generator.validate_csv_format(str(headers_only_csv))
        self.assertIn("no data rows", str(context.exception))
    
    def test_get_csv_statistics(self):
        """Test CSV statistics generation."""
        csv_path = self.csv_generator.generate_csv(self.test_characters)
        stats = self.csv_generator.get_csv_statistics(csv_path)
        
        # Check basic statistics
        self.assertEqual(stats['file_path'], csv_path)
        self.assertGreater(stats['file_size'], 0)
        self.assertEqual(stats['total_characters'], 3)
        self.assertEqual(stats['characters_with_images'], 2)
        self.assertEqual(stats['characters_without_images'], 1)
        
        # Check tier breakdown
        expected_tiers = {'Common': 1, 'Rare': 1, 'Epic': 1}
        self.assertEqual(stats['characters_by_tier'], expected_tiers)
        
        # Check timestamps
        self.assertIsInstance(stats['creation_time'], datetime)
        self.assertIsInstance(stats['modification_time'], datetime)
    
    def test_get_csv_statistics_nonexistent(self):
        """Test CSV statistics with non-existent file."""
        with self.assertRaises(IOError) as context:
            self.csv_generator.get_csv_statistics("nonexistent.csv")
        self.assertIn("does not exist", str(context.exception))
    
    @patch('card_generator.csv_generator.Path.mkdir', side_effect=PermissionError("Permission denied"))
    def test_ensure_output_directory_permission_error(self, mock_mkdir):
        """Test output directory creation with permission error."""
        with self.assertRaises(IOError) as context:
            CSVGenerator(self.config)
        self.assertIn("Permission denied", str(context.exception))
    
    def test_ensure_output_directory_success(self):
        """Test successful output directory creation."""
        # Create a new temp directory that doesn't exist yet
        new_temp_dir = os.path.join(self.temp_dir, "new_subdir")
        config = DatabaseBuilderConfig(output_dir=new_temp_dir)
        
        # Should create directory without error
        generator = CSVGenerator(config)
        self.assertTrue(os.path.exists(new_temp_dir))


if __name__ == '__main__':
    unittest.main()