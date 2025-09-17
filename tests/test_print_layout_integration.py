"""
Integration test for PrintLayoutManager with CardDesigner.
"""

import unittest
import tempfile
import os
from PIL import Image

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_generator.print_layout import PrintLayoutManager
from card_generator.card_designer import CardDesigner
from card_generator.data_models import CharacterData
from card_generator.config import PrintConfig, CardConfig


class TestPrintLayoutIntegration(unittest.TestCase):
    """Integration tests for PrintLayoutManager with real card data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.card_config = CardConfig()
        self.print_config = PrintConfig()
        self.card_designer = CardDesigner(self.card_config)
        self.layout_manager = PrintLayoutManager(self.print_config, self.card_config)
        
        # Create test character data
        self.test_characters = [
            CharacterData(
                name="Test Character 1",
                tier="Rare",
                cost=1000,
                income=50,
                variant="Standard"
            ),
            CharacterData(
                name="Test Character 2",
                tier="Epic", 
                cost=5000,
                income=200,
                variant="Standard"
            ),
            CharacterData(
                name="Very Long Character Name That Should Wrap",
                tier="Legendary",
                cost=25000,
                income=1000,
                variant="Special"
            )
        ]
    
    def test_create_cards_and_print_sheet(self):
        """Test creating cards with CardDesigner and arranging them with PrintLayoutManager."""
        # Create cards using CardDesigner
        cards = []
        for character in self.test_characters[:2]:  # Use first 2 characters
            card = self.card_designer.create_card(character)
            self.assertEqual(card.size, (self.card_config.width, self.card_config.height))
            cards.append(card)
        
        # Create print sheet
        print_sheet = self.layout_manager.create_print_sheet(cards)
        
        # Verify print sheet dimensions
        self.assertEqual(print_sheet.size, (self.print_config.sheet_width, self.print_config.sheet_height))
        
        # Verify that the sheet contains content from both cards
        pixels = list(print_sheet.getdata())
        non_white_pixels = [p for p in pixels if p != (255, 255, 255)]
        self.assertGreater(len(non_white_pixels), 1000, "Print sheet should contain significant content from cards")
    
    def test_batch_processing(self):
        """Test processing multiple characters into print sheets."""
        # Create cards for all test characters
        cards = []
        for character in self.test_characters:
            card = self.card_designer.create_card(character)
            cards.append(card)
        
        # Arrange into print sheets
        print_sheets = self.layout_manager.arrange_cards_for_printing(cards)
        
        # Should create 2 sheets (2 cards on first sheet, 1 card on second sheet)
        self.assertEqual(len(print_sheets), 2)
        
        # Verify all sheets have correct dimensions
        for sheet in print_sheets:
            self.assertEqual(sheet.size, (self.print_config.sheet_width, self.print_config.sheet_height))
    
    def test_single_card_print_sheet(self):
        """Test creating a print sheet with a single card."""
        # Create one card
        card = self.card_designer.create_card(self.test_characters[0])
        
        # Create print sheet
        print_sheet = self.layout_manager.create_print_sheet([card])
        
        # Verify dimensions
        self.assertEqual(print_sheet.size, (self.print_config.sheet_width, self.print_config.sheet_height))
        
        # Verify card is centered (approximately)
        # The card should be roughly in the center of the sheet
        card_positions = self.layout_manager._calculate_card_positions(1)
        expected_x = (self.print_config.sheet_width - self.card_config.width) // 2
        expected_y = (self.print_config.sheet_height - self.card_config.height) // 2
        
        self.assertEqual(card_positions[0], (expected_x, expected_y))
    
    def test_cutting_guides_visibility(self):
        """Test that cutting guides are visible on the print sheet."""
        # Create cards
        cards = [self.card_designer.create_card(char) for char in self.test_characters[:2]]
        
        # Create print sheet
        print_sheet = self.layout_manager.create_print_sheet(cards)
        
        # Check for black pixels (cutting guides)
        pixels = list(print_sheet.getdata())
        black_pixels = [p for p in pixels if p == (0, 0, 0)]
        
        # Should have cutting guide pixels
        self.assertGreater(len(black_pixels), 50, "Print sheet should contain visible cutting guides")
    
    def test_different_tier_cards(self):
        """Test that cards with different tiers work correctly in print layout."""
        # Create cards with different tiers
        cards = []
        for character in self.test_characters:
            card = self.card_designer.create_card(character)
            cards.append(card)
        
        # Arrange into print sheets
        print_sheets = self.layout_manager.arrange_cards_for_printing(cards)
        
        # All sheets should be valid
        for sheet in print_sheets:
            self.assertEqual(sheet.size, (self.print_config.sheet_width, self.print_config.sheet_height))
            
            # Should contain non-white pixels (content)
            pixels = list(sheet.getdata())
            non_white_pixels = [p for p in pixels if p != (255, 255, 255)]
            self.assertGreater(len(non_white_pixels), 100)


if __name__ == '__main__':
    unittest.main()