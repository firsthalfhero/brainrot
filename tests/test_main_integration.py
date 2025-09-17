"""
Integration tests for the main application entry point and end-to-end card generation.
"""

import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import main
from card_generator.cli import CardGeneratorCLI
from card_generator.data_models import CharacterData
from card_generator.config import CardConfig, PrintConfig, OutputConfig


class TestMainIntegration(unittest.TestCase):
    """Test the main application entry point and full workflow integration."""
    
    def setUp(self):
        """Set up test environment with temporary directories and sample data."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create sample CSV file
        self.csv_content = """Character Name,Tier,Cost,Income per Second,Cost/Income Ratio,Variant Type
"Tim Cheese","Common",100,10,"10.0","Standard"
"FluriFlura","Rare",500,50,"10.0","Standard"
"Test Character","Epic",1000,100,"10.0","Special\""""
        
        with open('steal_a_brainrot_complete_database.csv', 'w') as f:
            f.write(self.csv_content)
        
        # Create images directory with sample images
        os.makedirs('images', exist_ok=True)
        
        # Create sample images
        for name in ['Tim Cheese', 'FluriFlura']:
            img = Image.new('RGB', (300, 400), color='red')
            img.save(f'images/{name}.png')
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_environment_check_success(self):
        """Test successful environment validation."""
        result = main.check_environment()
        self.assertTrue(result)
    
    def test_environment_check_missing_csv(self):
        """Test environment check with missing CSV file."""
        os.remove('steal_a_brainrot_complete_database.csv')
        
        with patch('builtins.print') as mock_print:
            result = main.check_environment()
            self.assertFalse(result)
            mock_print.assert_called()
    
    def test_environment_check_missing_images_dir(self):
        """Test environment check with missing images directory."""
        shutil.rmtree('images')
        
        with patch('builtins.print') as mock_print:
            result = main.check_environment()
            self.assertFalse(result)
            mock_print.assert_called()
    
    def test_environment_check_empty_images_dir(self):
        """Test environment check with empty images directory."""
        # Remove all images
        for file in Path('images').iterdir():
            file.unlink()
        
        with patch('builtins.print') as mock_print:
            result = main.check_environment()
            self.assertFalse(result)
            mock_print.assert_called()
    
    def test_main_no_args_shows_help(self):
        """Test that main with no arguments shows help message."""
        with patch('sys.argv', ['main.py']):
            with patch('builtins.print') as mock_print:
                result = main.main()
                self.assertEqual(result, 0)
                mock_print.assert_called()
    
    def test_main_help_flag(self):
        """Test main with help flag."""
        with patch('sys.argv', ['main.py', '--help']):
            with patch('main.cli_main') as mock_cli:
                mock_cli.return_value = 0
                result = main.main()
                self.assertEqual(result, 0)
    
    def test_main_keyboard_interrupt(self):
        """Test main handles keyboard interrupt gracefully."""
        with patch('sys.argv', ['main.py', '--all']):
            with patch('main.cli_main', side_effect=KeyboardInterrupt):
                with patch('builtins.print') as mock_print:
                    result = main.main()
                    self.assertEqual(result, 130)
                    mock_print.assert_called_with("\nOperation interrupted by user")
    
    def test_main_unexpected_error(self):
        """Test main handles unexpected errors gracefully."""
        with patch('sys.argv', ['main.py', '--all']):
            with patch('main.cli_main', side_effect=Exception("Test error")):
                with patch('builtins.print') as mock_print:
                    result = main.main()
                    self.assertEqual(result, 1)
                    mock_print.assert_called_with("Unexpected error: Test error")


class TestEndToEndCardGeneration(unittest.TestCase):
    """Test complete end-to-end card generation workflow."""
    
    def setUp(self):
        """Set up test environment with temporary directories and sample data."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create sample CSV file
        self.csv_content = """Character Name,Tier,Cost,Income per Second,Cost/Income Ratio,Variant Type
"Tim Cheese","Common",100,10,"10.0","Standard"
"FluriFlura","Rare",500,50,"10.0","Standard\""""
        
        with open('steal_a_brainrot_complete_database.csv', 'w') as f:
            f.write(self.csv_content)
        
        # Create images directory with sample images
        os.makedirs('images', exist_ok=True)
        
        # Create sample images
        for name in ['Tim Cheese', 'FluriFlura']:
            img = Image.new('RGB', (300, 400), color='red')
            img.save(f'images/{name}.png')
        
        self.cli = CardGeneratorCLI()
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_generate_single_character_card(self):
        """Test generating a card for a single character."""
        args = ['--names', 'Tim Cheese', '--quiet']
        result = self.cli.run(args)
        
        # Should succeed
        self.assertEqual(result, 0)
        
        # Check output files were created
        output_dir = Path('output')
        self.assertTrue(output_dir.exists())
        
        individual_cards_dir = output_dir / 'individual_cards'
        self.assertTrue(individual_cards_dir.exists())
        
        # Should have at least one card file
        card_files = list(individual_cards_dir.glob('*.png'))
        self.assertGreater(len(card_files), 0)
    
    def test_generate_all_characters_cards(self):
        """Test generating cards for all characters."""
        args = ['--all', '--quiet']
        result = self.cli.run(args)
        
        # Should succeed
        self.assertEqual(result, 0)
        
        # Check output files were created
        output_dir = Path('output')
        individual_cards_dir = output_dir / 'individual_cards'
        print_sheets_dir = output_dir / 'print_sheets'
        
        self.assertTrue(individual_cards_dir.exists())
        self.assertTrue(print_sheets_dir.exists())
        
        # Should have card files for both characters
        card_files = list(individual_cards_dir.glob('*.png'))
        self.assertGreaterEqual(len(card_files), 2)
        
        # Should have at least one print sheet
        sheet_files = list(print_sheets_dir.glob('*.png'))
        self.assertGreater(len(sheet_files), 0)
    
    def test_generate_cards_by_tier(self):
        """Test generating cards filtered by tier."""
        args = ['--tiers', 'Common', '--quiet']
        result = self.cli.run(args)
        
        # Should succeed
        self.assertEqual(result, 0)
        
        # Check that only Common tier cards were generated
        output_dir = Path('output')
        individual_cards_dir = output_dir / 'individual_cards'
        
        card_files = list(individual_cards_dir.glob('*.png'))
        self.assertGreater(len(card_files), 0)
        
        # Should have fewer cards than total characters
        self.assertLess(len(card_files), 2)
    
    def test_generate_individual_cards_only(self):
        """Test generating only individual cards, no print sheets."""
        args = ['--all', '--individual-only', '--quiet']
        result = self.cli.run(args)
        
        # Should succeed
        self.assertEqual(result, 0)
        
        # Check output structure
        output_dir = Path('output')
        individual_cards_dir = output_dir / 'individual_cards'
        print_sheets_dir = output_dir / 'print_sheets'
        
        self.assertTrue(individual_cards_dir.exists())
        
        # Should have individual cards
        card_files = list(individual_cards_dir.glob('*.png'))
        self.assertGreater(len(card_files), 0)
        
        # Should not have print sheets (or empty directory)
        if print_sheets_dir.exists():
            sheet_files = list(print_sheets_dir.glob('*.png'))
            self.assertEqual(len(sheet_files), 0)
    
    def test_generate_print_sheets_only(self):
        """Test generating only print sheets, no individual cards."""
        args = ['--all', '--print-sheets-only', '--quiet']
        result = self.cli.run(args)
        
        # Should succeed
        self.assertEqual(result, 0)
        
        # Check output structure
        output_dir = Path('output')
        individual_cards_dir = output_dir / 'individual_cards'
        print_sheets_dir = output_dir / 'print_sheets'
        
        self.assertTrue(print_sheets_dir.exists())
        
        # Should have print sheets
        sheet_files = list(print_sheets_dir.glob('*.png'))
        self.assertGreater(len(sheet_files), 0)
        
        # Should not have individual cards (or empty directory)
        if individual_cards_dir.exists():
            card_files = list(individual_cards_dir.glob('*.png'))
            self.assertEqual(len(card_files), 0)
    
    def test_generate_cards_with_custom_output_dir(self):
        """Test generating cards with custom output directory."""
        custom_output = 'custom_output'
        args = ['--names', 'Tim Cheese', '--output-dir', custom_output, '--quiet']
        result = self.cli.run(args)
        
        # Should succeed
        self.assertEqual(result, 0)
        
        # Check custom output directory was used
        output_dir = Path(custom_output)
        self.assertTrue(output_dir.exists())
        
        individual_cards_dir = output_dir / 'individual_cards'
        self.assertTrue(individual_cards_dir.exists())
        
        card_files = list(individual_cards_dir.glob('*.png'))
        self.assertGreater(len(card_files), 0)
    
    def test_generate_cards_both_formats(self):
        """Test generating cards in both PNG and PDF formats."""
        args = ['--names', 'Tim Cheese', '--format', 'both', '--quiet']
        result = self.cli.run(args)
        
        # Should succeed
        self.assertEqual(result, 0)
        
        # Check both formats were generated
        output_dir = Path('output')
        individual_cards_dir = output_dir / 'individual_cards'
        
        png_files = list(individual_cards_dir.glob('*.png'))
        pdf_files = list(individual_cards_dir.glob('*.pdf'))
        
        self.assertGreater(len(png_files), 0)
        self.assertGreater(len(pdf_files), 0)
    
    def test_generate_cards_with_missing_images(self):
        """Test generating cards when some character images are missing."""
        # Remove one image
        os.remove('images/FluriFlura.png')
        
        args = ['--all', '--quiet']
        result = self.cli.run(args)
        
        # Should still succeed (with placeholders)
        self.assertEqual(result, 0)
        
        # Should still generate cards
        output_dir = Path('output')
        individual_cards_dir = output_dir / 'individual_cards'
        
        card_files = list(individual_cards_dir.glob('*.png'))
        self.assertGreater(len(card_files), 0)
    
    def test_generate_cards_with_images_only_filter(self):
        """Test generating cards only for characters with images."""
        # Remove one image
        os.remove('images/FluriFlura.png')
        
        args = ['--all', '--with-images-only', '--quiet']
        result = self.cli.run(args)
        
        # Should succeed
        self.assertEqual(result, 0)
        
        # Should generate fewer cards
        output_dir = Path('output')
        individual_cards_dir = output_dir / 'individual_cards'
        
        card_files = list(individual_cards_dir.glob('*.png'))
        self.assertGreater(len(card_files), 0)
        self.assertLess(len(card_files), 2)  # Should be less than total characters
    
    def test_preview_mode_no_generation(self):
        """Test preview mode doesn't generate any files."""
        args = ['--all', '--preview']
        
        with patch('builtins.print') as mock_print:
            result = self.cli.run(args)
            
            # Should succeed
            self.assertEqual(result, 0)
            
            # Should show preview output
            mock_print.assert_called()
        
        # Should not create output files
        output_dir = Path('output')
        if output_dir.exists():
            individual_cards_dir = output_dir / 'individual_cards'
            if individual_cards_dir.exists():
                card_files = list(individual_cards_dir.glob('*.png'))
                self.assertEqual(len(card_files), 0)
    
    def test_list_commands_no_generation(self):
        """Test list commands don't generate any files."""
        for list_arg in ['--list-characters', '--list-tiers', '--list-variants', '--stats']:
            with self.subTest(list_arg=list_arg):
                args = [list_arg]
                
                with patch('builtins.print') as mock_print:
                    result = self.cli.run(args)
                    
                    # Should succeed
                    self.assertEqual(result, 0)
                    
                    # Should show list output
                    mock_print.assert_called()
                
                # Should not create output files
                output_dir = Path('output')
                if output_dir.exists():
                    individual_cards_dir = output_dir / 'individual_cards'
                    if individual_cards_dir.exists():
                        card_files = list(individual_cards_dir.glob('*.png'))
                        self.assertEqual(len(card_files), 0)
    
    def test_error_handling_invalid_csv(self):
        """Test error handling with invalid CSV file."""
        # Create invalid CSV
        with open('steal_a_brainrot_complete_database.csv', 'w') as f:
            f.write("Invalid,CSV,Content\nBad,Data,Here")
        
        args = ['--all', '--quiet']
        result = self.cli.run(args)
        
        # Should fail gracefully
        self.assertNotEqual(result, 0)
    
    def test_error_handling_no_selection_criteria(self):
        """Test error handling when no selection criteria provided."""
        args = ['--quiet']  # No selection criteria
        result = self.cli.run(args)
        
        # Should fail with error
        self.assertNotEqual(result, 0)
    
    def test_progress_reporting_verbose_mode(self):
        """Test progress reporting in verbose mode."""
        args = ['--names', 'Tim Cheese', '--verbose']
        
        with patch('builtins.print') as mock_print:
            result = self.cli.run(args)
            
            # Should succeed
            self.assertEqual(result, 0)
            
            # Should show verbose output
            mock_print.assert_called()
            
            # Check that progress messages were printed
            print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
            progress_messages = [msg for msg in print_calls if '✓' in str(msg) or 'Generating' in str(msg)]
            self.assertGreater(len(progress_messages), 0)


if __name__ == '__main__':
    unittest.main()