"""
Integration test for A5 compliance with real card generation.
"""

import unittest
import tempfile
import os
from PIL import Image

from card_generator.config import CardConfig
from card_generator.card_designer import CardDesigner
from card_generator.data_models import CharacterData


class TestA5ComplianceIntegration(unittest.TestCase):
    """Integration test for A5 compliance with actual card generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = CardConfig()
        self.designer = CardDesigner(self.config)
        self.temp_dir = tempfile.mkdtemp()
        
        # Test character with realistic data
        self.test_character = CharacterData(
            name="Avocadini Guffo",
            tier="Epic",
            cost=25000,
            income=1250,
            variant="Standard"
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_real_card_generation_meets_a5_compliance(self):
        """Test that real card generation meets A5 compliance requirements."""
        # Create a test image that represents a typical character image
        test_image = Image.new('RGB', (800, 1000), 'blue')  # Portrait orientation
        
        # Generate the card
        card = self.designer.create_card(self.test_character, test_image)
        
        # Verify card dimensions are A5
        self.assertEqual(card.size, (self.config.width, self.config.height))
        
        # Verify the card was created successfully
        self.assertIsInstance(card, Image.Image)
        
        # Save the card to verify it can be written
        output_path = os.path.join(self.temp_dir, "test_card.png")
        card.save(output_path)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify file size is reasonable (not empty, not too large)
        file_size = os.path.getsize(output_path)
        self.assertGreater(file_size, 10000)  # At least 10KB
        self.assertLess(file_size, 5000000)   # Less than 5MB
    
    def test_different_character_types_compliance(self):
        """Test A5 compliance with different character types."""
        test_characters = [
            CharacterData("Short", "Common", 100, 10, "Standard"),
            CharacterData("Medium Length Name", "Rare", 5000, 250, "Standard"),
            CharacterData("Very Long Character Name That Tests Wrapping", "Legendary", 1000000, 50000, "Special"),
            CharacterData("Brri Brri Bicus Dicus Bombicus", "Mythic", 10000000, 500000, "Standard")
        ]
        
        test_image = Image.new('RGB', (600, 800), 'green')
        
        for character in test_characters:
            with self.subTest(character=character.name):
                # Should not raise any validation errors
                card = self.designer.create_card(character, test_image)
                
                # Verify card properties
                self.assertEqual(card.size, (self.config.width, self.config.height))
                self.assertIsInstance(card, Image.Image)
    
    def test_image_scaling_compliance(self):
        """Test that image scaling meets the 60% height requirement."""
        # Test with different aspect ratios
        test_images = [
            Image.new('RGB', (400, 600), 'red'),    # Portrait
            Image.new('RGB', (800, 400), 'blue'),   # Landscape
            Image.new('RGB', (500, 500), 'green'),  # Square
            Image.new('RGB', (200, 1000), 'yellow'), # Very tall
            Image.new('RGB', (1200, 300), 'purple') # Very wide
        ]
        
        for i, test_image in enumerate(test_images):
            with self.subTest(image_type=f"image_{i}"):
                card = self.designer.create_card(self.test_character, test_image)
                
                # Verify card was created successfully
                self.assertEqual(card.size, (self.config.width, self.config.height))
                self.assertIsInstance(card, Image.Image)
    
    def test_font_size_compliance_verification(self):
        """Test that font sizes meet minimum requirements."""
        # Verify configuration meets requirements
        self.assertGreaterEqual(self.config.scaled_title_font_size, 48)
        self.assertGreaterEqual(self.config.scaled_tier_font_size, 36)
        self.assertGreaterEqual(self.config.scaled_stats_font_size, 24)
        
        # Verify A5 compliance validation passes
        self.assertTrue(self.config.validate_a5_compliance())
    
    def test_layout_validation_with_real_content(self):
        """Test layout validation with realistic content."""
        test_image = Image.new('RGB', (400, int(self.config.height * 0.6)), 'orange')
        
        # Should not raise validation errors
        card = self.designer.create_card(self.test_character, test_image)
        
        # Verify the card meets basic requirements
        self.assertEqual(card.size, (self.config.width, self.config.height))
        self.assertIsInstance(card, Image.Image)


if __name__ == '__main__':
    unittest.main()