"""
Unit tests for the OutputManager class.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from card_generator.output_manager import OutputManager
from card_generator.config import OutputConfig
from card_generator.data_models import CharacterData


class TestOutputManager(unittest.TestCase):
    """Test cases for OutputManager functionality."""
    
    def setUp(self):
        """Set up test fixtures with temporary directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test configuration with temporary directories
        self.test_config = OutputConfig(
            individual_cards_dir=str(self.temp_path / 'individual_cards'),
            print_sheets_dir=str(self.temp_path / 'print_sheets'),
            formats=('PNG', 'PDF'),
            image_quality=95,
            card_filename_template='{name}_{tier}_card.png',
            sheet_filename_template='print_sheet_{batch_number:03d}.png'
        )
        
        # Create test character data
        self.test_character = CharacterData(
            name="Test Character",
            tier="Rare",
            cost=100,
            income=50,
            variant="Standard"
        )
        
        # Create test image
        self.test_image = Image.new('RGB', (100, 100), 'red')
        
        # Initialize OutputManager with test config
        self.output_manager = OutputManager(self.test_config)
    
    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_creates_directories(self):
        """Test that OutputManager creates required directories on initialization."""
        cards_dir = Path(self.test_config.individual_cards_dir)
        sheets_dir = Path(self.test_config.print_sheets_dir)
        
        self.assertTrue(cards_dir.exists())
        self.assertTrue(sheets_dir.exists())
        self.assertTrue(cards_dir.is_dir())
        self.assertTrue(sheets_dir.is_dir())
    
    def test_save_individual_card_png(self):
        """Test saving individual card in PNG format."""
        filepath = self.output_manager.save_individual_card(
            self.test_image, self.test_character, 'PNG'
        )
        
        # Check file was created
        self.assertTrue(Path(filepath).exists())
        self.assertTrue(filepath.endswith('.png'))
        self.assertIn('Test_Character_Rare_card.png', filepath)
        
        # Verify image can be loaded
        saved_image = Image.open(filepath)
        self.assertEqual(saved_image.size, (100, 100))
    
    def test_save_individual_card_pdf(self):
        """Test saving individual card in PDF format."""
        filepath = self.output_manager.save_individual_card(
            self.test_image, self.test_character, 'PDF'
        )
        
        # Check file was created
        self.assertTrue(Path(filepath).exists())
        self.assertTrue(filepath.endswith('.pdf'))
        self.assertIn('Test_Character_Rare_card.pdf', filepath)
    
    def test_save_individual_card_unsupported_format(self):
        """Test that unsupported format raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.output_manager.save_individual_card(
                self.test_image, self.test_character, 'JPEG'
            )
        
        self.assertIn("Unsupported format", str(context.exception))
    
    def test_save_print_sheet_png(self):
        """Test saving print sheet in PNG format."""
        sheet_image = Image.new('RGB', (200, 200), 'blue')
        
        filepath = self.output_manager.save_print_sheet(sheet_image, 1, 'PNG')
        
        # Check file was created
        self.assertTrue(Path(filepath).exists())
        self.assertTrue(filepath.endswith('.png'))
        self.assertIn('print_sheet_001.png', filepath)
        
        # Verify image can be loaded
        saved_image = Image.open(filepath)
        self.assertEqual(saved_image.size, (200, 200))
    
    def test_save_print_sheet_pdf(self):
        """Test saving print sheet in PDF format."""
        sheet_image = Image.new('RGB', (200, 200), 'blue')
        
        filepath = self.output_manager.save_print_sheet(sheet_image, 5, 'PDF')
        
        # Check file was created
        self.assertTrue(Path(filepath).exists())
        self.assertTrue(filepath.endswith('.pdf'))
        self.assertIn('print_sheet_005.pdf', filepath)
    
    def test_batch_process_cards_success(self):
        """Test successful batch processing of cards."""
        # Create test data
        characters = [
            CharacterData("Char1", "Common", 10, 5, "Standard"),
            CharacterData("Char2", "Rare", 20, 10, "Standard"),
            CharacterData("Char3", "Epic", 30, 15, "Standard")
        ]
        
        cards_data = [(self.test_image, char) for char in characters]
        
        # Mock progress callback
        progress_callback = Mock()
        
        # Process cards
        results = self.output_manager.batch_process_cards(cards_data, progress_callback)
        
        # Check results
        self.assertEqual(results['total_cards'], 3)
        self.assertEqual(results['successful_cards'], 3)
        self.assertEqual(results['failed_cards'], 0)
        self.assertEqual(len(results['saved_files']), 6)  # 3 cards × 2 formats
        self.assertEqual(len(results['errors']), 0)
        
        # Check progress callback was called
        self.assertEqual(progress_callback.call_count, 3)
    
    def test_batch_process_cards_with_errors(self):
        """Test batch processing with some failures."""
        # Create character with problematic name
        bad_character = CharacterData("Bad<>Name", "Common", 10, 5, "Standard")
        good_character = CharacterData("Good Name", "Rare", 20, 10, "Standard")
        
        cards_data = [(self.test_image, bad_character), (self.test_image, good_character)]
        
        # Mock save method to fail for bad character
        original_save = self.output_manager.save_individual_card
        def mock_save(image, character, format):
            if "Bad" in character.name:
                raise IOError("Simulated save error")
            return original_save(image, character, format)
        
        with patch.object(self.output_manager, 'save_individual_card', side_effect=mock_save):
            results = self.output_manager.batch_process_cards(cards_data)
        
        # Check results
        self.assertEqual(results['total_cards'], 2)
        self.assertEqual(results['successful_cards'], 1)
        self.assertEqual(results['failed_cards'], 1)
        self.assertEqual(len(results['errors']), 1)
    
    def test_batch_process_print_sheets(self):
        """Test batch processing of print sheets."""
        sheets = [
            Image.new('RGB', (200, 200), 'red'),
            Image.new('RGB', (200, 200), 'green'),
            Image.new('RGB', (200, 200), 'blue')
        ]
        
        progress_callback = Mock()
        
        results = self.output_manager.batch_process_print_sheets(sheets, progress_callback)
        
        # Check results
        self.assertEqual(results['total_sheets'], 3)
        self.assertEqual(results['successful_sheets'], 3)
        self.assertEqual(results['failed_sheets'], 0)
        self.assertEqual(len(results['saved_files']), 6)  # 3 sheets × 2 formats
        self.assertEqual(len(results['errors']), 0)
        
        # Check progress callback was called
        self.assertEqual(progress_callback.call_count, 3)
    
    def test_clean_output_directories(self):
        """Test cleaning output directories."""
        # Create some test files
        cards_dir = Path(self.test_config.individual_cards_dir)
        sheets_dir = Path(self.test_config.print_sheets_dir)
        
        test_card_file = cards_dir / 'test_card.png'
        test_sheet_file = sheets_dir / 'test_sheet.png'
        
        test_card_file.write_text('test')
        test_sheet_file.write_text('test')
        
        # Verify files exist
        self.assertTrue(test_card_file.exists())
        self.assertTrue(test_sheet_file.exists())
        
        # Clean directories
        self.output_manager.clean_output_directories()
        
        # Verify files are gone
        self.assertFalse(test_card_file.exists())
        self.assertFalse(test_sheet_file.exists())
        
        # Verify directories still exist
        self.assertTrue(cards_dir.exists())
        self.assertTrue(sheets_dir.exists())
    
    def test_get_output_summary(self):
        """Test getting output summary information."""
        # Create some test files
        cards_dir = Path(self.test_config.individual_cards_dir)
        sheets_dir = Path(self.test_config.print_sheets_dir)
        
        # Create test files
        (cards_dir / 'card1.png').write_text('test')
        (cards_dir / 'card2.png').write_text('test')
        (sheets_dir / 'sheet1.png').write_text('test')
        
        summary = self.output_manager.get_output_summary()
        
        # Check summary
        self.assertEqual(summary['individual_cards_count'], 2)
        self.assertEqual(summary['print_sheets_count'], 1)
        self.assertEqual(summary['total_files'], 3)
        self.assertEqual(summary['supported_formats'], ['PNG', 'PDF'])
        self.assertEqual(summary['individual_cards_dir'], self.test_config.individual_cards_dir)
        self.assertEqual(summary['print_sheets_dir'], self.test_config.print_sheets_dir)
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test various problematic filenames
        test_cases = [
            ("Normal Name", "Normal_Name"),
            ("Name<>With:Invalid/Chars", "Name_With_Invalid_Chars"),
            ("Name\\With|More?Invalid*Chars", "Name_With_More_Invalid_Chars"),
            ("  Leading and trailing spaces  ", "Leading_and_trailing_spaces"),
            ("Multiple___Underscores", "Multiple_Underscores"),
            ("", "unnamed"),
            ("A" * 150, "A" * 100),  # Test length limit
        ]
        
        for original, expected in test_cases:
            with self.subTest(original=original):
                result = self.output_manager._sanitize_filename(original)
                self.assertEqual(result, expected)
    
    def test_save_with_io_error(self):
        """Test handling of IO errors during save operations."""
        # Mock PIL Image.save to raise an exception
        with patch.object(Image.Image, 'save', side_effect=IOError("Disk full")):
            with self.assertRaises(IOError) as context:
                self.output_manager.save_individual_card(
                    self.test_image, self.test_character, 'PNG'
                )
            
            self.assertIn("Could not save card file", str(context.exception))
    
    def test_default_configuration(self):
        """Test OutputManager with default configuration."""
        # Create OutputManager without config
        default_manager = OutputManager()
        
        # Check that it uses default config values
        self.assertEqual(default_manager.config.individual_cards_dir, 'output/individual_cards')
        self.assertEqual(default_manager.config.print_sheets_dir, 'output/print_sheets')
        self.assertEqual(default_manager.config.formats, ('PNG', 'PDF'))


class TestOutputManagerIntegration(unittest.TestCase):
    """Integration tests for OutputManager with real file operations."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        self.test_config = OutputConfig(
            individual_cards_dir=str(self.temp_path / 'cards'),
            print_sheets_dir=str(self.temp_path / 'sheets'),
            formats=('PNG',),  # Only PNG for faster tests
        )
        
        self.output_manager = OutputManager(self.test_config)
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow_integration(self):
        """Test complete workflow from card creation to file output."""
        # Create test characters
        characters = [
            CharacterData("Hero Alpha", "Legendary", 500, 100, "Standard"),
            CharacterData("Villain Beta", "Epic", 300, 75, "Special"),
        ]
        
        # Create test images
        card_images = [
            Image.new('RGB', (100, 150), 'gold'),
            Image.new('RGB', (100, 150), 'purple')
        ]
        
        # Create print sheet
        sheet_image = Image.new('RGB', (300, 200), 'white')
        
        # Process individual cards
        cards_data = list(zip(card_images, characters))
        card_results = self.output_manager.batch_process_cards(cards_data)
        
        # Process print sheet
        sheet_results = self.output_manager.batch_process_print_sheets([sheet_image])
        
        # Verify results
        self.assertEqual(card_results['successful_cards'], 2)
        self.assertEqual(sheet_results['successful_sheets'], 1)
        
        # Verify files exist
        cards_dir = Path(self.test_config.individual_cards_dir)
        sheets_dir = Path(self.test_config.print_sheets_dir)
        
        card_files = list(cards_dir.glob('*.png'))
        sheet_files = list(sheets_dir.glob('*.png'))
        
        self.assertEqual(len(card_files), 2)
        self.assertEqual(len(sheet_files), 1)
        
        # Verify file contents
        for card_file in card_files:
            saved_image = Image.open(card_file)
            self.assertEqual(saved_image.size, (100, 150))
        
        saved_sheet = Image.open(sheet_files[0])
        self.assertEqual(saved_sheet.size, (300, 200))
        
        # Test summary
        summary = self.output_manager.get_output_summary()
        self.assertEqual(summary['total_files'], 3)


if __name__ == '__main__':
    unittest.main()