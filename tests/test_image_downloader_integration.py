"""
Integration tests for the ImageDownloader class.

These tests verify the ImageDownloader works correctly with the existing
image processing pipeline and file system operations.
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, Mock
from io import BytesIO
from PIL import Image

from card_generator.image_downloader import ImageDownloader
from card_generator.config import DatabaseBuilderConfig
from card_generator.image_processor import ImageProcessor
from card_generator.data_models import CharacterData


class TestImageDownloaderIntegration(unittest.TestCase):
    """Integration tests for ImageDownloader with existing components."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Create temporary directory structure
        self.temp_dir = tempfile.mkdtemp()
        self.images_dir = os.path.join(self.temp_dir, 'images')
        self.output_dir = os.path.join(self.temp_dir, 'output')
        
        # Create test configuration
        self.config = DatabaseBuilderConfig(
            images_dir=self.images_dir,
            output_dir=self.output_dir,
            rate_limit_delay=0.5,  # Minimum allowed for testing
            max_retries=2,
            timeout=10,
            skip_existing_images=True,
            validate_images=True
        )
        
        # Create downloader and image processor
        self.downloader = ImageDownloader(self.config)
        self.image_processor = ImageProcessor()
        
        # Create test images of different sizes and formats
        self.test_images = self._create_test_images()
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_images(self):
        """Create test images for various scenarios."""
        images = {}
        
        # Standard character image (PNG)
        standard_image = Image.new('RGB', (400, 600), color='red')
        standard_data = BytesIO()
        standard_image.save(standard_data, format='PNG')
        images['standard_png'] = standard_data.getvalue()
        
        # JPEG character image
        jpeg_image = Image.new('RGB', (350, 500), color='blue')
        jpeg_data = BytesIO()
        jpeg_image.save(jpeg_data, format='JPEG', quality=90)
        images['standard_jpeg'] = jpeg_data.getvalue()
        
        # Large high-quality image
        large_image = Image.new('RGB', (800, 1200), color='green')
        large_data = BytesIO()
        large_image.save(large_data, format='PNG')
        images['large_png'] = large_data.getvalue()
        
        # Small image (below minimum size)
        small_image = Image.new('RGB', (100, 100), color='yellow')
        small_data = BytesIO()
        small_image.save(small_data, format='PNG')
        images['small_png'] = small_data.getvalue()
        
        # Wide aspect ratio image
        wide_image = Image.new('RGB', (1000, 200), color='purple')
        wide_data = BytesIO()
        wide_image.save(wide_data, format='PNG')
        images['wide_png'] = wide_data.getvalue()
        
        return images
    
    @patch('requests.Session.get')
    def test_download_and_process_workflow(self, mock_get):
        """Test complete workflow from download to image processing."""
        # Mock successful download
        mock_response = Mock()
        mock_response.content = self.test_images['standard_png']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Download image
        character_name = "Test Character"
        image_url = "https://example.com/character.png"
        
        downloaded_path = self.downloader.download_character_image(character_name, image_url)
        
        # Verify download
        self.assertIsNotNone(downloaded_path)
        self.assertTrue(os.path.exists(downloaded_path))
        
        # Test integration with image processor
        loaded_image = self.image_processor.load_image(downloaded_path)
        self.assertIsNotNone(loaded_image)
        
        # Test image processing operations
        processed_image = self.image_processor.resize_and_crop(loaded_image)
        self.assertIsNotNone(processed_image)
        
        # Verify processed image dimensions are reasonable
        width, height = processed_image.size
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)
    
    @patch('requests.Session.get')
    def test_download_multiple_formats(self, mock_get):
        """Test downloading images in different formats."""
        test_cases = [
            ("Character PNG", "https://example.com/char.png", self.test_images['standard_png']),
            ("Character JPEG", "https://example.com/char.jpg", self.test_images['standard_jpeg']),
            ("Character Large", "https://example.com/char_large.png", self.test_images['large_png'])
        ]
        
        downloaded_paths = []
        
        for character_name, image_url, image_data in test_cases:
            with self.subTest(character=character_name):
                # Mock response for this image
                mock_response = Mock()
                mock_response.content = image_data
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                # Download image
                path = self.downloader.download_character_image(character_name, image_url)
                
                # Verify download
                self.assertIsNotNone(path)
                self.assertTrue(os.path.exists(path))
                downloaded_paths.append(path)
                
                # Verify image can be processed
                image = self.image_processor.load_image(path)
                self.assertIsNotNone(image)
        
        # Verify all images were downloaded
        self.assertEqual(len(downloaded_paths), len(test_cases))
        
        # Test download statistics
        stats = self.downloader.get_download_stats()
        self.assertEqual(stats['total_images'], len(test_cases))
        self.assertEqual(stats['valid_images'], len(test_cases))
        self.assertEqual(stats['invalid_images'], 0)
    
    @patch('requests.Session.get')
    def test_skip_existing_images(self, mock_get):
        """Test skipping download when images already exist."""
        character_name = "Existing Character"
        
        # Create existing image file
        existing_filename = f"{character_name}.png"
        existing_path = os.path.join(self.images_dir, existing_filename)
        
        with open(existing_path, 'wb') as f:
            f.write(self.test_images['standard_png'])
        
        # Attempt to download (should skip)
        image_url = "https://example.com/existing.png"
        result_path = self.downloader.download_character_image(character_name, image_url)
        
        # Verify it returned existing path and didn't make network request
        self.assertEqual(result_path, existing_path)
        mock_get.assert_not_called()
    
    @patch('requests.Session.get')
    def test_validation_rejects_invalid_images(self, mock_get):
        """Test that validation rejects images that don't meet quality standards."""
        test_cases = [
            ("Too Small", self.test_images['small_png']),
            ("Too Wide", self.test_images['wide_png'])
        ]
        
        for character_name, image_data in test_cases:
            with self.subTest(character=character_name):
                # Mock response with invalid image
                mock_response = Mock()
                mock_response.content = image_data
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                # Attempt download
                result = self.downloader.download_character_image(character_name, "https://example.com/invalid.png")
                
                # Should reject invalid images
                self.assertIsNone(result)
    
    def test_cleanup_invalid_images_integration(self):
        """Test cleanup of invalid images with real file operations."""
        # Create mix of valid and invalid images
        valid_path = os.path.join(self.images_dir, "valid.png")
        invalid_path = os.path.join(self.images_dir, "invalid.png")
        corrupted_path = os.path.join(self.images_dir, "corrupted.jpg")
        
        # Write valid image
        with open(valid_path, 'wb') as f:
            f.write(self.test_images['standard_png'])
        
        # Write invalid image (too small)
        with open(invalid_path, 'wb') as f:
            f.write(self.test_images['small_png'])
        
        # Write corrupted image
        with open(corrupted_path, 'wb') as f:
            f.write(b"This is not an image file")
        
        # Run cleanup
        removed_files = self.downloader.cleanup_invalid_images()
        
        # Verify results
        self.assertTrue(os.path.exists(valid_path))  # Valid should remain
        self.assertFalse(os.path.exists(invalid_path))  # Invalid should be removed
        self.assertFalse(os.path.exists(corrupted_path))  # Corrupted should be removed
        
        self.assertIn(invalid_path, removed_files)
        self.assertIn(corrupted_path, removed_files)
        self.assertNotIn(valid_path, removed_files)
    
    def test_character_data_integration(self):
        """Test integration with CharacterData model."""
        # Create test character data
        character_data = CharacterData(
            name="Integration Character",
            tier="Epic",
            cost=500,
            income=25,
            variant="Standard"
        )
        
        # Create corresponding image file
        image_filename = f"{character_data.name}.png"
        image_path = os.path.join(self.images_dir, image_filename)
        
        with open(image_path, 'wb') as f:
            f.write(self.test_images['standard_png'])
        
        # Test finding image for character
        found_path = self.downloader.get_image_path(character_data.name)
        self.assertEqual(found_path, image_path)
        
        # Test image validation
        self.assertTrue(self.downloader.validate_image_file(found_path))
        
        # Test image processing integration
        image = self.image_processor.load_image(found_path)
        self.assertIsNotNone(image)
        
        # Test creating placeholder if image missing
        missing_character = CharacterData(
            name="Missing Character",
            tier="Rare",
            cost=200,
            income=10,
            variant="Standard"
        )
        
        missing_path = self.downloader.get_image_path(missing_character.name)
        self.assertIsNone(missing_path)
        
        # Should be able to create placeholder
        placeholder = self.image_processor.create_placeholder(
            missing_character.name, 
            missing_character.tier
        )
        self.assertIsNotNone(placeholder)
    
    @patch('requests.Session.get')
    def test_error_recovery_and_logging(self, mock_get):
        """Test error recovery and logging integration."""
        # Test network error recovery - both attempts fail to ensure error is logged
        mock_get.side_effect = [
            Exception("Network error"),  # First attempt fails
            Exception("Network error")   # Second attempt also fails
        ]
        
        character_name = "Recovery Test"
        image_url = "https://example.com/recovery.png"
        
        result = self.downloader.download_character_image(character_name, image_url)
        
        # Should fail after retries
        self.assertIsNone(result)
        
        # Check error was logged
        self.assertGreater(len(self.downloader.error_handler.error_history), 0)
    
    def test_directory_creation_and_permissions(self):
        """Test directory creation and permission handling."""
        # Test with non-existent directory
        new_images_dir = os.path.join(self.temp_dir, 'new_images')
        new_config = DatabaseBuilderConfig(images_dir=new_images_dir)
        
        # Creating downloader should create directory
        new_downloader = ImageDownloader(new_config)
        self.assertTrue(os.path.exists(new_images_dir))
        
        # Test stats on empty directory
        stats = new_downloader.get_download_stats()
        self.assertEqual(stats['total_images'], 0)
        self.assertEqual(stats['valid_images'], 0)
        self.assertEqual(stats['invalid_images'], 0)
    
    def test_filename_safety_and_conflicts(self):
        """Test filename safety and conflict resolution."""
        # Test characters with problematic names
        problematic_names = [
            "Character/With\\Slashes",
            "Character<With>Brackets",
            "Character:With:Colons",
            "Character\"With\"Quotes",
            "Character|With|Pipes",
            "Character?With?Questions",
            "Character*With*Asterisks"
        ]
        
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.content = self.test_images['standard_png']
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            downloaded_paths = []
            
            for character_name in problematic_names:
                with self.subTest(character=character_name):
                    result = self.downloader.download_character_image(
                        character_name, 
                        "https://example.com/test.png"
                    )
                    
                    self.assertIsNotNone(result)
                    self.assertTrue(os.path.exists(result))
                    downloaded_paths.append(result)
                    
                    # Verify filename is safe
                    filename = os.path.basename(result)
                    self.assertNotRegex(filename, r'[<>:"/\\|?*]')
            
            # Verify all files were created with unique names
            self.assertEqual(len(set(downloaded_paths)), len(problematic_names))
    
    def test_large_batch_processing(self):
        """Test processing a larger batch of images."""
        # Create batch of test characters
        characters = [f"Character {i:03d}" for i in range(20)]
        
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.content = self.test_images['standard_png']
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            downloaded_count = 0
            failed_count = 0
            
            for character_name in characters:
                result = self.downloader.download_character_image(
                    character_name,
                    f"https://example.com/{character_name.replace(' ', '_')}.png"
                )
                
                if result:
                    downloaded_count += 1
                    self.assertTrue(os.path.exists(result))
                else:
                    failed_count += 1
            
            # Verify batch processing results
            self.assertEqual(downloaded_count, len(characters))
            self.assertEqual(failed_count, 0)
            
            # Verify statistics
            stats = self.downloader.get_download_stats()
            self.assertEqual(stats['total_images'], len(characters))
            self.assertEqual(stats['valid_images'], len(characters))
            
            # Test cleanup doesn't remove valid images
            removed = self.downloader.cleanup_invalid_images()
            self.assertEqual(len(removed), 0)


class TestImageDownloaderConfigIntegration(unittest.TestCase):
    """Test ImageDownloader integration with different configurations."""
    
    def setUp(self):
        """Set up configuration integration tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.images_dir = os.path.join(self.temp_dir, 'images')
    
    def tearDown(self):
        """Clean up configuration integration tests."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_custom_configuration(self):
        """Test ImageDownloader with custom configuration."""
        custom_config = DatabaseBuilderConfig(
            images_dir=self.images_dir,
            rate_limit_delay=0.5,
            max_retries=5,
            timeout=60,
            skip_existing_images=False,
            validate_images=False
        )
        
        downloader = ImageDownloader(custom_config)
        
        # Verify configuration is applied
        self.assertEqual(downloader.config.rate_limit_delay, 0.5)
        self.assertEqual(downloader.config.max_retries, 5)
        self.assertEqual(downloader.config.timeout, 60)
        self.assertFalse(downloader.config.skip_existing_images)
        self.assertFalse(downloader.config.validate_images)
    
    def test_configuration_validation(self):
        """Test configuration validation in ImageDownloader."""
        # Test invalid configurations
        with self.assertRaises(ValueError):
            invalid_config = DatabaseBuilderConfig(
                images_dir=self.images_dir,
                rate_limit_delay=0.1,  # Too low
                max_retries=0,  # Too low
                timeout=1  # Too low
            )
    
    def test_default_configuration(self):
        """Test ImageDownloader with default configuration."""
        downloader = ImageDownloader()
        
        # Verify default values
        self.assertEqual(downloader.config.images_dir, "images")
        self.assertEqual(downloader.config.rate_limit_delay, 2.0)
        self.assertEqual(downloader.config.max_retries, 3)
        self.assertEqual(downloader.config.timeout, 30)
        self.assertTrue(downloader.config.skip_existing_images)
        self.assertTrue(downloader.config.validate_images)


if __name__ == '__main__':
    unittest.main()