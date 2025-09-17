"""
Unit tests for comprehensive error handling across all modules.

Tests error scenarios, recovery mechanisms, and logging functionality.
"""

import unittest
import tempfile
import shutil
import os
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from card_generator.data_loader import CSVDataLoader
from card_generator.image_processor import ImageProcessor
from card_generator.output_manager import OutputManager
from card_generator.data_models import CharacterData
from card_generator.config import CardConfig, OutputConfig


class TestDataLoaderErrorHandling(unittest.TestCase):
    """Test error handling in CSVDataLoader."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.test_dir, 'test.csv')
        self.images_dir = os.path.join(self.test_dir, 'images')
        os.makedirs(self.images_dir)
        
        # Set up logging capture
        self.log_capture = []
        self.handler = logging.Handler()
        self.handler.emit = lambda record: self.log_capture.append(record)
        
        logger = logging.getLogger('card_generator.data_loader')
        logger.addHandler(self.handler)
        logger.setLevel(logging.DEBUG)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Clean up logging
        logger = logging.getLogger('card_generator.data_loader')
        logger.removeHandler(self.handler)
    
    def test_csv_file_not_found_error(self):
        """Test handling of missing CSV file."""
        loader = CSVDataLoader('nonexistent.csv', self.images_dir)
        
        with self.assertRaises(FileNotFoundError):
            loader.load_characters()
        
        # Check that error was logged
        error_logs = [log for log in self.log_capture if log.levelno >= logging.ERROR]
        self.assertGreater(len(error_logs), 0)
    
    def test_csv_permission_denied(self):
        """Test handling of CSV file permission errors."""
        # Create CSV file
        with open(self.csv_path, 'w') as f:
            f.write('Character Name,Tier,Cost,Income per Second,Variant Type\n')
            f.write('"Test","Common",100,5,"Standard"\n')
        
        # Mock permission error
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            loader = CSVDataLoader(self.csv_path, self.images_dir)
            
            with self.assertRaises(ValueError) as context:
                loader.load_characters()
            
            self.assertIn("Permission denied", str(context.exception))
    
    def test_corrupted_csv_data_handling(self):
        """Test handling of corrupted CSV data."""
        # Create CSV with various types of corruption
        corrupted_csv = '''Character Name,Tier,Cost,Income per Second,Variant Type
"Valid Character","Common",100,5,"Standard"
"Invalid Cost","Common","not_a_number",5,"Standard"
"Missing Tier","",100,5,"Standard"
"Invalid Income","Common",100,"not_a_number","Standard"
"Negative Cost","Common",-100,5,"Standard"
"Missing Name","","Common",100,5,"Standard"
'''
        
        with open(self.csv_path, 'w', encoding='utf-8') as f:
            f.write(corrupted_csv)
        
        loader = CSVDataLoader(self.csv_path, self.images_dir)
        characters = loader.load_characters()
        
        # Should only load the valid character
        self.assertEqual(len(characters), 1)
        self.assertEqual(characters[0].name, "Valid Character")
        
        # Check failed characters tracking
        failed = loader.get_failed_characters()
        self.assertGreater(len(failed), 0)
        
        # Check loading summary
        summary = loader.get_loading_summary()
        self.assertEqual(summary['successful_characters'], 1)
        self.assertGreater(summary['failed_characters'], 0)
        self.assertLess(summary['success_rate'], 100)
    
    def test_csv_encoding_errors(self):
        """Test handling of CSV encoding issues."""
        # Create CSV with problematic encoding
        with open(self.csv_path, 'wb') as f:
            # Write some bytes that aren't valid UTF-8
            f.write(b'Character Name,Tier,Cost,Income per Second,Variant Type\n')
            f.write(b'"Test \xff Character","Common",100,5,"Standard"\n')
        
        loader = CSVDataLoader(self.csv_path, self.images_dir)
        
        # Should handle encoding error gracefully
        try:
            characters = loader.load_characters()
            # If it succeeds, it should have used fallback encoding
            self.assertIsInstance(characters, list)
        except ValueError as e:
            # If it fails, should be a clear error message
            self.assertIn("encoding", str(e).lower())
    
    def test_empty_csv_file(self):
        """Test handling of empty CSV file."""
        # Create empty CSV
        with open(self.csv_path, 'w') as f:
            f.write('')
        
        loader = CSVDataLoader(self.csv_path, self.images_dir)
        
        with self.assertRaises(ValueError) as context:
            loader.load_characters()
        
        # Should fail with some error message about the CSV
        self.assertTrue(len(str(context.exception)) > 0)
    
    def test_csv_structure_validation(self):
        """Test CSV structure validation."""
        # Test missing required columns
        with open(self.csv_path, 'w') as f:
            f.write('Name,Type\n')  # Missing required columns
            f.write('"Test","Common"\n')
        
        loader = CSVDataLoader(self.csv_path, self.images_dir)
        validation = loader.validate_csv_structure()
        
        self.assertFalse(validation['is_valid'])
        self.assertGreater(len(validation['errors']), 0)
        self.assertGreater(len(validation['missing_columns']), 0)
    
    def test_images_directory_permission_error(self):
        """Test handling of images directory permission issues."""
        # Create CSV with valid data
        with open(self.csv_path, 'w') as f:
            f.write('Character Name,Tier,Cost,Income per Second,Variant Type\n')
            f.write('"Test Character","Common",100,5,"Standard"\n')
        
        # Mock permission error for images directory
        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', side_effect=PermissionError("Permission denied")):
            
            loader = CSVDataLoader(self.csv_path, self.images_dir)
            characters = loader.load_characters()
            
            # Should still load characters but without images
            self.assertEqual(len(characters), 1)
            self.assertIsNone(characters[0].image_path)


class TestImageProcessorErrorHandling(unittest.TestCase):
    """Test error handling in ImageProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = ImageProcessor()
        self.test_dir = tempfile.mkdtemp()
        
        # Set up logging capture
        self.log_capture = []
        self.handler = logging.Handler()
        self.handler.emit = lambda record: self.log_capture.append(record)
        
        logger = logging.getLogger('card_generator.image_processor')
        logger.addHandler(self.handler)
        logger.setLevel(logging.DEBUG)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Clean up logging
        logger = logging.getLogger('card_generator.image_processor')
        logger.removeHandler(self.handler)
    
    def test_image_file_not_found(self):
        """Test handling of missing image files."""
        with self.assertRaises(FileNotFoundError):
            self.processor.load_image('nonexistent.png')
        
        # Check error logging
        error_logs = [log for log in self.log_capture if log.levelno >= logging.ERROR]
        self.assertGreater(len(error_logs), 0)
    
    def test_image_permission_denied(self):
        """Test handling of image permission errors."""
        # Create test image
        image_path = os.path.join(self.test_dir, 'test.png')
        test_image = Image.new('RGB', (300, 300), 'red')
        test_image.save(image_path)
        
        # Mock permission error
        with patch('PIL.Image.open', side_effect=PermissionError("Permission denied")):
            result = self.processor.load_image(image_path)
            self.assertIsNone(result)
        
        # Check error logging
        error_logs = [log for log in self.log_capture if log.levelno >= logging.ERROR]
        self.assertGreater(len(error_logs), 0)
    
    def test_corrupted_image_file(self):
        """Test handling of corrupted image files."""
        # Create fake corrupted image file
        corrupted_path = os.path.join(self.test_dir, 'corrupted.png')
        with open(corrupted_path, 'wb') as f:
            f.write(b'This is not a valid image file')
        
        result = self.processor.load_image(corrupted_path)
        self.assertIsNone(result)
        
        # Check error logging
        error_logs = [log for log in self.log_capture if log.levelno >= logging.ERROR]
        self.assertGreater(len(error_logs), 0)
    
    def test_unsupported_image_format(self):
        """Test handling of unsupported image formats."""
        unsupported_path = os.path.join(self.test_dir, 'test.xyz')
        with open(unsupported_path, 'w') as f:
            f.write('fake content')
        
        with self.assertRaises(ValueError) as context:
            self.processor.load_image(unsupported_path)
        
        self.assertIn("Unsupported image format", str(context.exception))
    
    def test_extremely_large_image_file(self):
        """Test handling of extremely large image files."""
        large_image_path = os.path.join(self.test_dir, 'large.png')
        
        # Mock large file size
        with patch('os.path.getsize', return_value=100 * 1024 * 1024):  # 100MB
            # Create a small actual file
            test_image = Image.new('RGB', (100, 100), 'red')
            test_image.save(large_image_path)
            
            result = self.processor.load_image(large_image_path)
            self.assertIsNone(result)
        
        # Check warning logging
        warning_logs = [log for log in self.log_capture if log.levelno >= logging.WARNING]
        self.assertGreater(len(warning_logs), 0)
    
    def test_image_conversion_error(self):
        """Test handling of image conversion errors."""
        # Create test image
        image_path = os.path.join(self.test_dir, 'test.png')
        test_image = Image.new('RGBA', (300, 300), (255, 0, 0, 128))
        test_image.save(image_path)
        
        # Mock conversion error
        with patch.object(Image.Image, 'convert', side_effect=Exception("Conversion failed")):
            result = self.processor.load_image(image_path)
            self.assertIsNone(result)
        
        # Check error logging
        error_logs = [log for log in self.log_capture if log.levelno >= logging.ERROR]
        self.assertGreater(len(error_logs), 0)
    
    def test_placeholder_creation_with_font_errors(self):
        """Test placeholder creation when font loading fails."""
        # Mock font loading to fail
        with patch('PIL.ImageFont.truetype', side_effect=OSError("Font not found")), \
             patch('PIL.ImageFont.load_default', side_effect=OSError("No default font")):
            
            # Should handle font errors gracefully
            try:
                placeholder = self.processor.create_placeholder('Test Character', 'Epic')
                # If it succeeds, it should still be a valid image
                self.assertIsNotNone(placeholder)
                self.assertEqual(placeholder.mode, 'RGB')
            except Exception:
                # If it fails completely, that's also acceptable for this edge case
                pass
    
    def test_image_quality_validation_edge_cases(self):
        """Test image quality validation with edge cases."""
        # Test extremely small image
        tiny_image = Image.new('RGB', (50, 50), 'red')
        self.assertFalse(self.processor._validate_image_quality(tiny_image))
        
        # Test extremely wide image
        wide_image = Image.new('RGB', (5000, 100), 'red')
        self.assertFalse(self.processor._validate_image_quality(wide_image))
        
        # Test extremely tall image
        tall_image = Image.new('RGB', (100, 5000), 'red')
        self.assertFalse(self.processor._validate_image_quality(tall_image))


class TestOutputManagerErrorHandling(unittest.TestCase):
    """Test error handling in OutputManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config = OutputConfig(
            individual_cards_dir=os.path.join(self.test_dir, 'cards'),
            print_sheets_dir=os.path.join(self.test_dir, 'sheets'),
            formats=('PNG',)
        )
        self.output_manager = OutputManager(self.config)
        
        self.test_character = CharacterData(
            name="Test Character",
            tier="Common",
            cost=100,
            income=50,
            variant="Standard"
        )
        self.test_image = Image.new('RGB', (100, 100), 'red')
        
        # Set up logging capture
        self.log_capture = []
        self.handler = logging.Handler()
        self.handler.emit = lambda record: self.log_capture.append(record)
        
        logger = logging.getLogger('card_generator.output_manager')
        logger.addHandler(self.handler)
        logger.setLevel(logging.DEBUG)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Clean up logging
        logger = logging.getLogger('card_generator.output_manager')
        logger.removeHandler(self.handler)
    
    def test_directory_creation_permission_error(self):
        """Test handling of directory creation permission errors."""
        # Mock permission error during directory creation
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(IOError) as context:
                OutputManager(self.config)
            
            self.assertIn("Permission denied", str(context.exception))
    
    def test_disk_space_check_insufficient_space(self):
        """Test handling of insufficient disk space."""
        # Mock insufficient disk space
        with patch('shutil.disk_usage', return_value=(1000, 900, 50)):  # 50 bytes free
            with self.assertRaises(IOError) as context:
                self.output_manager.save_individual_card(
                    self.test_image, self.test_character, 'PNG'
                )
            
            self.assertIn("Insufficient disk space", str(context.exception))
    
    def test_file_save_permission_error(self):
        """Test handling of file save permission errors."""
        # Mock permission error during save
        with patch.object(Image.Image, 'save', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(IOError) as context:
                self.output_manager.save_individual_card(
                    self.test_image, self.test_character, 'PNG'
                )
            
            self.assertIn("Permission denied", str(context.exception))
    
    def test_file_save_disk_full_error(self):
        """Test handling of disk full errors during save."""
        # Mock disk full error
        disk_full_error = OSError("No space left on device")
        disk_full_error.errno = 28
        
        with patch.object(Image.Image, 'save', side_effect=disk_full_error):
            with self.assertRaises(IOError) as context:
                self.output_manager.save_individual_card(
                    self.test_image, self.test_character, 'PNG'
                )
            
            self.assertIn("Disk full", str(context.exception))
    
    def test_file_save_creates_empty_file(self):
        """Test handling when save creates empty file."""
        # Mock save to create empty file
        def mock_save(filepath, format, **kwargs):
            Path(filepath).touch()  # Create empty file
        
        with patch.object(Image.Image, 'save', side_effect=mock_save):
            with self.assertRaises(IOError) as context:
                self.output_manager.save_individual_card(
                    self.test_image, self.test_character, 'PNG'
                )
            
            self.assertIn("Created file is empty", str(context.exception))
    
    def test_batch_processing_partial_failures(self):
        """Test batch processing with partial failures."""
        characters = [
            CharacterData("Good Character", "Common", 100, 50, "Standard"),
            CharacterData("Bad Character", "Rare", 200, 100, "Standard"),
            CharacterData("Another Good", "Epic", 300, 150, "Standard")
        ]
        
        cards_data = [(self.test_image, char) for char in characters]
        
        # Mock save to fail for "Bad Character"
        original_save = self.output_manager.save_individual_card
        def mock_save(image, character, format):
            if "Bad" in character.name:
                raise IOError("Simulated failure")
            return original_save(image, character, format)
        
        with patch.object(self.output_manager, 'save_individual_card', side_effect=mock_save):
            results = self.output_manager.batch_process_cards(cards_data)
        
        # Check results
        self.assertEqual(results['total_cards'], 3)
        self.assertEqual(results['successful_cards'], 2)
        self.assertEqual(results['failed_cards'], 1)
        self.assertEqual(len(results['errors']), 1)
        self.assertIn("Bad Character", results['errors'][0])
    
    def test_directory_write_permission_check(self):
        """Test directory write permission checking."""
        # Skip this test on Windows as chmod doesn't work the same way
        import platform
        if platform.system() == 'Windows':
            self.skipTest("Directory permission test not reliable on Windows")
        
        # Create read-only directory
        readonly_dir = Path(self.test_dir) / 'readonly'
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        try:
            with self.assertRaises(IOError) as context:
                self.output_manager._ensure_directory_writable(readonly_dir)
            
            self.assertIn("not writable", str(context.exception))
        finally:
            # Clean up - restore write permissions
            readonly_dir.chmod(0o755)
    
    def test_error_recovery_suggestions(self):
        """Test error recovery suggestion system."""
        # Test permission error suggestions
        perm_error = PermissionError("Permission denied")
        suggestions = self.output_manager.get_error_recovery_suggestions(perm_error)
        self.assertIn("Check file and directory permissions", suggestions)
        
        # Test disk full error suggestions
        disk_error = OSError("Disk full - no space left on device")
        suggestions = self.output_manager.get_error_recovery_suggestions(disk_error)
        self.assertTrue(any("Free up disk space" in suggestion for suggestion in suggestions))
        
        # Test file not found error suggestions
        file_error = FileNotFoundError("File not found")
        suggestions = self.output_manager.get_error_recovery_suggestions(file_error)
        self.assertIn("Verify the input file paths", suggestions)
        
        # Test generic error suggestions
        generic_error = Exception("Unknown error")
        suggestions = self.output_manager.get_error_recovery_suggestions(generic_error)
        self.assertIn("Check the error logs", suggestions)


class TestIntegratedErrorHandling(unittest.TestCase):
    """Test error handling across multiple components."""
    
    def setUp(self):
        """Set up integrated test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.test_dir, 'test.csv')
        self.images_dir = os.path.join(self.test_dir, 'images')
        self.output_dir = os.path.join(self.test_dir, 'output')
        
        os.makedirs(self.images_dir)
        os.makedirs(self.output_dir)
        
        # Create test CSV with mixed valid/invalid data
        csv_content = '''Character Name,Tier,Cost,Income per Second,Variant Type
"Valid Character 1","Common",100,5,"Standard"
"Invalid Cost Char","Common","not_a_number",5,"Standard"
"Valid Character 2","Rare",200,10,"Standard"
"Missing Tier Char","",150,7,"Standard"
"Valid Character 3","Epic",300,15,"Standard"
'''
        with open(self.csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Create some test images (only for some characters)
        valid_image = Image.new('RGB', (300, 300), 'blue')
        valid_image.save(os.path.join(self.images_dir, 'Valid Character 1_1.png'))
        valid_image.save(os.path.join(self.images_dir, 'Valid Character 3_1.png'))
        
        # Create corrupted image file
        with open(os.path.join(self.images_dir, 'Valid Character 2_1.png'), 'wb') as f:
            f.write(b'corrupted image data')
    
    def tearDown(self):
        """Clean up integrated test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_end_to_end_error_resilience(self):
        """Test that the system handles errors gracefully end-to-end."""
        # Initialize components
        loader = CSVDataLoader(self.csv_path, self.images_dir)
        processor = ImageProcessor()
        output_config = OutputConfig(
            individual_cards_dir=os.path.join(self.output_dir, 'cards'),
            print_sheets_dir=os.path.join(self.output_dir, 'sheets'),
            formats=('PNG',)
        )
        output_manager = OutputManager(output_config)
        
        # Load characters (should handle invalid data gracefully)
        characters = loader.load_characters()
        
        # Should have loaded only valid characters
        self.assertEqual(len(characters), 3)  # 3 valid out of 5 total
        
        # Check that failures were tracked
        failed = loader.get_failed_characters()
        self.assertEqual(len(failed), 2)  # 2 invalid characters
        
        # Process images for each character
        processed_cards = []
        for character in characters:
            if character.has_image():
                try:
                    image = processor.load_image(character.image_path)
                    if image is None:
                        # Use placeholder for corrupted images
                        image = processor.create_placeholder(character.name, character.tier)
                    processed_cards.append((image, character))
                except Exception:
                    # Use placeholder for any image loading errors
                    image = processor.create_placeholder(character.name, character.tier)
                    processed_cards.append((image, character))
            else:
                # Create placeholder for missing images
                image = processor.create_placeholder(character.name, character.tier)
                processed_cards.append((image, character))
        
        # Should have processed all valid characters
        self.assertEqual(len(processed_cards), 3)
        
        # Save cards (should handle any save errors gracefully)
        results = output_manager.batch_process_cards(processed_cards)
        
        # Check that processing completed
        self.assertGreater(results['successful_cards'], 0)
        
        # Get summary of the entire process
        loading_summary = loader.get_loading_summary()
        self.assertLess(loading_summary['success_rate'], 100)  # Some failures expected
        self.assertGreater(loading_summary['successful_characters'], 0)


if __name__ == '__main__':
    # Set up logging for tests
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    unittest.main()