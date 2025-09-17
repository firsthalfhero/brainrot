"""
Unit tests for the command-line interface.
"""

import unittest
import tempfile
import os
import shutil
import io
import sys
from unittest.mock import patch, MagicMock
from card_generator.cli import CardGeneratorCLI


class TestCardGeneratorCLI(unittest.TestCase):
    """Test cases for CardGeneratorCLI class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.test_dir, 'test_characters.csv')
        self.images_dir = os.path.join(self.test_dir, 'images')
        os.makedirs(self.images_dir)
        
        # Create sample CSV data
        self.sample_csv_content = '''Character Name,Tier,Cost,Income per Second,Cost/Income Ratio,Variant Type
"Tim Cheese","Common",100,5,"20.0","Standard"
"FluriFlura","Rare",500,10,"50.0","Standard"
"Epic Dragon","Epic",1000,25,"40.0","Special"
"Test Character","Common",50,2,"25.0","Standard"
'''
        
        # Write sample CSV file
        with open(self.csv_path, 'w', encoding='utf-8') as f:
            f.write(self.sample_csv_content)
        
        # Create sample image files
        test_images = ['Tim Cheese_1.png', 'FluriFlura_1.png']
        for image_name in test_images:
            image_path = os.path.join(self.images_dir, image_name)
            with open(image_path, 'w') as f:
                f.write('fake image content')
        
        self.cli = CardGeneratorCLI()
    
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.test_dir)
    
    def test_create_parser(self):
        """Test parser creation."""
        parser = self.cli.create_parser()
        self.assertIsNotNone(parser)
        
        # Test that it can parse basic arguments
        args = parser.parse_args(['--all'])
        self.assertTrue(args.all)
    
    def test_parse_selection_criteria(self):
        """Test parsing selection criteria from arguments."""
        parser = self.cli.create_parser()
        
        # Test basic criteria
        args = parser.parse_args(['--names', 'Tim Cheese', 'FluriFlura'])
        criteria = self.cli.parse_selection_criteria(args)
        self.assertEqual(criteria['names'], ['Tim Cheese', 'FluriFlura'])
        
        # Test complex criteria
        args = parser.parse_args([
            '--tiers', 'Common', 'Rare',
            '--min-cost', '100',
            '--max-cost', '1000',
            '--with-images-only',
            '--case-sensitive'
        ])
        criteria = self.cli.parse_selection_criteria(args)
        self.assertEqual(criteria['tiers'], ['Common', 'Rare'])
        self.assertEqual(criteria['min_cost'], 100)
        self.assertEqual(criteria['max_cost'], 1000)
        self.assertTrue(criteria['with_images_only'])
        self.assertTrue(criteria['case_sensitive'])
    
    def test_validate_args_success(self):
        """Test successful argument validation."""
        parser = self.cli.create_parser()
        
        # Valid arguments
        args = parser.parse_args(['--all'])
        self.assertTrue(self.cli.validate_args(args))
        
        args = parser.parse_args(['--names', 'Tim Cheese'])
        self.assertTrue(self.cli.validate_args(args))
        
        args = parser.parse_args(['--list-characters'])
        self.assertTrue(self.cli.validate_args(args))
    
    def test_validate_args_conflicts(self):
        """Test argument validation with conflicts."""
        parser = self.cli.create_parser()
        
        # Conflicting image options
        args = parser.parse_args(['--with-images-only', '--without-images-only'])
        self.assertFalse(self.cli.validate_args(args))
        
        # Conflicting output options
        args = parser.parse_args(['--individual-only', '--print-sheets-only'])
        self.assertFalse(self.cli.validate_args(args))
        
        # Invalid cost range
        args = parser.parse_args(['--min-cost', '1000', '--max-cost', '100'])
        self.assertFalse(self.cli.validate_args(args))
        
        # Invalid income range
        args = parser.parse_args(['--min-income', '50', '--max-income', '10'])
        self.assertFalse(self.cli.validate_args(args))
    
    def test_validate_args_no_selection(self):
        """Test validation when no selection method is specified."""
        parser = self.cli.create_parser()
        
        # No selection or info methods
        args = parser.parse_args(['--output-dir', 'test'])
        self.assertFalse(self.cli.validate_args(args))
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_info_commands(self, mock_stdout):
        """Test handling of information commands."""
        # Mock the data loader to use our test data
        with patch.object(self.cli, 'data_loader') as mock_loader:
            mock_loader.get_character_names.return_value = ['Tim Cheese', 'FluriFlura']
            mock_loader.get_available_tiers.return_value = ['Common', 'Rare']
            mock_loader.get_available_variants.return_value = ['Standard', 'Special']
            mock_loader.get_image_coverage_stats.return_value = {
                'total_characters': 4,
                'characters_with_images': 2,
                'characters_without_images': 2,
                'image_coverage_percentage': 50.0
            }
            
            parser = self.cli.create_parser()
            
            # Test list characters
            args = parser.parse_args(['--list-characters'])
            result = self.cli.handle_info_commands(args)
            self.assertTrue(result)
            output = mock_stdout.getvalue()
            self.assertIn('Tim Cheese', output)
            self.assertIn('FluriFlura', output)
            
            # Reset stdout
            mock_stdout.seek(0)
            mock_stdout.truncate(0)
            
            # Test list tiers
            args = parser.parse_args(['--list-tiers'])
            result = self.cli.handle_info_commands(args)
            self.assertTrue(result)
            output = mock_stdout.getvalue()
            self.assertIn('Common', output)
            self.assertIn('Rare', output)
            
            # Reset stdout
            mock_stdout.seek(0)
            mock_stdout.truncate(0)
            
            # Test stats
            args = parser.parse_args(['--stats'])
            result = self.cli.handle_info_commands(args)
            self.assertTrue(result)
            output = mock_stdout.getvalue()
            self.assertIn('Total characters: 4', output)
            self.assertIn('Image coverage: 50.0%', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_preview_selection(self, mock_stdout):
        """Test preview functionality."""
        # Mock the character selector
        with patch.object(self.cli, 'character_selector') as mock_selector:
            from card_generator.data_models import CharacterData
            
            # Create mock characters
            mock_chars = [
                CharacterData("Tim Cheese", "Common", 100, 5, "Standard"),
                CharacterData("FluriFlura", "Rare", 500, 10, "Standard")
            ]
            mock_chars[0].image_path = "tim_cheese.png"
            # mock_chars[1] has no image
            
            mock_selector.get_all_characters.return_value = mock_chars
            mock_selector.select_characters.return_value = mock_chars
            mock_selector.get_selection_summary.return_value = {
                'total_selected': 2,
                'with_images': 1,
                'without_images': 1,
                'tiers': {'Common': 1, 'Rare': 1}
            }
            
            parser = self.cli.create_parser()
            
            # Test preview all
            args = parser.parse_args(['--all', '--preview'])
            characters = self.cli.preview_selection(args)
            self.assertEqual(len(characters), 2)
            
            output = mock_stdout.getvalue()
            self.assertIn('Selected 2 characters', output)
            self.assertIn('Tim Cheese', output)
            self.assertIn('FluriFlura', output)
            self.assertIn('✓', output)  # Character with image
            self.assertIn('✗', output)  # Character without image
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_preview_selection_empty(self, mock_stdout):
        """Test preview with no matching characters."""
        with patch.object(self.cli, 'character_selector') as mock_selector:
            mock_selector.select_characters.return_value = []
            
            parser = self.cli.create_parser()
            args = parser.parse_args(['--names', 'Nonexistent', '--preview'])
            
            characters = self.cli.preview_selection(args)
            self.assertEqual(len(characters), 0)
            
            output = mock_stdout.getvalue()
            self.assertIn('No characters match', output)
    
    def test_run_with_help(self):
        """Test running CLI with help argument."""
        # Help should exit with code 0
        result = self.cli.run(['--help'])
        self.assertEqual(result, 0)
    
    def test_run_with_invalid_args(self):
        """Test running CLI with invalid arguments."""
        # Invalid argument should exit with non-zero code
        result = self.cli.run(['--invalid-argument'])
        self.assertNotEqual(result, 0)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_info_command(self, mock_stdout):
        """Test running CLI with info command."""
        with patch.object(self.cli, 'data_loader') as mock_loader:
            mock_loader.get_available_tiers.return_value = ['Common', 'Rare']
            
            result = self.cli.run(['--list-tiers'])
            self.assertEqual(result, 0)
            
            output = mock_stdout.getvalue()
            self.assertIn('Available tiers', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_preview_command(self, mock_stdout):
        """Test running CLI with preview command."""
        with patch.object(self.cli, 'character_selector') as mock_selector:
            from card_generator.data_models import CharacterData
            
            mock_chars = [CharacterData("Tim Cheese", "Common", 100, 5, "Standard")]
            mock_chars[0].image_path = "tim_cheese.png"
            
            mock_selector.get_all_characters.return_value = mock_chars
            mock_selector.get_selection_summary.return_value = {
                'total_selected': 1,
                'with_images': 1,
                'without_images': 0,
                'tiers': {'Common': 1}
            }
            
            result = self.cli.run(['--all', '--preview'])
            self.assertEqual(result, 0)
            
            output = mock_stdout.getvalue()
            self.assertIn('Selected 1 characters', output)
    
    def test_run_with_exception(self):
        """Test running CLI when an exception occurs."""
        with patch.object(self.cli, 'character_selector') as mock_selector:
            mock_selector.get_all_characters.side_effect = Exception("Test error")
            
            # Test with verbose flag
            result = self.cli.run(['--all', '--preview', '--verbose'])
            self.assertNotEqual(result, 0)
            
            # Test without verbose flag
            result = self.cli.run(['--all', '--preview'])
            self.assertNotEqual(result, 0)


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI with real data."""
    
    def test_cli_with_actual_data(self):
        """Test CLI with actual project data if available."""
        if os.path.exists('steal_a_brainrot_complete_database.csv'):
            cli = CardGeneratorCLI()
            
            # Test listing characters
            result = cli.run(['--list-characters'])
            self.assertEqual(result, 0)
            
            # Test stats
            result = cli.run(['--stats'])
            self.assertEqual(result, 0)
            
            # Test preview with common tier
            result = cli.run(['--tiers', 'Common', '--preview'])
            self.assertEqual(result, 0)
        else:
            self.skipTest("Actual CSV file not found")


if __name__ == '__main__':
    unittest.main()