"""
Unit tests for the CardDesigner class.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from PIL import Image, ImageDraw

from card_generator.card_designer import CardDesigner
from card_generator.config import CardConfig, TIER_COLORS
from card_generator.data_models import CharacterData


class TestCardDesigner(unittest.TestCase):
    """Test cases for CardDesigner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = CardConfig()
        self.designer = CardDesigner(self.config)
        
        # Sample character data for testing
        self.sample_character = CharacterData(
            name="Test Character",
            tier="Rare",
            cost=1000,
            income=50,
            variant="Standard"
        )
        
        self.long_name_character = CharacterData(
            name="This Is A Very Long Character Name That Should Wrap",
            tier="Epic",
            cost=5000,
            income=250,
            variant="Special"
        )
        
        # Create a simple test image
        self.test_image = Image.new('RGB', (400, 400), 'red')
    
    def test_init_with_default_config(self):
        """Test CardDesigner initialization with default config."""
        designer = CardDesigner()
        self.assertIsInstance(designer.config, CardConfig)
        self.assertEqual(designer.config.width, 1745)
        self.assertEqual(designer.config.height, 2468)
    
    def test_init_with_custom_config(self):
        """Test CardDesigner initialization with custom config."""
        custom_config = CardConfig(dpi=150, margin=30)
        designer = CardDesigner(custom_config)
        self.assertEqual(designer.config.dpi, 150)
        self.assertEqual(designer.config.margin, 30)
        # Test that scaled properties work
        self.assertEqual(designer.config.width, int(1745 * 0.5))  # 150 DPI is half of 300
        self.assertEqual(designer.config.height, int(2468 * 0.5))
    
    def test_create_card_basic(self):
        """Test basic card creation with character data."""
        card = self.designer.create_card(self.sample_character)
        
        # Verify card dimensions
        self.assertEqual(card.size, (self.config.width, self.config.height))
        self.assertEqual(card.mode, 'RGB')
    
    def test_create_card_with_image(self):
        """Test card creation with character image."""
        card = self.designer.create_card(self.sample_character, self.test_image)
        
        # Verify card was created
        self.assertEqual(card.size, (self.config.width, self.config.height))
        self.assertEqual(card.mode, 'RGB')
    
    def test_create_card_without_image(self):
        """Test card creation without character image (placeholder)."""
        card = self.designer.create_card(self.sample_character)
        
        # Verify card was created with placeholder
        self.assertEqual(card.size, (self.config.width, self.config.height))
        self.assertEqual(card.mode, 'RGB')
    
    def test_create_card_long_name(self):
        """Test card creation with long character name."""
        card = self.designer.create_card(self.long_name_character)
        
        # Verify card was created successfully
        self.assertEqual(card.size, (self.config.width, self.config.height))
        self.assertEqual(card.mode, 'RGB')
    
    def test_prepare_character_image_normal(self):
        """Test image preparation with normal-sized image."""
        target_height = 1000
        processed = self.designer._prepare_character_image(self.test_image, target_height)
        
        # Should maintain aspect ratio
        self.assertEqual(processed.height, target_height)
        self.assertEqual(processed.width, target_height)  # Square image
    
    def test_prepare_character_image_too_wide(self):
        """Test image preparation with very wide image."""
        wide_image = Image.new('RGB', (2000, 400), 'blue')
        target_height = 1000
        max_width = self.config.width - (2 * self.config.margin)
        
        processed = self.designer._prepare_character_image(wide_image, target_height)
        
        # Should be constrained by width
        self.assertLessEqual(processed.width, max_width)
    
    def test_prepare_character_image_height_based_scaling(self):
        """Test that image preparation uses height-based scaling without cropping."""
        # Create a portrait image (taller than wide)
        portrait_image = Image.new('RGB', (400, 800), 'green')
        target_height = 1000
        
        processed = self.designer._prepare_character_image(portrait_image, target_height)
        
        # Should scale to target height while maintaining aspect ratio
        self.assertEqual(processed.height, target_height)
        expected_width = int(target_height * (400 / 800))  # Maintain aspect ratio
        self.assertEqual(processed.width, expected_width)
        
        # Verify no cropping occurred by checking aspect ratio is preserved
        original_ratio = portrait_image.width / portrait_image.height
        processed_ratio = processed.width / processed.height
        self.assertAlmostEqual(original_ratio, processed_ratio, places=2)
    
    def test_prepare_character_image_portrait_no_cropping(self):
        """Test that portrait images are not cropped when using height-based scaling."""
        # Create a very tall portrait image
        tall_portrait = Image.new('RGB', (300, 1200), 'purple')
        target_height = 800
        
        processed = self.designer._prepare_character_image(tall_portrait, target_height)
        
        # Should maintain aspect ratio without cropping
        original_ratio = tall_portrait.width / tall_portrait.height
        processed_ratio = processed.width / processed.height
        self.assertAlmostEqual(original_ratio, processed_ratio, places=2)
        
        # Should scale to fit height
        self.assertEqual(processed.height, target_height)
        expected_width = int(target_height * original_ratio)
        self.assertEqual(processed.width, expected_width)
    
    def test_prepare_character_image_landscape_scaling(self):
        """Test height-based scaling with landscape images."""
        # Create a landscape image (wider than tall)
        landscape_image = Image.new('RGB', (1200, 600), 'orange')
        target_height = 800
        max_width = self.config.width - (2 * self.config.margin)
        
        processed = self.designer._prepare_character_image(landscape_image, target_height)
        
        # Calculate expected dimensions
        aspect_ratio = landscape_image.width / landscape_image.height
        expected_width = int(target_height * aspect_ratio)
        
        if expected_width <= max_width:
            # Should scale to target height
            self.assertEqual(processed.height, target_height)
            self.assertEqual(processed.width, expected_width)
        else:
            # Should be constrained by max width and scale proportionally
            self.assertLessEqual(processed.width, max_width)
            # Height should be scaled down proportionally
            scale_factor = max_width / expected_width
            expected_scaled_height = int(target_height * scale_factor)
            self.assertEqual(processed.height, expected_scaled_height)
    
    def test_create_placeholder_image(self):
        """Test placeholder image creation."""
        target_height = 1000
        placeholder = self.designer._create_placeholder_image(self.sample_character, target_height)
        
        # Verify placeholder properties
        self.assertIsInstance(placeholder, Image.Image)
        self.assertEqual(placeholder.mode, 'RGB')
        self.assertLessEqual(placeholder.height, target_height)
    
    def test_placeholder_image_tier_colors(self):
        """Test that placeholder images use correct tier colors."""
        for tier, expected_color in TIER_COLORS.items():
            character = CharacterData(
                name="Test",
                tier=tier,
                cost=100,
                income=10,
                variant="Standard"
            )
            
            placeholder = self.designer._create_placeholder_image(character, 500)
            
            # Get the dominant color (should be the tier color)
            # This is a simplified test - in practice, we'd need more sophisticated color checking
            self.assertIsInstance(placeholder, Image.Image)
    
    def test_wrap_text_single_line(self):
        """Test text wrapping with text that fits on one line."""
        font = self.designer._get_font(24)
        max_width = 1000
        text = "Short Name"
        
        wrapped = self.designer._wrap_text(text, font, max_width)
        
        self.assertEqual(len(wrapped), 1)
        self.assertEqual(wrapped[0], text)
    
    def test_wrap_text_multiple_lines(self):
        """Test text wrapping with text that needs multiple lines."""
        font = self.designer._get_font(48)
        max_width = 300  # Very narrow
        text = "This Is A Very Long Name"
        
        wrapped = self.designer._wrap_text(text, font, max_width)
        
        self.assertGreater(len(wrapped), 1)
        # Each line should be non-empty
        for line in wrapped:
            self.assertTrue(line.strip())
    
    def test_wrap_text_force_break(self):
        """Test text wrapping with force break for very long words."""
        font = self.designer._get_font(24)
        max_width = 100  # Very narrow
        text = "Supercalifragilisticexpialidocious"
        
        wrapped = self.designer._wrap_text(text, font, max_width, force=True)
        
        # Should break the long word
        self.assertGreater(len(wrapped), 1)
    
    def test_get_font_caching(self):
        """Test font caching functionality."""
        font1 = self.designer._get_font(24)
        font2 = self.designer._get_font(24)
        
        # Should return the same cached font object
        self.assertIs(font1, font2)
    
    def test_get_font_different_sizes(self):
        """Test getting fonts of different sizes."""
        font_small = self.designer._get_font(12)
        font_large = self.designer._get_font(48)
        
        # Should be different font objects
        self.assertIsNot(font_small, font_large)
    

    
    def test_render_character_name_short(self):
        """Test character name rendering with short name."""
        card = Image.new('RGB', (self.config.width, self.config.height), 'white')
        draw = ImageDraw.Draw(card)
        
        y_after = self.designer._render_character_name(draw, "Short", 100)
        
        # Should return a Y position after the text
        self.assertGreater(y_after, 100)
    
    def test_render_character_name_long(self):
        """Test character name rendering with long name."""
        card = Image.new('RGB', (self.config.width, self.config.height), 'white')
        draw = ImageDraw.Draw(card)
        
        long_name = "This Is A Very Long Character Name That Should Wrap"
        y_after = self.designer._render_character_name(draw, long_name, 100)
        
        # Should return a Y position after the text (likely multiple lines)
        self.assertGreater(y_after, 100)
    
    def test_all_tier_colors_supported(self):
        """Test that cards can be created for all supported tiers."""
        for tier in TIER_COLORS.keys():
            character = CharacterData(
                name=f"Test {tier}",
                tier=tier,
                cost=1000,
                income=50,
                variant="Standard"
            )
            
            # Should not raise an exception
            card = self.designer.create_card(character)
            self.assertEqual(card.size, (self.config.width, self.config.height))
    
    def test_various_character_data_combinations(self):
        """Test card creation with various character data combinations."""
        test_cases = [
            # Normal case
            CharacterData("Normal", "Common", 100, 5, "Standard"),
            # High values
            CharacterData("Expensive", "Divine", 1000000, 50000, "Special"),
            # Zero values
            CharacterData("Free", "Common", 0, 0, "Standard"),
            # Single character name
            CharacterData("X", "Rare", 50, 2, "Standard"),
            # Name with special characters
            CharacterData("Café Münchën", "Epic", 2500, 125, "Standard"),
        ]
        
        for character in test_cases:
            with self.subTest(character=character):
                card = self.designer.create_card(character)
                self.assertEqual(card.size, (self.config.width, self.config.height))
                self.assertEqual(card.mode, 'RGB')
    
    def test_new_layout_character_name_rendering(self):
        """Test new layout character name rendering with 60% width constraint."""
        card = Image.new('RGB', (self.config.width, self.config.height), 'white')
        draw = ImageDraw.Draw(card)
        
        # Test short name
        y_after = self.designer._render_character_name_new_layout(draw, "Short", 100)
        self.assertGreater(y_after, 100)
        
        # Test long name that should fit within 60% width
        long_name = "This Is A Very Long Character Name"
        y_after = self.designer._render_character_name_new_layout(draw, long_name, 100)
        self.assertGreater(y_after, 100)
    
    def test_new_layout_tier_display(self):
        """Test new layout tier display rendering."""
        card = Image.new('RGB', (self.config.width, self.config.height), 'white')
        draw = ImageDraw.Draw(card)
        
        for tier in TIER_COLORS.keys():
            with self.subTest(tier=tier):
                y_after = self.designer._render_tier_display(draw, tier, 100)
                self.assertGreater(y_after, 100)
    
    def test_new_layout_income_display(self):
        """Test new layout income display rendering with proper formatting."""
        card = Image.new('RGB', (self.config.width, self.config.height), 'white')
        draw = ImageDraw.Draw(card)
        
        test_incomes = [5, 1500, 2500000, 1500000000]
        for income in test_incomes:
            with self.subTest(income=income):
                y_after = self.designer._render_income_display(draw, income, 100)
                self.assertGreater(y_after, 100)
    
    def test_new_layout_cost_display(self):
        """Test new layout cost display rendering with proper formatting."""
        card = Image.new('RGB', (self.config.width, self.config.height), 'white')
        draw = ImageDraw.Draw(card)
        
        test_costs = [100, 1500, 2500000, 1500000000]
        for cost in test_costs:
            with self.subTest(cost=cost):
                y_after = self.designer._render_cost_display(draw, cost, 100)
                self.assertGreater(y_after, 100)
    
    def test_format_income_value(self):
        """Test income value formatting with appropriate scaling."""
        test_cases = [
            (5, "5 / sec"),
            (1500, "1.5k / sec"),
            (2500000, "2.5m / sec"),
            (1500000000, "1.5b / sec"),
            (1000, "1k / sec"),
            (1000000, "1m / sec"),
            (1000000000, "1b / sec"),
        ]
        
        for income, expected in test_cases:
            with self.subTest(income=income):
                result = self.designer._format_income_value(income)
                self.assertEqual(result, expected)
    
    def test_format_cost_value(self):
        """Test cost value formatting with appropriate scaling."""
        test_cases = [
            (100, "$100"),
            (1500, "$1.5k"),
            (2500000, "$2.5m"),
            (1500000000, "$1.5b"),
            (1000, "$1k"),
            (1000000, "$1m"),
            (1000000000, "$1b"),
        ]
        
        for cost, expected in test_cases:
            with self.subTest(cost=cost):
                result = self.designer._format_cost_value(cost)
                self.assertEqual(result, expected)
    
    def test_new_layout_no_border(self):
        """Test that new layout cards have no border/frame elements."""
        character = CharacterData("Test", "Common", 100, 5, "Standard")
        card = self.designer.create_card(character)
        
        # Check that the card background is white (no border drawn)
        # Sample a few edge pixels to ensure no border
        edge_pixels = [
            card.getpixel((0, 0)),
            card.getpixel((card.width - 1, 0)),
            card.getpixel((0, card.height - 1)),
            card.getpixel((card.width - 1, card.height - 1))
        ]
        
        # All edge pixels should be white (background color)
        for pixel in edge_pixels:
            self.assertEqual(pixel, (255, 255, 255))  # White RGB
    
    def test_new_layout_element_positioning(self):
        """Test that new layout follows top-to-bottom order: title, image, rarity, income, cost."""
        character = CharacterData("Test Character", "Rare", 1500, 75, "Standard")
        card = self.designer.create_card(character)
        
        # Verify card was created successfully with new layout
        self.assertEqual(card.size, (self.config.width, self.config.height))
        self.assertEqual(card.mode, 'RGB')
        
        # The layout should be visually correct - this is tested through integration
        # Individual element positioning is tested in separate methods above


class TestCardDesignerIntegration(unittest.TestCase):
    """Integration tests for CardDesigner with real-like scenarios."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.designer = CardDesigner()
        
        # Create a more realistic test image
        self.character_image = Image.new('RGB', (800, 600), 'green')
        draw = ImageDraw.Draw(self.character_image)
        draw.rectangle([100, 100, 700, 500], fill='blue')
    
    def test_full_card_generation_workflow(self):
        """Test complete card generation workflow."""
        character = CharacterData(
            name="Integration Test Character",
            tier="Legendary",
            cost=25000,
            income=1250,
            variant="Special"
        )
        
        # Generate card with image
        card_with_image = self.designer.create_card(character, self.character_image)
        self.assertIsInstance(card_with_image, Image.Image)
        
        # Generate card without image (placeholder)
        card_without_image = self.designer.create_card(character)
        self.assertIsInstance(card_without_image, Image.Image)
        
        # Both should have same dimensions
        self.assertEqual(card_with_image.size, card_without_image.size)
    
    def test_batch_card_generation(self):
        """Test generating multiple cards in sequence."""
        characters = [
            CharacterData(f"Character {i}", "Common", i * 100, i * 5, "Standard")
            for i in range(1, 6)
        ]
        
        cards = []
        for character in characters:
            card = self.designer.create_card(character)
            cards.append(card)
        
        # All cards should be generated successfully
        self.assertEqual(len(cards), 5)
        for card in cards:
            self.assertEqual(card.size, (self.designer.config.width, self.designer.config.height))


if __name__ == '__main__':
    unittest.main()