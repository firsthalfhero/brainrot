"""
Unit tests for the character selection functionality.
"""

import unittest
import tempfile
import os
import shutil
from card_generator.data_loader import CSVDataLoader
from card_generator.character_selector import CharacterSelector
from card_generator.data_models import CharacterData


class TestCharacterSelector(unittest.TestCase):
    """Test cases for CharacterSelector class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.test_dir, 'test_characters.csv')
        self.images_dir = os.path.join(self.test_dir, 'images')
        os.makedirs(self.images_dir)
        
        # Create sample CSV data with diverse characters for testing
        self.sample_csv_content = '''Character Name,Tier,Cost,Income per Second,Cost/Income Ratio,Variant Type
"Tim Cheese","Common",100,5,"20.0","Standard"
"FluriFlura","Rare",500,10,"50.0","Standard"
"Epic Dragon","Epic",1000,25,"40.0","Special"
"Legendary Hero","Legendary",2000,50,"40.0","Standard"
"Mythic Beast","Mythic",5000,100,"50.0","Special"
"Divine Angel","Divine",10000,200,"50.0","Standard"
"Test Character A","Common",50,2,"25.0","Standard"
"Test Character B","Common",150,8,"18.75","Special"
"Rare Unicorn","Rare",750,15,"50.0","Standard"
"Special Dragon","Epic",1200,30,"40.0","Special"
'''
        
        # Write sample CSV file
        with open(self.csv_path, 'w', encoding='utf-8') as f:
            f.write(self.sample_csv_content)
        
        # Create sample image files
        self.create_sample_images()
        
        # Initialize loader and selector
        self.data_loader = CSVDataLoader(self.csv_path, self.images_dir)
        self.selector = CharacterSelector(self.data_loader)
    
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.test_dir)
    
    def create_sample_images(self):
        """Create sample image files for testing."""
        # Create images for some characters (not all)
        test_images = [
            'Tim Cheese_1.png',
            'FluriFlura_1.png',
            'Epic Dragon_1.png',
            'Test Character A_1.png',
            'Rare Unicorn_1.png'
        ]
        
        for image_name in test_images:
            image_path = os.path.join(self.images_dir, image_name)
            with open(image_path, 'w') as f:
                f.write('fake image content')
    
    def test_get_all_characters(self):
        """Test getting all characters."""
        characters = self.selector.get_all_characters()
        self.assertEqual(len(characters), 10)
        
        # Test caching
        characters2 = self.selector.get_all_characters()
        self.assertIs(characters, characters2)  # Should be the same object
    
    def test_select_by_names(self):
        """Test selecting characters by exact names."""
        # Test single name
        characters = self.selector.select_by_names(['Tim Cheese'])
        self.assertEqual(len(characters), 1)
        self.assertEqual(characters[0].name, 'Tim Cheese')
        
        # Test multiple names
        characters = self.selector.select_by_names(['Tim Cheese', 'FluriFlura'])
        self.assertEqual(len(characters), 2)
        names = [char.name for char in characters]
        self.assertIn('Tim Cheese', names)
        self.assertIn('FluriFlura', names)
        
        # Test case insensitive
        characters = self.selector.select_by_names(['tim cheese'], case_sensitive=False)
        self.assertEqual(len(characters), 1)
        self.assertEqual(characters[0].name, 'Tim Cheese')
        
        # Test case sensitive (should not match)
        characters = self.selector.select_by_names(['tim cheese'], case_sensitive=True)
        self.assertEqual(len(characters), 0)
    
    def test_select_by_name_pattern(self):
        """Test selecting characters by name pattern."""
        # Test wildcard pattern
        characters = self.selector.select_by_name_pattern('Test*')
        self.assertEqual(len(characters), 2)
        names = [char.name for char in characters]
        self.assertIn('Test Character A', names)
        self.assertIn('Test Character B', names)
        
        # Test regex pattern
        characters = self.selector.select_by_name_pattern(r'.*Dragon.*')
        self.assertEqual(len(characters), 2)
        names = [char.name for char in characters]
        self.assertIn('Epic Dragon', names)
        self.assertIn('Special Dragon', names)
        
        # Test case insensitive
        characters = self.selector.select_by_name_pattern('dragon', case_sensitive=False)
        self.assertEqual(len(characters), 2)
        
        # Test case sensitive
        characters = self.selector.select_by_name_pattern('dragon', case_sensitive=True)
        self.assertEqual(len(characters), 0)
    
    def test_select_by_tiers(self):
        """Test selecting characters by tier."""
        # Test single tier
        characters = self.selector.select_by_tiers(['Common'])
        self.assertEqual(len(characters), 3)
        for char in characters:
            self.assertEqual(char.tier, 'Common')
        
        # Test multiple tiers
        characters = self.selector.select_by_tiers(['Common', 'Rare'])
        self.assertEqual(len(characters), 5)
        tiers = [char.tier for char in characters]
        self.assertTrue(all(tier in ['Common', 'Rare'] for tier in tiers))
        
        # Test case insensitive
        characters = self.selector.select_by_tiers(['common'], case_sensitive=False)
        self.assertEqual(len(characters), 3)
    
    def test_select_by_cost_range(self):
        """Test selecting characters by cost range."""
        # Test minimum cost only
        characters = self.selector.select_by_cost_range(min_cost=1000)
        costs = [char.cost for char in characters]
        self.assertTrue(all(cost >= 1000 for cost in costs))
        
        # Test maximum cost only
        characters = self.selector.select_by_cost_range(max_cost=500)
        costs = [char.cost for char in characters]
        self.assertTrue(all(cost <= 500 for cost in costs))
        
        # Test both min and max
        characters = self.selector.select_by_cost_range(min_cost=100, max_cost=1000)
        costs = [char.cost for char in characters]
        self.assertTrue(all(100 <= cost <= 1000 for cost in costs))
    
    def test_select_by_income_range(self):
        """Test selecting characters by income range."""
        # Test minimum income only
        characters = self.selector.select_by_income_range(min_income=25)
        incomes = [char.income for char in characters]
        self.assertTrue(all(income >= 25 for income in incomes))
        
        # Test maximum income only
        characters = self.selector.select_by_income_range(max_income=10)
        incomes = [char.income for char in characters]
        self.assertTrue(all(income <= 10 for income in incomes))
        
        # Test both min and max
        characters = self.selector.select_by_income_range(min_income=5, max_income=50)
        incomes = [char.income for char in characters]
        self.assertTrue(all(5 <= income <= 50 for income in incomes))
    
    def test_select_with_images_only(self):
        """Test selecting only characters with images."""
        characters = self.selector.select_with_images_only()
        
        # Should have 5 characters with images based on our test setup
        self.assertEqual(len(characters), 5)
        
        # All should have images
        for char in characters:
            self.assertTrue(char.has_image())
    
    def test_select_without_images_only(self):
        """Test selecting only characters without images."""
        characters = self.selector.select_without_images_only()
        
        # Should have 5 characters without images based on our test setup
        self.assertEqual(len(characters), 5)
        
        # None should have images
        for char in characters:
            self.assertFalse(char.has_image())
    
    def test_select_characters_complex_criteria(self):
        """Test selecting characters with complex criteria."""
        # Test multiple criteria combined
        criteria = {
            'tiers': ['Common', 'Rare'],
            'min_cost': 100,
            'max_cost': 800,
            'with_images_only': True
        }
        
        characters = self.selector.select_characters(criteria)
        
        # Verify all criteria are met
        for char in characters:
            self.assertIn(char.tier, ['Common', 'Rare'])
            self.assertGreaterEqual(char.cost, 100)
            self.assertLessEqual(char.cost, 800)
            self.assertTrue(char.has_image())
    
    def test_get_selection_summary(self):
        """Test getting selection summary statistics."""
        characters = self.selector.select_by_tiers(['Common', 'Rare'])
        summary = self.selector.get_selection_summary(characters)
        
        self.assertEqual(summary['total_selected'], 5)
        self.assertIn('Common', summary['tiers'])
        self.assertIn('Rare', summary['tiers'])
        self.assertEqual(summary['tiers']['Common'], 3)
        self.assertEqual(summary['tiers']['Rare'], 2)
        self.assertGreater(summary['with_images'], 0)
        self.assertGreater(summary['without_images'], 0)
        self.assertIsNotNone(summary['cost_range']['min'])
        self.assertIsNotNone(summary['cost_range']['max'])
    
    def test_get_selection_summary_empty(self):
        """Test getting summary for empty selection."""
        summary = self.selector.get_selection_summary([])
        
        self.assertEqual(summary['total_selected'], 0)
        self.assertEqual(summary['tiers'], {})
        self.assertEqual(summary['variants'], {})
        self.assertEqual(summary['with_images'], 0)
        self.assertEqual(summary['without_images'], 0)
        self.assertIsNone(summary['cost_range']['min'])
        self.assertIsNone(summary['cost_range']['max'])
    
    def test_get_available_options(self):
        """Test getting available filtering options."""
        options = self.selector.get_available_options()
        
        self.assertIn('tiers', options)
        self.assertIn('variants', options)
        self.assertIn('character_names', options)
        
        # Check that we have the expected tiers
        expected_tiers = ['Common', 'Divine', 'Epic', 'Legendary', 'Mythic', 'Rare']
        self.assertEqual(sorted(options['tiers']), expected_tiers)
        
        # Check that we have the expected variants
        expected_variants = ['Special', 'Standard']
        self.assertEqual(sorted(options['variants']), expected_variants)
        
        # Check that we have all character names
        self.assertEqual(len(options['character_names']), 10)


class TestDataLoaderFiltering(unittest.TestCase):
    """Test cases for filtering methods in CSVDataLoader."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test characters directly
        self.characters = [
            CharacterData("Tim Cheese", "Common", 100, 5, "Standard"),
            CharacterData("FluriFlura", "Rare", 500, 10, "Standard"),
            CharacterData("Epic Dragon", "Epic", 1000, 25, "Special"),
            CharacterData("Test Character", "Common", 50, 2, "Standard"),
            CharacterData("Special Beast", "Legendary", 2000, 50, "Special"),
        ]
        
        # Set image paths for some characters
        self.characters[0].image_path = "tim_cheese.png"
        self.characters[1].image_path = "fluriflura.png"
        # characters[2], [3], [4] have no images
        
        self.loader = CSVDataLoader()
    
    def test_filter_characters_by_name(self):
        """Test filtering by exact name matches."""
        # Test single name
        result = self.loader.filter_characters_by_name(
            self.characters, ["Tim Cheese"]
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Tim Cheese")
        
        # Test multiple names
        result = self.loader.filter_characters_by_name(
            self.characters, ["Tim Cheese", "FluriFlura"]
        )
        self.assertEqual(len(result), 2)
        
        # Test case insensitive
        result = self.loader.filter_characters_by_name(
            self.characters, ["tim cheese"], case_sensitive=False
        )
        self.assertEqual(len(result), 1)
        
        # Test empty list
        result = self.loader.filter_characters_by_name(self.characters, [])
        self.assertEqual(len(result), 5)  # Should return all
    
    def test_filter_characters_by_name_pattern(self):
        """Test filtering by name pattern."""
        # Test wildcard
        result = self.loader.filter_characters_by_name_pattern(
            self.characters, "Test*"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Test Character")
        
        # Test regex
        result = self.loader.filter_characters_by_name_pattern(
            self.characters, r".*Dragon.*"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Epic Dragon")
        
        # Test invalid pattern
        with self.assertRaises(ValueError):
            self.loader.filter_characters_by_name_pattern(
                self.characters, "[invalid"
            )
    
    def test_filter_characters_by_tier(self):
        """Test filtering by tier."""
        result = self.loader.filter_characters_by_tier(
            self.characters, ["Common"]
        )
        self.assertEqual(len(result), 2)
        for char in result:
            self.assertEqual(char.tier, "Common")
    
    def test_filter_characters_by_cost_range(self):
        """Test filtering by cost range."""
        # Test min only
        result = self.loader.filter_characters_by_cost_range(
            self.characters, min_cost=500
        )
        self.assertEqual(len(result), 3)
        
        # Test max only
        result = self.loader.filter_characters_by_cost_range(
            self.characters, max_cost=100
        )
        self.assertEqual(len(result), 2)
        
        # Test both
        result = self.loader.filter_characters_by_cost_range(
            self.characters, min_cost=100, max_cost=1000
        )
        self.assertEqual(len(result), 3)
    
    def test_filter_characters_by_income_range(self):
        """Test filtering by income range."""
        result = self.loader.filter_characters_by_income_range(
            self.characters, min_income=10, max_income=25
        )
        self.assertEqual(len(result), 2)
    
    def test_filter_characters_by_variant(self):
        """Test filtering by variant."""
        result = self.loader.filter_characters_by_variant(
            self.characters, ["Standard"]
        )
        self.assertEqual(len(result), 3)
        for char in result:
            self.assertEqual(char.variant, "Standard")
    
    def test_filter_characters_with_images_only(self):
        """Test filtering for characters with images."""
        result = self.loader.filter_characters_with_images_only(self.characters)
        self.assertEqual(len(result), 2)
        for char in result:
            self.assertTrue(char.has_image())
    
    def test_filter_characters_without_images_only(self):
        """Test filtering for characters without images."""
        result = self.loader.filter_characters_without_images_only(self.characters)
        self.assertEqual(len(result), 3)
        for char in result:
            self.assertFalse(char.has_image())
    
    def test_apply_custom_filter(self):
        """Test applying custom filter function."""
        # Filter for characters with cost > 500 and income > 20
        def custom_filter(char):
            return char.cost > 500 and char.income > 20
        
        result = self.loader.apply_custom_filter(self.characters, custom_filter)
        self.assertEqual(len(result), 2)  # Epic Dragon and Special Beast


if __name__ == '__main__':
    unittest.main()