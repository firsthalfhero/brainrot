"""
Integration tests for OutputManager with other card generator components.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image

from card_generator import (
    CharacterData, CardConfig, PrintConfig, OutputConfig,
    CardDesigner, PrintLayoutManager, OutputManager
)


class TestOutputManagerIntegration(unittest.TestCase):
    """Integration tests for OutputManager with real card generation workflow."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create configurations
        self.card_config = CardConfig(width=200, height=300)  # Smaller for faster tests
        self.print_config = PrintConfig(sheet_width=500, sheet_height=400)
        self.output_config = OutputConfig(
            individual_cards_dir=str(self.temp_path / 'cards'),
            print_sheets_dir=str(self.temp_path / 'sheets'),
            formats=('PNG',)  # Only PNG for faster tests
        )
        
        # Initialize components
        self.card_designer = CardDesigner(self.card_config)
        self.print_manager = PrintLayoutManager(self.print_config, self.card_config)
        self.output_manager = OutputManager(self.output_config)
        
        # Create test characters
        self.characters = [
            CharacterData("Alpha Hero", "Legendary", 1000, 200, "Standard"),
            CharacterData("Beta Villain", "Epic", 500, 100, "Special"),
            CharacterData("Gamma Support", "Rare", 250, 50, "Standard"),
        ]
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_card_generation_workflow(self):
        """Test complete workflow from character data to saved files."""
        # Step 1: Generate card images
        card_images = []
        for character in self.characters:
            # Create a simple test image for each character
            test_image = Image.new('RGB', (100, 100), 'red')
            card_image = self.card_designer.create_card(character, test_image)
            card_images.append(card_image)
        
        # Verify cards were created with correct dimensions
        self.assertEqual(len(card_images), 3)
        for card in card_images:
            self.assertEqual(card.size, (self.card_config.width, self.card_config.height))
        
        # Step 2: Save individual cards
        cards_data = list(zip(card_images, self.characters))
        card_results = self.output_manager.batch_process_cards(cards_data)
        
        # Verify individual card results
        self.assertEqual(card_results['successful_cards'], 3)
        self.assertEqual(card_results['failed_cards'], 0)
        self.assertEqual(len(card_results['saved_files']), 3)  # 3 cards × 1 format
        
        # Step 3: Create print sheets
        print_sheets = self.print_manager.arrange_cards_for_printing(card_images)
        
        # Verify print sheets were created (3 cards = 2 sheets with 2 cards per sheet)
        self.assertEqual(len(print_sheets), 2)  # 3 cards = 2 sheets (2+1)
        
        # Step 4: Save print sheets
        sheet_results = self.output_manager.batch_process_print_sheets(print_sheets)
        
        # Verify print sheet results
        self.assertEqual(sheet_results['successful_sheets'], 2)
        self.assertEqual(sheet_results['failed_sheets'], 0)
        self.assertEqual(len(sheet_results['saved_files']), 2)  # 2 sheets × 1 format
        
        # Step 5: Verify files exist on disk
        cards_dir = Path(self.output_config.individual_cards_dir)
        sheets_dir = Path(self.output_config.print_sheets_dir)
        
        card_files = list(cards_dir.glob('*.png'))
        sheet_files = list(sheets_dir.glob('*.png'))
        
        self.assertEqual(len(card_files), 3)
        self.assertEqual(len(sheet_files), 2)
        
        # Step 6: Verify file contents
        for card_file in card_files:
            saved_card = Image.open(card_file)
            self.assertEqual(saved_card.size, (self.card_config.width, self.card_config.height))
            saved_card.close()
        
        for sheet_file in sheet_files:
            saved_sheet = Image.open(sheet_file)
            self.assertEqual(saved_sheet.size, (self.print_config.sheet_width, self.print_config.sheet_height))
            saved_sheet.close()
        
        # Step 7: Verify output summary
        summary = self.output_manager.get_output_summary()
        self.assertEqual(summary['individual_cards_count'], 3)
        self.assertEqual(summary['print_sheets_count'], 2)
        self.assertEqual(summary['total_files'], 5)
    
    def test_workflow_with_progress_tracking(self):
        """Test workflow with progress tracking callbacks."""
        # Create progress tracking
        progress_updates = []
        
        def progress_callback(progress, item_name, error):
            progress_updates.append({
                'progress': progress,
                'item': item_name,
                'error': error
            })
        
        # Generate cards
        card_images = []
        for character in self.characters[:2]:  # Only 2 characters for simpler test
            test_image = Image.new('RGB', (100, 100), 'blue')
            card_image = self.card_designer.create_card(character, test_image)
            card_images.append(card_image)
        
        # Process with progress tracking
        cards_data = list(zip(card_images, self.characters[:2]))
        results = self.output_manager.batch_process_cards(cards_data, progress_callback)
        
        # Verify progress tracking
        self.assertEqual(len(progress_updates), 2)
        self.assertEqual(progress_updates[0]['progress'], 0.5)
        self.assertEqual(progress_updates[1]['progress'], 1.0)
        self.assertIsNone(progress_updates[0]['error'])
        self.assertIsNone(progress_updates[1]['error'])
        
        # Verify results
        self.assertEqual(results['successful_cards'], 2)
        self.assertEqual(results['failed_cards'], 0)
    
    def test_workflow_with_error_handling(self):
        """Test workflow error handling with mixed success/failure."""
        # Create one valid character and one with problematic name
        characters = [
            CharacterData("Valid Name", "Common", 100, 10, "Standard"),
            CharacterData("Invalid<>Name", "Rare", 200, 20, "Standard")
        ]
        
        # Generate cards
        card_images = []
        for character in characters:
            test_image = Image.new('RGB', (100, 100), 'green')
            card_image = self.card_designer.create_card(character, test_image)
            card_images.append(card_image)
        
        # Process cards (should handle the invalid filename gracefully)
        cards_data = list(zip(card_images, characters))
        results = self.output_manager.batch_process_cards(cards_data)
        
        # Both should succeed because filename sanitization handles invalid characters
        self.assertEqual(results['successful_cards'], 2)
        self.assertEqual(results['failed_cards'], 0)
        
        # Verify files were created with sanitized names
        cards_dir = Path(self.output_config.individual_cards_dir)
        card_files = list(cards_dir.glob('*.png'))
        self.assertEqual(len(card_files), 2)
        
        # Check that invalid characters were sanitized
        filenames = [f.name for f in card_files]
        self.assertTrue(any('Valid_Name' in name for name in filenames))
        self.assertTrue(any('Invalid_Name' in name for name in filenames))
        self.assertFalse(any('<' in name or '>' in name for name in filenames))
    
    def test_clean_and_regenerate_workflow(self):
        """Test cleaning output directories and regenerating files."""
        # Generate initial files
        character = self.characters[0]
        test_image = Image.new('RGB', (100, 100), 'yellow')
        card_image = self.card_designer.create_card(character, test_image)
        
        # Save initial files
        self.output_manager.save_individual_card(card_image, character)
        print_sheet = self.print_manager.create_print_sheet([card_image])
        self.output_manager.save_print_sheet(print_sheet, 1)
        
        # Verify files exist
        summary_before = self.output_manager.get_output_summary()
        self.assertEqual(summary_before['total_files'], 2)
        
        # Clean directories
        self.output_manager.clean_output_directories()
        
        # Verify files are gone
        summary_after_clean = self.output_manager.get_output_summary()
        self.assertEqual(summary_after_clean['total_files'], 0)
        
        # Regenerate files
        self.output_manager.save_individual_card(card_image, character)
        self.output_manager.save_print_sheet(print_sheet, 1)
        
        # Verify files are back
        summary_after_regen = self.output_manager.get_output_summary()
        self.assertEqual(summary_after_regen['total_files'], 2)


if __name__ == '__main__':
    unittest.main()