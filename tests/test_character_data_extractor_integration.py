"""
Integration tests for the CharacterDataExtractor module.

These tests make actual HTTP requests to verify the extractor works with real wiki pages.
Run these tests sparingly to avoid overwhelming the wiki servers.
"""

import unittest
import time
from card_generator.character_data_extractor import CharacterDataExtractor
from card_generator.data_models import CharacterData


class TestCharacterDataExtractorIntegration(unittest.TestCase):
    """Integration test cases for CharacterDataExtractor class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        cls.extractor = CharacterDataExtractor()
        # Add a small delay to be respectful to the server
        time.sleep(1)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.extractor.close()
    
    def setUp(self):
        """Add delay between tests to be respectful."""
        time.sleep(2)  # Respectful delay between requests
    
    @unittest.skip("Skip integration test by default to avoid server load")
    def test_extract_real_character_data(self):
        """Test extracting data from a real character page."""
        # Test with a known character (adjust name as needed)
        character_name = "Fluriflura"  # This should be a real character from the wiki
        tier = "Common"
        
        character_data = self.extractor.extract_character_data(character_name, tier)
        
        if character_data:
            self.assertIsInstance(character_data, CharacterData)
            self.assertEqual(character_data.name, character_name)
            self.assertEqual(character_data.tier, tier)
            self.assertEqual(character_data.variant, "Standard")
            self.assertIsNotNone(character_data.extraction_timestamp)
            
            # Print results for manual verification
            print(f"\nExtracted data for {character_name}:")
            print(f"  Cost: {character_data.cost}")
            print(f"  Income: {character_data.income}")
            print(f"  Wiki URL: {character_data.wiki_url}")
            print(f"  Image URL: {character_data.image_url}")
            print(f"  Extraction Success: {character_data.extraction_success}")
            print(f"  Errors: {character_data.extraction_errors}")
        else:
            print(f"Could not extract data for {character_name}")
            self.fail(f"Failed to extract data for {character_name}")
    
    @unittest.skip("Skip integration test by default to avoid server load")
    def test_find_character_page_variations(self):
        """Test finding character pages with different name variations."""
        test_characters = [
            "Fluriflura",
            "Test Character",  # This probably doesn't exist
            "Brr Brr Patapim"  # Character with spaces
        ]
        
        for character_name in test_characters:
            print(f"\nTesting page discovery for: {character_name}")
            
            url = self.extractor._find_character_page(character_name)
            
            if url:
                print(f"  Found URL: {url}")
                self.assertTrue(url.startswith("https://"))
            else:
                print(f"  No URL found for {character_name}")
            
            # Add delay between requests
            time.sleep(2)
    
    @unittest.skip("Skip integration test by default to avoid server load")
    def test_url_variations_generation(self):
        """Test URL variation generation with real character names."""
        test_names = [
            "Fluriflura",
            "Brr Brr Patapim",
            "Test-Character!",
            "Character With Spaces"
        ]
        
        for name in test_names:
            variations = self.extractor._generate_url_variations(name)
            print(f"\nURL variations for '{name}':")
            for i, url in enumerate(variations, 1):
                print(f"  {i}. {url}")
            
            self.assertTrue(len(variations) > 0)
            self.assertTrue(all(url.startswith("https://") for url in variations))


if __name__ == '__main__':
    # To run integration tests, comment out the @unittest.skip decorators
    print("Integration tests are skipped by default to avoid server load.")
    print("To run them, comment out the @unittest.skip decorators in the test methods.")
    unittest.main()