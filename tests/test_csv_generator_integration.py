"""
Integration tests for the CSVGenerator class.
"""

import unittest
import tempfile
import shutil
import csv
import os
from pathlib import Path
from datetime import datetime

from card_generator.csv_generator import CSVGenerator
from card_generator.config import DatabaseBuilderConfig
from card_generator.data_models import CharacterData
from card_generator.data_loader import CSVDataLoader


class TestCSVGeneratorIntegration(unittest.TestCase):
    """Integration test cases for CSVGenerator with existing system components."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configuration
        self.config = DatabaseBuilderConfig(
            output_dir=self.temp_dir,
            include_timestamp=True,
            csv_filename_template="brainrot_database_{timestamp}.csv"
        )
        
        # Create CSVGenerator instance
        self.csv_generator = CSVGenerator(self.config)
        
        # Create test character data that matches real data structure
        self.test_characters = [
            CharacterData(
                name="Fluriflura",
                tier="Common",
                cost=100,
                income=5,
                variant="Standard",
                image_path="images/Fluriflura.png"
            ),
            CharacterData(
                name="Gangster Footera",
                tier="Rare",
                cost=500,
                income=25,
                variant="Standard",
                image_path="images/Gangster_Footera.png"
            ),
            CharacterData(
                name="Cappuccino Assassino",
                tier="Epic",
                cost=1000,
                income=50,
                variant="Standard",
                image_path="images/Cappuccino_Assassino.png"
            ),
            CharacterData(
                name="Lionel Cactuseli",
                tier="Legendary",
                cost=2500,
                income=125,
                variant="Standard",
                image_path="images/Lionel_Cactuseli.png"
            ),
            CharacterData(
                name="Matteo",
                tier="Mythic",
                cost=5000,
                income=250,
                variant="Standard",
                image_path="images/Matteo.png"
            )
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_csv_compatible_with_data_loader(self):
        """Test that generated CSV is compatible with existing CSVDataLoader."""
        # Generate CSV file
        csv_path = self.csv_generator.generate_csv(self.test_characters)
        
        # Verify file exists
        self.assertTrue(os.path.exists(csv_path))
        
        # Try to load the generated CSV with existing CSVDataLoader
        data_loader = CSVDataLoader(csv_path)
        loaded_characters = data_loader.load_characters()
        
        # Verify all characters were loaded correctly
        self.assertEqual(len(loaded_characters), len(self.test_characters))
        
        # Check character data matches
        for original, loaded in zip(self.test_characters, loaded_characters):
            self.assertEqual(original.name, loaded.name)
            self.assertEqual(original.tier, loaded.tier)
            self.assertEqual(original.cost, loaded.cost)
            self.assertEqual(original.income, loaded.income)
            self.assertEqual(original.variant, loaded.variant)
            # Note: CSVDataLoader searches for images in filesystem, not from CSV Image Path column
            # So loaded.image_path will be None unless actual image files exist
    
    def test_csv_format_matches_existing_database(self):
        """Test that generated CSV format matches existing database structure."""
        # Generate CSV file
        csv_path = self.csv_generator.generate_csv(self.test_characters)
        
        # Read and verify CSV structure
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Check headers match expected format
            headers = next(reader)
            expected_headers = [
                'Character Name',
                'Tier',
                'Cost',
                'Income per Second',
                'Variant Type',
                'Image Path'
            ]
            self.assertEqual(headers, expected_headers)
            
            # Check data format
            rows = list(reader)
            self.assertEqual(len(rows), 5)
            
            # Verify first row format
            first_row = rows[0]
            self.assertEqual(first_row[0], "Fluriflura")  # Character Name
            self.assertEqual(first_row[1], "Common")      # Tier
            self.assertEqual(first_row[2], "100")         # Cost (as string)
            self.assertEqual(first_row[3], "5")           # Income per Second (as string)
            self.assertEqual(first_row[4], "Standard")    # Variant Type
            self.assertEqual(first_row[5], "images/Fluriflura.png")  # Image Path
    
    def test_timestamp_filename_generation(self):
        """Test that timestamp-based filenames are generated correctly."""
        # Generate CSV file
        csv_path = self.csv_generator.generate_csv(self.test_characters)
        
        # Check filename contains timestamp
        filename = os.path.basename(csv_path)
        self.assertTrue(filename.startswith("brainrot_database_"))
        self.assertTrue(filename.endswith(".csv"))
        
        # Check timestamp format (YYYYMMDD_HHMMSS)
        timestamp_part = filename.replace("brainrot_database_", "").replace(".csv", "")
        self.assertEqual(len(timestamp_part), 15)  # YYYYMMDD_HHMMSS
        self.assertTrue(timestamp_part[8] == "_")  # Underscore separator
        
        # Verify timestamp is valid
        try:
            datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
        except ValueError:
            self.fail(f"Invalid timestamp format: {timestamp_part}")
    
    def test_csv_statistics_accuracy(self):
        """Test that CSV statistics are accurate."""
        # Generate CSV file
        csv_path = self.csv_generator.generate_csv(self.test_characters)
        
        # Get statistics
        stats = self.csv_generator.get_csv_statistics(csv_path)
        
        # Verify statistics
        self.assertEqual(stats['total_characters'], 5)
        self.assertEqual(stats['characters_with_images'], 5)  # All have images
        self.assertEqual(stats['characters_without_images'], 0)
        
        # Check tier breakdown
        expected_tiers = {
            'Common': 1,
            'Rare': 1,
            'Epic': 1,
            'Legendary': 1,
            'Mythic': 1
        }
        self.assertEqual(stats['characters_by_tier'], expected_tiers)
        
        # Check file information
        self.assertEqual(stats['file_path'], csv_path)
        self.assertGreater(stats['file_size'], 0)
        self.assertIsInstance(stats['creation_time'], datetime)
        self.assertIsInstance(stats['modification_time'], datetime)
    
    def test_append_functionality_with_data_loader(self):
        """Test appending to CSV and loading with CSVDataLoader."""
        # Generate initial CSV file
        initial_characters = self.test_characters[:3]
        csv_path = self.csv_generator.generate_csv(initial_characters)
        
        # Append additional characters
        additional_characters = self.test_characters[3:]
        self.csv_generator.append_to_existing_csv(additional_characters, csv_path)
        
        # Load complete CSV with data loader
        data_loader = CSVDataLoader(csv_path)
        loaded_characters = data_loader.load_characters()
        
        # Verify all characters are present
        self.assertEqual(len(loaded_characters), 5)
        
        # Check that all original characters are present
        loaded_names = [char.name for char in loaded_characters]
        expected_names = [char.name for char in self.test_characters]
        self.assertEqual(set(loaded_names), set(expected_names))
    
    def test_csv_validation_with_real_format(self):
        """Test CSV validation with real database format."""
        # Generate CSV file
        csv_path = self.csv_generator.generate_csv(self.test_characters)
        
        # Validate format
        is_valid = self.csv_generator.validate_csv_format(csv_path)
        self.assertTrue(is_valid)
        
        # Verify it can be loaded by CSVDataLoader without errors
        try:
            data_loader = CSVDataLoader(csv_path)
            characters = data_loader.load_characters()
            self.assertGreater(len(characters), 0)
        except Exception as e:
            self.fail(f"CSVDataLoader failed to load generated CSV: {e}")
    
    def test_multiple_csv_generation_unique_filenames(self):
        """Test that multiple CSV generations create unique filenames."""
        # Generate first CSV
        csv_path1 = self.csv_generator.generate_csv(self.test_characters[:2])
        
        # Wait a moment to ensure different timestamp
        import time
        time.sleep(1)
        
        # Generate second CSV
        csv_path2 = self.csv_generator.generate_csv(self.test_characters[2:])
        
        # Verify different filenames
        self.assertNotEqual(csv_path1, csv_path2)
        
        # Verify both files exist
        self.assertTrue(os.path.exists(csv_path1))
        self.assertTrue(os.path.exists(csv_path2))
        
        # Verify both can be loaded
        data_loader1 = CSVDataLoader(csv_path1)
        data_loader2 = CSVDataLoader(csv_path2)
        
        chars1 = data_loader1.load_characters()
        chars2 = data_loader2.load_characters()
        
        self.assertEqual(len(chars1), 2)
        self.assertEqual(len(chars2), 3)


if __name__ == '__main__':
    unittest.main()