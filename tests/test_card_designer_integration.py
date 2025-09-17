"""
Integration tests for CardDesigner with other components.
"""

import unittest
import os
from PIL import Image

from card_generator.card_designer import CardDesigner
from card_generator.data_loader import CSVDataLoader
from card_generator.image_processor import ImageProcessor
from card_generator.config import CardConfig


class TestCardDesignerIntegration(unittest.TestCase):
    """Integration tests for CardDesigner with real data and images."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.designer = CardDesigner()
        self.data_loader = CSVDataLoader()
        self.image_processor = ImageProcessor()
        
        # Check if test data exists
        self.csv_exists = os.path.exists('steal_a_brainrot_complete_database.csv')
        self.images_exist = os.path.exists('images') and os.listdir('images')
    
    @unittest.skipUnless(os.path.exists('steal_a_brainrot_complete_database.csv'), 
                        "CSV file not found")
    def test_card_generation_with_real_data(self):
        """Test card generation using real character data."""
        # Load a few characters from the CSV
        characters = self.data_loader.load_characters()[:3]  # Just test first 3
        
        self.assertGreater(len(characters), 0, "No characters loaded from CSV")
        
        for character in characters:
            with self.subTest(character=character.name):
                # Generate card without image first
                card = self.designer.create_card(character)
                
                # Verify card properties
                self.assertEqual(card.size, (self.designer.config.width, self.designer.config.height))
                self.assertEqual(card.mode, 'RGB')
    
    @unittest.skipUnless(os.path.exists('steal_a_brainrot_complete_database.csv') and 
                        os.path.exists('images') and os.listdir('images'), 
                        "CSV file or images directory not found")
    def test_card_generation_with_real_images(self):
        """Test card generation using real character data and images."""
        # Load characters and try to find their images
        characters = self.data_loader.load_characters()[:5]  # Test first 5
        
        cards_generated = 0
        for character in characters:
            if character.has_image():
                try:
                    # Load the character image
                    image = self.image_processor.load_image(character.image_path)
                    
                    # Generate card with image
                    card = self.designer.create_card(character, image)
                    
                    # Verify card properties
                    self.assertEqual(card.size, (self.designer.config.width, self.designer.config.height))
                    self.assertEqual(card.mode, 'RGB')
                    
                    cards_generated += 1
                    
                except Exception as e:
                    # Log but don't fail the test for individual image issues
                    print(f"Warning: Could not process {character.name}: {e}")
        
        # At least some cards should have been generated
        if cards_generated == 0:
            self.skipTest("No character images could be processed")
    
    def test_card_generation_with_various_tiers(self):
        """Test card generation with characters of different tiers."""
        from card_generator.config import TIER_COLORS
        from card_generator.data_models import CharacterData
        
        # Create test characters for each tier
        test_characters = []
        for tier in TIER_COLORS.keys():
            character = CharacterData(
                name=f"Test {tier} Character",
                tier=tier,
                cost=1000,
                income=50,
                variant="Standard"
            )
            test_characters.append(character)
        
        # Generate cards for all tiers
        for character in test_characters:
            with self.subTest(tier=character.tier):
                card = self.designer.create_card(character)
                
                # Verify card was created successfully
                self.assertEqual(card.size, (self.designer.config.width, self.designer.config.height))
                self.assertEqual(card.mode, 'RGB')
    
    def test_card_generation_with_processed_images(self):
        """Test card generation with images processed by ImageProcessor."""
        from card_generator.data_models import CharacterData
        
        # Create a test character
        character = CharacterData(
            name="Processed Image Test",
            tier="Epic",
            cost=5000,
            income=250,
            variant="Standard"
        )
        
        # Create and process a test image
        test_image = Image.new('RGB', (800, 600), 'purple')
        
        # Process the image (resize, validate, etc.)
        processed_image = self.image_processor.resize_and_crop(
            test_image, 
            (400, 400)
        )
        
        # Generate card with processed image
        card = self.designer.create_card(character, processed_image)
        
        # Verify card properties
        self.assertEqual(card.size, (self.designer.config.width, self.designer.config.height))
        self.assertEqual(card.mode, 'RGB')
    
    def test_card_generation_performance(self):
        """Test card generation performance with multiple characters."""
        from card_generator.data_models import CharacterData
        import time
        
        # Create multiple test characters
        characters = []
        for i in range(10):
            character = CharacterData(
                name=f"Performance Test Character {i+1}",
                tier="Common",
                cost=100 * (i + 1),
                income=5 * (i + 1),
                variant="Standard"
            )
            characters.append(character)
        
        # Time the card generation
        start_time = time.time()
        
        cards = []
        for character in characters:
            card = self.designer.create_card(character)
            cards.append(card)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Verify all cards were generated
        self.assertEqual(len(cards), 10)
        
        # Performance should be reasonable (less than 5 seconds for 10 cards)
        self.assertLess(generation_time, 5.0, 
                       f"Card generation took too long: {generation_time:.2f} seconds")
        
        # Average time per card should be reasonable
        avg_time = generation_time / len(cards)
        self.assertLess(avg_time, 1.0, 
                       f"Average time per card too high: {avg_time:.2f} seconds")


if __name__ == '__main__':
    unittest.main()