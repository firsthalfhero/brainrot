"""
Comprehensive integration tests using sample characters from the CSV database.
Tests the complete workflow from CSV loading to card generation.
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from PIL import Image
import csv

from card_generator.data_loader import CSVDataLoader
from card_generator.image_processor import ImageProcessor
from card_generator.card_designer import CardDesigner
from card_generator.print_layout import PrintLayoutManager
from card_generator.output_manager import OutputManager
from card_generator.config import CardConfig, PrintConfig, OutputConfig


class TestComprehensiveIntegration(unittest.TestCase):
    """Integration tests using real CSV data and complete workflow."""
    
    def setUp(self):
        """Set up test environment with temporary directories."""
        self.test_dir = tempfile.mkdtemp()
        self.images_dir = os.path.join(self.test_dir, 'images')
        self.output_dir = os.path.join(self.test_dir, 'output')
        os.makedirs(self.images_dir)
        os.makedirs(self.output_dir)
        
        # Create test CSV with sample characters
        self.csv_path = os.path.join(self.test_dir, 'test_characters.csv')
        self.create_test_csv()
        
        # Create test images for some characters
        self.create_test_images()
        
        # Initialize components
        self.data_loader = CSVDataLoader()
        self.image_processor = ImageProcessor()
        self.card_designer = CardDesigner(CardConfig())
        self.print_layout = PrintLayoutManager(PrintConfig())
        self.output_manager = OutputManager(OutputConfig(
            individual_cards_dir=os.path.join(self.output_dir, 'cards'),
            print_sheets_dir=os.path.join(self.output_dir, 'sheets')
        ))
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def create_test_csv(self):
        """Create a test CSV with sample characters from the real database."""
        test_characters = [
            ["Character Name", "Tier", "Cost", "Income per Second", "Cost/Income Ratio", "Variant Type"],
            ["Noobini Pizzanini", "Common", "25", "1", "25.0", "Standard"],
            ["Tim Cheese", "Common", "500", "5", "100.0", "Standard"],
            ["FluriFlura", "Common", "750", "7", "107.1", "Standard"],
            ["Trippi Troppi", "Rare", "2000", "15", "133.3", "Standard"],
            ["Tung Tung Tung Sahur", "Rare", "3000", "25", "120.0", "Standard"],
            ["Ballerina Cappuccina", "Epic", "5000", "50", "100.0", "Standard"],
            ["Matteo", "Legendary", "10000", "100", "100.0", "Standard"],
            ["Las Tralaleritas", "Mythic", "25000", "300", "83.3", "Standard"]
        ]
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(test_characters)
    
    def create_test_images(self):
        """Create test images for some characters."""
        # Create simple colored rectangles as test images
        colors = [
            (255, 0, 0),    # Red for Noobini Pizzanini
            (0, 255, 0),    # Green for Tim Cheese
            (0, 0, 255),    # Blue for FluriFlura
            (255, 255, 0),  # Yellow for Trippi Troppi
        ]
        
        character_names = [
            "Noobini Pizzanini",
            "Tim Cheese", 
            "FluriFlura",
            "Trippi Troppi"
        ]
        
        for name, color in zip(character_names, colors):
            img = Image.new('RGB', (400, 400), color)
            img.save(os.path.join(self.images_dir, f"{name}.png"))
    
    def test_complete_workflow_with_real_data(self):
        """Test the complete workflow from CSV to generated cards."""
        # Load characters from CSV
        data_loader = CSVDataLoader(self.csv_path, self.images_dir)
        characters = data_loader.load_characters()
        
        # Verify we loaded the expected characters
        self.assertEqual(len(characters), 8)  # 8 test characters
        
        # Verify character data
        noobini = next(c for c in characters if c.name == "Noobini Pizzanini")
        self.assertEqual(noobini.tier, "Common")
        self.assertEqual(noobini.cost, 25)
        self.assertEqual(noobini.income, 1)
        
        # Process characters and generate cards
        generated_cards = []
        for character in characters[:4]:  # Test first 4 characters
            # Load or create image
            if character.image_path and os.path.exists(character.image_path):
                image = self.image_processor.load_image(character.image_path)
            else:
                image = self.image_processor.create_placeholder(
                    character.name, character.tier, (400, 400)
                )
            
            # Generate card
            card = self.card_designer.create_card(character, image)
            generated_cards.append((character, card))
        
        # Verify cards were generated
        self.assertEqual(len(generated_cards), 4)
        
        # Verify card dimensions
        for character, card in generated_cards:
            self.assertEqual(card.size, (1745, 2468))  # A5 at 300 DPI (adjusted for print layout)
        
        # Create print layout
        cards_only = [card for _, card in generated_cards]
        print_sheets = self.print_layout.arrange_cards_for_printing(cards_only)
        
        # Verify print sheets
        self.assertGreater(len(print_sheets), 0)
        for sheet in print_sheets:
            self.assertEqual(sheet.size, (3508, 2480))  # A4 landscape at 300 DPI
        
        # Save outputs
        for character, card in generated_cards:
            self.output_manager.save_individual_card(card, character)
        
        for i, sheet in enumerate(print_sheets):
            self.output_manager.save_print_sheet(sheet, i + 1)
        
        # Verify files were created
        cards_dir = self.output_manager.config.individual_cards_dir
        sheets_dir = self.output_manager.config.print_sheets_dir
        
        self.assertTrue(os.path.exists(cards_dir))
        self.assertTrue(os.path.exists(sheets_dir))
        
        # Check individual card files
        card_files = os.listdir(cards_dir)
        self.assertEqual(len(card_files), 4)
        
        # Check print sheet files
        sheet_files = os.listdir(sheets_dir)
        self.assertGreater(len(sheet_files), 0)
    
    def test_error_handling_integration(self):
        """Test error handling in the complete workflow."""
        # Create CSV with problematic data
        problematic_csv = os.path.join(self.test_dir, 'problematic.csv')
        with open(problematic_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows([
                ["Character Name", "Tier", "Cost", "Income per Second", "Cost/Income Ratio", "Variant Type"],
                ["Valid Character", "Common", "100", "5", "20.0", "Standard"],
                ["Invalid Cost", "Rare", "invalid", "10", "0", "Standard"],
                ["Missing Image", "Epic", "1000", "20", "50.0", "Standard"],
            ])
        
        # Load characters (should handle invalid data gracefully)
        data_loader = CSVDataLoader(problematic_csv, self.images_dir)
        characters = data_loader.load_characters()
        
        # Should have loaded valid characters and skipped invalid ones
        self.assertGreater(len(characters), 0)
        
        # Verify valid character was loaded correctly
        valid_char = next((c for c in characters if c.name == "Valid Character"), None)
        self.assertIsNotNone(valid_char)
        self.assertEqual(valid_char.cost, 100)
    
    def test_different_tier_handling(self):
        """Test that different tiers are handled correctly throughout the workflow."""
        data_loader = CSVDataLoader(self.csv_path, self.images_dir)
        characters = data_loader.load_characters()
        
        # Group characters by tier
        tiers = {}
        for character in characters:
            if character.tier not in tiers:
                tiers[character.tier] = []
            tiers[character.tier].append(character)
        
        # Verify we have multiple tiers
        self.assertGreater(len(tiers), 1)
        
        # Test card generation for each tier
        for tier, tier_characters in tiers.items():
            character = tier_characters[0]  # Test first character of each tier
            
            # Create placeholder image
            image = self.image_processor.create_placeholder(
                character.name, character.tier, (400, 400)
            )
            
            # Generate card
            card = self.card_designer.create_card(character, image)
            
            # Verify card was created successfully
            self.assertIsNotNone(card)
            self.assertEqual(card.size, (1745, 2468))


if __name__ == '__main__':
    unittest.main()