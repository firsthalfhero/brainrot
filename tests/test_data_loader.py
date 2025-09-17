"""
Unit tests for the CSV data loading functionality.
"""

import unittest
import tempfile
import os
import shutil
from card_generator.data_loader import CSVDataLoader
from card_generator.data_models import CharacterData


class TestCSVDataLoader(unittest.TestCase):
    """Test cases for CSVDataLoader class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.test_dir, 'test_characters.csv')
        self.images_dir = os.path.join(self.test_dir, 'images')
        os.makedirs(self.images_dir)
        
        # Create sample CSV data
        self.sample_csv_content = '''Character Name,Tier,Cost,Income per Second,Cost/Income Ratio,Variant Type
"Noobini Pizzanini","Common",25,1,"25.0","Standard"
"Tim Cheese","Common",500,5,"100.0","Standard"
"FluriFlura","Rare",750,7,"107.1","Standard"
"Test Character","Epic",1000,10,"100.0","Special"
"Unicode Test ñáéíóú","Legendary",2000,20,"100.0","Standard"
'''
        
        # Write sample CSV file
        with open(self.csv_path, 'w', encoding='utf-8') as f:
            f.write(self.sample_csv_content)
        
        # Create sample image files
        self.create_sample_images()
        
        # Initialize loader
        self.loader = CSVDataLoader(self.csv_path, self.images_dir)
    
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.test_dir)
    
    def create_sample_images(self):
        """Create sample image files for testing."""
        # Create some test image files (empty files for testing)
        test_images = [
            'Noobini Pizzanini_1.png',
            'Tim Cheese_1.png',
            'Tim Cheese_2.jpg',
            'FluriFlura_1.webp',
            'Test Character_1.png',
            'Other Character_1.png'  # This won't match any CSV entry
        ]
        
        for image_name in test_images:
            image_path = os.path.join(self.images_dir, image_name)
            with open(image_path, 'w') as f:
                f.write('fake image content')
    
    def test_load_characters_success(self):
        """Test successful loading of characters from CSV."""
        characters = self.loader.load_characters()
        
        # Should load 5 characters from sample CSV
        self.assertEqual(len(characters), 5)
        
        # Check first character
        first_char = characters[0]
        self.assertEqual(first_char.name, "Noobini Pizzanini")
        self.assertEqual(first_char.tier, "Common")
        self.assertEqual(first_char.cost, 25)
        self.assertEqual(first_char.income, 1)
        self.assertEqual(first_char.variant, "Standard")
        
        # Check that image path is set for characters with images
        self.assertIsNotNone(first_char.image_path)
        self.assertTrue(first_char.has_image())
    
    def test_load_characters_with_unicode(self):
        """Test loading characters with unicode characters in names."""
        characters = self.loader.load_characters()
        
        # Find the unicode character
        unicode_char = next((c for c in characters if "ñáéíóú" in c.name), None)
        self.assertIsNotNone(unicode_char)
        self.assertEqual(unicode_char.name, "Unicode Test ñáéíóú")
        self.assertEqual(unicode_char.tier, "Legendary")
    
    def test_find_character_image_exact_match(self):
        """Test finding character images with exact name match."""
        image_path = self.loader.find_character_image("Noobini Pizzanini")
        self.assertIsNotNone(image_path)
        self.assertTrue(image_path.endswith("Noobini Pizzanini_1.png"))
    
    def test_find_character_image_multiple_files(self):
        """Test that first image is returned when multiple exist."""
        image_path = self.loader.find_character_image("Tim Cheese")
        self.assertIsNotNone(image_path)
        # Should return the first one alphabetically (Tim Cheese_1.png, not _2.jpg)
        self.assertTrue("Tim Cheese_1.png" in image_path)
    
    def test_find_character_image_not_found(self):
        """Test behavior when character image is not found."""
        image_path = self.loader.find_character_image("Nonexistent Character")
        self.assertIsNone(image_path)
    
    def test_get_characters_with_images(self):
        """Test filtering characters that have images."""
        characters_with_images = self.loader.get_characters_with_images()
        
        # Should have 4 characters with images (all except Unicode Test)
        self.assertEqual(len(characters_with_images), 4)
        
        # All should have image paths
        for char in characters_with_images:
            self.assertTrue(char.has_image())
    
    def test_get_characters_without_images(self):
        """Test filtering characters that don't have images."""
        characters_without_images = self.loader.get_characters_without_images()
        
        # Should have 1 character without image (Unicode Test)
        self.assertEqual(len(characters_without_images), 1)
        self.assertEqual(characters_without_images[0].name, "Unicode Test ñáéíóú")
    
    def test_get_image_coverage_stats(self):
        """Test image coverage statistics."""
        stats = self.loader.get_image_coverage_stats()
        
        self.assertEqual(stats['total_characters'], 5)
        self.assertEqual(stats['characters_with_images'], 4)
        self.assertEqual(stats['characters_without_images'], 1)
        self.assertEqual(stats['image_coverage_percentage'], 80.0)
    
    def test_csv_file_not_found(self):
        """Test error handling when CSV file doesn't exist."""
        loader = CSVDataLoader('nonexistent.csv', self.images_dir)
        
        with self.assertRaises(FileNotFoundError):
            loader.load_characters()
    
    def test_invalid_csv_data(self):
        """Test handling of invalid CSV data."""
        # Create CSV with invalid data
        invalid_csv = os.path.join(self.test_dir, 'invalid.csv')
        with open(invalid_csv, 'w', encoding='utf-8') as f:
            f.write('''Character Name,Tier,Cost,Income per Second,Variant Type
"Valid Character","Common",100,5,"Standard"
"Invalid Cost","Common","not_a_number",5,"Standard"
"Missing Tier","",100,5,"Standard"
"Invalid Income","Common",100,"not_a_number","Standard"
''')
        
        loader = CSVDataLoader(invalid_csv, self.images_dir)
        characters = loader.load_characters()
        
        # Should only load the valid character
        self.assertEqual(len(characters), 1)
        self.assertEqual(characters[0].name, "Valid Character")
    
    def test_empty_csv_file(self):
        """Test handling of empty CSV file."""
        empty_csv = os.path.join(self.test_dir, 'empty.csv')
        with open(empty_csv, 'w', encoding='utf-8') as f:
            f.write('Character Name,Tier,Cost,Income per Second,Variant Type\n')
        
        loader = CSVDataLoader(empty_csv, self.images_dir)
        
        with self.assertRaises(ValueError):
            loader.load_characters()
    
    def test_missing_images_directory(self):
        """Test behavior when images directory doesn't exist."""
        loader = CSVDataLoader(self.csv_path, 'nonexistent_images_dir')
        characters = loader.load_characters()
        
        # Characters should load but have no image paths
        self.assertEqual(len(characters), 5)
        for char in characters:
            self.assertFalse(char.has_image())
    
    def test_character_data_validation(self):
        """Test that CharacterData validation works through the loader."""
        # This test ensures the data models validation is working
        characters = self.loader.load_characters()
        
        for char in characters:
            # All characters should be valid CharacterData objects
            self.assertIsInstance(char, CharacterData)
            self.assertIsInstance(char.name, str)
            self.assertIsInstance(char.tier, str)
            self.assertIsInstance(char.cost, int)
            self.assertIsInstance(char.income, int)
            self.assertIsInstance(char.variant, str)
            self.assertGreaterEqual(char.cost, 0)
            self.assertGreaterEqual(char.income, 0)


class TestCSVDataLoaderIntegration(unittest.TestCase):
    """Integration tests using the actual project files."""
    
    def test_load_actual_csv_file(self):
        """Test loading the actual project CSV file if it exists."""
        if os.path.exists('steal_a_brainrot_complete_database.csv'):
            loader = CSVDataLoader()
            characters = loader.load_characters()
            
            # Should load some characters
            self.assertGreater(len(characters), 0)
            
            # Check that at least some characters have images
            characters_with_images = loader.get_characters_with_images()
            self.assertGreater(len(characters_with_images), 0)
            
            # Print some stats for manual verification
            stats = loader.get_image_coverage_stats()
            print(f"\nActual CSV stats:")
            print(f"Total characters: {stats['total_characters']}")
            print(f"Characters with images: {stats['characters_with_images']}")
            print(f"Image coverage: {stats['image_coverage_percentage']:.1f}%")
        else:
            self.skipTest("Actual CSV file not found")


if __name__ == '__main__':
    unittest.main()