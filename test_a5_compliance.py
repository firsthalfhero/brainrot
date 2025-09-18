"""
Unit tests for A5 format compliance validation.
"""

import unittest
from unittest.mock import Mock, patch
from PIL import Image

from card_generator.config import CardConfig
from card_generator.card_designer import CardDesigner
from card_generator.data_models import CharacterData


class TestA5Compliance(unittest.TestCase):
    """Test A5 format compliance requirements."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = CardConfig()
        self.designer = CardDesigner(self.config)
        self.test_character = CharacterData(
            name="Test Character",
            tier="Common",
            cost=1000,
            income=50,
            variant="Standard"
        )
    
    def test_minimum_font_sizes_at_300_dpi(self):
        """Test that font sizes meet enhanced minimum requirements at 300 DPI."""
        config = CardConfig(dpi=300)
        
        # Character name font must be at least 96pt (doubled for enhanced readability)
        self.assertGreaterEqual(config.scaled_title_font_size, 96)
        
        # Tier font must be at least 72pt (doubled for enhanced readability)
        self.assertGreaterEqual(config.scaled_tier_font_size, 72)
        
        # Stats font must be at least 48pt (doubled for enhanced readability)
        self.assertGreaterEqual(config.scaled_stats_font_size, 48)
    
    def test_minimum_font_sizes_at_different_dpi(self):
        """Test that font sizes scale correctly for different DPI settings."""
        # Test at 150 DPI (half of 300)
        config_150 = CardConfig(dpi=150)
        self.assertGreaterEqual(config_150.scaled_title_font_size, 48)  # 96 * 0.5
        self.assertGreaterEqual(config_150.scaled_tier_font_size, 36)   # 72 * 0.5
        self.assertGreaterEqual(config_150.scaled_stats_font_size, 24)  # 48 * 0.5
        
        # Test at 600 DPI (double of 300)
        config_600 = CardConfig(dpi=600)
        self.assertGreaterEqual(config_600.scaled_title_font_size, 192)  # 96 * 2
        self.assertGreaterEqual(config_600.scaled_tier_font_size, 144)   # 72 * 2
        self.assertGreaterEqual(config_600.scaled_stats_font_size, 96)   # 48 * 2
    
    def test_image_height_exactly_60_percent(self):
        """Test that image area is exactly 60% of card height."""
        config = CardConfig()
        expected_image_height = int(config.height * 0.6)
        actual_image_height = config.image_height
        
        self.assertEqual(actual_image_height, expected_image_height)
        self.assertAlmostEqual(config.image_ratio, 0.6, places=3)
    
    def test_a5_compliance_validation_success(self):
        """Test that valid configuration passes A5 compliance validation."""
        config = CardConfig(
            title_font_size=96,
            tier_font_size=72,
            stats_font_size=48,
            image_ratio=0.6,
            dpi=300
        )
        
        # Should not raise any exception
        self.assertTrue(config.validate_a5_compliance())
    
    def test_a5_compliance_validation_font_size_failures(self):
        """Test that invalid font sizes fail A5 compliance validation."""
        # Test title font too small
        with self.assertRaises(ValueError) as context:
            config = CardConfig(title_font_size=80, dpi=300)
            config.validate_a5_compliance()
        self.assertIn("Character name font must be at least 96pt", str(context.exception))
        
        # Test tier font too small
        with self.assertRaises(ValueError) as context:
            config = CardConfig(tier_font_size=60, dpi=300)
            config.validate_a5_compliance()
        self.assertIn("Tier font must be at least 72pt", str(context.exception))
        
        # Test stats font too small
        with self.assertRaises(ValueError) as context:
            config = CardConfig(stats_font_size=40, dpi=300)
            config.validate_a5_compliance()
        self.assertIn("Stats font must be at least 48pt", str(context.exception))
    
    def test_a5_compliance_validation_image_ratio_failure(self):
        """Test that incorrect image ratio fails A5 compliance validation."""
        with self.assertRaises(ValueError) as context:
            config = CardConfig(image_ratio=0.5)
            config.validate_a5_compliance()
        self.assertIn("Image must occupy exactly 60%", str(context.exception))
    
    def test_card_layout_validation_success(self):
        """Test that valid card layout passes validation."""
        # Create a test image that fits within 60% height
        test_image = Image.new('RGB', (400, int(self.config.height * 0.6)), 'red')
        
        # Mock the font methods to avoid font loading issues in tests
        with patch.object(self.designer, '_get_font') as mock_font:
            mock_font_obj = Mock()
            mock_font_obj.getbbox.return_value = (0, 0, 100, 30)  # width=100, height=30
            mock_font.return_value = mock_font_obj
            
            # Should not raise any exception
            self.designer._validate_card_layout(self.test_character, test_image)
    
    def test_card_layout_validation_image_too_tall(self):
        """Test that oversized image fails layout validation."""
        # Create an image that exceeds 60% height
        oversized_image = Image.new('RGB', (400, int(self.config.height * 0.7)), 'red')
        
        with self.assertRaises(ValueError) as context:
            self.designer._validate_card_layout(self.test_character, oversized_image)
        self.assertIn("Image height", str(context.exception))
        self.assertIn("exceeds 60% of card height", str(context.exception))
    
    def test_card_layout_validation_content_overflow(self):
        """Test that content overflow fails layout validation."""
        # Create a normal-sized image
        test_image = Image.new('RGB', (400, int(self.config.height * 0.6)), 'red')
        
        # Mock fonts to return very large text dimensions
        with patch.object(self.designer, '_get_font') as mock_font:
            mock_font_obj = Mock()
            mock_font_obj.getbbox.return_value = (0, 0, 100, 500)  # Very tall text
            mock_font.return_value = mock_font_obj
            
            with self.assertRaises(ValueError) as context:
                self.designer._validate_card_layout(self.test_character, test_image)
            self.assertIn("Total content height", str(context.exception))
            self.assertIn("exceeds available card space", str(context.exception))
    
    def test_calculate_total_content_height(self):
        """Test calculation of total content height."""
        test_image = Image.new('RGB', (400, 300), 'red')
        
        with patch.object(self.designer, '_get_font') as mock_font:
            mock_font_obj = Mock()
            mock_font_obj.getbbox.return_value = (0, 0, 100, 30)  # width=100, height=30
            mock_font.return_value = mock_font_obj
            
            total_height = self.designer._calculate_total_content_height(
                self.test_character, test_image
            )
            
            # Should include: name(30) + image(300) + tier(30) + income(30) + cost(30) + margins(4*20)
            expected_height = 30 + 300 + 30 + 30 + 30 + (4 * self.config.scaled_inner_margin)
            self.assertEqual(total_height, expected_height)
    
    def test_image_scaling_maintains_60_percent_height(self):
        """Test that image scaling ensures exactly 60% height usage."""
        # Create a test image with different aspect ratio
        original_image = Image.new('RGB', (800, 600), 'blue')
        
        # Process the image
        target_height = int(self.config.height * 0.6)
        processed_image = self.designer._prepare_character_image(original_image, target_height)
        
        # Image should be scaled to fit within the target height
        self.assertLessEqual(processed_image.height, target_height)
        
        # For this specific case, height should match target (since width constraint isn't hit)
        expected_width = int(target_height * (800/600))  # Maintain aspect ratio
        max_width = self.config.width - (2 * self.config.scaled_margin)
        
        if expected_width <= max_width:
            self.assertEqual(processed_image.height, target_height)
        else:
            # Image was scaled down to fit width constraint
            self.assertLess(processed_image.height, target_height)
    
    def test_font_size_compliance_in_card_creation(self):
        """Test that card creation uses enhanced compliant font sizes."""
        # Test that the configuration itself has enhanced compliant font sizes
        self.assertGreaterEqual(self.config.scaled_title_font_size, 96)
        self.assertGreaterEqual(self.config.scaled_tier_font_size, 72)
        self.assertGreaterEqual(self.config.scaled_stats_font_size, 48)
        
        # Test that validation passes for compliant configuration
        self.assertTrue(self.config.validate_a5_compliance())


class TestA5ComplianceIntegration(unittest.TestCase):
    """Integration tests for A5 compliance with real character data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = CardConfig()
        self.designer = CardDesigner(self.config)
        
        # Test characters with various name lengths and stats
        self.test_characters = [
            CharacterData("Short", "Common", 100, 10, "Standard"),
            CharacterData("Medium Length Name", "Rare", 5000, 250, "Standard"),
            CharacterData("Very Long Character Name That Might Cause Issues", "Legendary", 1000000, 50000, "Special"),
            CharacterData("Avocadini Guffo", "Epic", 25000, 1250, "Standard"),
            CharacterData("Brri Brri Bicus Dicus Bombicus", "Mythic", 10000000, 500000, "Standard")
        ]
    
    def test_all_characters_pass_validation(self):
        """Test that all test characters pass A5 compliance validation."""
        test_image = Image.new('RGB', (400, int(self.config.height * 0.6)), 'purple')
        
        for character in self.test_characters:
            with self.subTest(character=character.name):
                # Test that validation logic works for different characters
                with patch.object(self.designer, '_get_font') as mock_font:
                    mock_font_obj = Mock()
                    mock_font_obj.getbbox.return_value = (0, 0, 200, 40)
                    mock_font.return_value = mock_font_obj
                    
                    # Test validation directly without full card creation
                    try:
                        self.designer._validate_card_layout(character, test_image)
                        validation_passed = True
                    except ValueError:
                        validation_passed = False
                    
                    self.assertTrue(validation_passed, f"Validation failed for {character.name}")
    
    def test_different_dpi_settings_maintain_compliance(self):
        """Test that different DPI settings maintain A5 compliance."""
        dpi_settings = [150, 300, 450, 600]
        
        for dpi in dpi_settings:
            with self.subTest(dpi=dpi):
                # Create configuration with enhanced font sizes appropriate for the DPI
                scale_factor = dpi / 300.0
                config = CardConfig(
                    dpi=dpi,
                    title_font_size=max(96, int(96 * scale_factor)),
                    tier_font_size=max(72, int(72 * scale_factor)),
                    stats_font_size=max(48, int(48 * scale_factor))
                )
                
                # Test that configuration is compliant at different DPI settings
                self.assertTrue(config.validate_a5_compliance())
                
                # Test that font sizes scale correctly
                expected_title_size = int(96 * scale_factor)
                expected_tier_size = int(72 * scale_factor)
                expected_stats_size = int(48 * scale_factor)
                
                self.assertGreaterEqual(config.scaled_title_font_size, expected_title_size)
                self.assertGreaterEqual(config.scaled_tier_font_size, expected_tier_size)
                self.assertGreaterEqual(config.scaled_stats_font_size, expected_stats_size)


if __name__ == '__main__':
    unittest.main()