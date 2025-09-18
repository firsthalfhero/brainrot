"""
Unit tests for the ImageDownloader class.
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from PIL import Image
import requests

from card_generator.image_downloader import ImageDownloader
from card_generator.config import DatabaseBuilderConfig
from card_generator.error_handling import ErrorCategory, ErrorSeverity


class TestImageDownloader(unittest.TestCase):
    """Test cases for ImageDownloader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.images_dir = os.path.join(self.temp_dir, 'images')
        
        # Create test config
        self.config = DatabaseBuilderConfig(
            images_dir=self.images_dir,
            rate_limit_delay=0.5,  # Minimum allowed for testing
            max_retries=2,
            timeout=5
        )
        
        # Create downloader instance
        self.downloader = ImageDownloader(self.config)
        
        # Create a test image
        self.test_image = Image.new('RGB', (300, 400), color='red')
        self.test_image_data = BytesIO()
        self.test_image.save(self.test_image_data, format='PNG')
        self.test_image_bytes = self.test_image_data.getvalue()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_images_directory(self):
        """Test that initialization creates the images directory."""
        self.assertTrue(os.path.exists(self.images_dir))
    
    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        downloader = ImageDownloader()
        self.assertIsInstance(downloader.config, DatabaseBuilderConfig)
        self.assertEqual(downloader.config.images_dir, "images")
    
    def test_clean_filename(self):
        """Test filename cleaning functionality."""
        test_cases = [
            ("Normal Name", "Normal Name"),
            ("Name/With\\Slashes", "Name_With_Slashes"),
            ("Name<With>Invalid:Chars", "Name_With_Invalid_Chars"),
            ("Name\"With|Quotes?", "Name_With_Quotes_"),
            ("Name*With*Asterisks", "Name_With_Asterisks")
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.downloader._clean_filename(input_name)
                self.assertEqual(result, expected)
    
    def test_get_original_image_url(self):
        """Test URL cleaning and normalization."""
        test_cases = [
            # Scale removal
            ("https://example.com/image.png/scale-to-width-down/300", 
             "https://example.com/image.png"),
            ("https://example.com/image.png/scale-to-height-down/400", 
             "https://example.com/image.png"),
            
            # Revision URL cleaning
            ("https://example.com/image.png/revision/latest/scale?cb=123", 
             "https://example.com/image.png/revision/latest?cb=123"),
            ("https://example.com/image.png/revision/latest/", 
             "https://example.com/image.png/revision/latest"),
            
            # Protocol addition
            ("//example.com/image.png", "https://example.com/image.png"),
            
            # Invalid URLs
            ("not-a-url", None),
            ("", None),
            (None, None),
            ("https://example.com/notanimage.txt", None)
        ]
        
        for input_url, expected in test_cases:
            with self.subTest(input_url=input_url):
                result = self.downloader._get_original_image_url(input_url)
                self.assertEqual(result, expected)
    
    def test_determine_file_extension(self):
        """Test file extension determination."""
        test_cases = [
            ("https://example.com/image.png", ".png"),
            ("https://example.com/image.jpg", ".jpg"),
            ("https://example.com/image.jpeg", ".jpg"),
            ("https://example.com/image.gif", ".gif"),
            ("https://example.com/image.webp", ".webp"),
            ("https://example.com/image.PNG", ".png"),  # Case insensitive
            ("https://example.com/image", None),
            ("https://example.com/image.txt", None)
        ]
        
        for input_url, expected in test_cases:
            with self.subTest(input_url=input_url):
                result = self.downloader._determine_file_extension(input_url)
                self.assertEqual(result, expected)
    
    def test_validate_image_data_valid(self):
        """Test validation of valid image data."""
        result = self.downloader._validate_image_data(self.test_image_bytes, "Test Character")
        self.assertTrue(result)
    
    def test_validate_image_data_invalid(self):
        """Test validation of invalid image data."""
        # Test with non-image data
        invalid_data = b"This is not an image"
        result = self.downloader._validate_image_data(invalid_data, "Test Character")
        self.assertFalse(result)
        
        # Test with too small image
        small_image = Image.new('RGB', (50, 50), color='blue')
        small_image_data = BytesIO()
        small_image.save(small_image_data, format='PNG')
        result = self.downloader._validate_image_data(small_image_data.getvalue(), "Test Character")
        self.assertFalse(result)
        
        # Test with extreme aspect ratio
        wide_image = Image.new('RGB', (1000, 100), color='green')
        wide_image_data = BytesIO()
        wide_image.save(wide_image_data, format='PNG')
        result = self.downloader._validate_image_data(wide_image_data.getvalue(), "Test Character")
        self.assertFalse(result)
    
    def test_generate_image_path(self):
        """Test image path generation."""
        character_name = "Test Character"
        image_url = "https://example.com/image.png"
        
        result = self.downloader._generate_image_path(character_name, image_url)
        expected_path = os.path.join(self.images_dir, "Test Character.png")
        self.assertEqual(result, expected_path)
    
    def test_find_existing_image_found(self):
        """Test finding existing image file."""
        # Create a test image file
        character_name = "Test Character"
        filename = "Test Character.png"
        file_path = os.path.join(self.images_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(self.test_image_bytes)
        
        result = self.downloader._find_existing_image(character_name)
        self.assertEqual(result, file_path)
    
    def test_find_existing_image_not_found(self):
        """Test finding non-existent image file."""
        result = self.downloader._find_existing_image("Nonexistent Character")
        self.assertIsNone(result)
    
    @patch('card_generator.image_downloader.time.sleep')
    @patch('requests.Session.get')
    def test_download_with_retries_success(self, mock_get, mock_sleep):
        """Test successful download with retries."""
        # Mock successful response
        mock_response = Mock()
        mock_response.content = self.test_image_bytes
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        url = "https://example.com/image.png"
        result = self.downloader._download_with_retries(url)
        
        self.assertEqual(result, self.test_image_bytes)
        mock_get.assert_called_once_with(url, timeout=self.config.timeout)
    
    @patch('card_generator.image_downloader.time.sleep')
    @patch('requests.Session.get')
    def test_download_with_retries_failure(self, mock_get, mock_sleep):
        """Test download failure with retries."""
        # Mock failed responses
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        url = "https://example.com/image.png"
        result = self.downloader._download_with_retries(url)
        
        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, self.config.max_retries)
    
    @patch('card_generator.image_downloader.time.sleep')
    @patch('requests.Session.get')
    def test_download_with_retries_rate_limited(self, mock_get, mock_sleep):
        """Test download with rate limiting."""
        # Mock rate limited response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        url = "https://example.com/image.png"
        result = self.downloader._download_with_retries(url)
        
        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, self.config.max_retries)
    
    @patch('card_generator.image_downloader.time.sleep')
    @patch('requests.Session.get')
    def test_download_character_image_success(self, mock_get, mock_sleep):
        """Test successful character image download."""
        # Mock successful response
        mock_response = Mock()
        mock_response.content = self.test_image_bytes
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        character_name = "Test Character"
        image_url = "https://example.com/image.png"
        
        result = self.downloader.download_character_image(character_name, image_url)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        
        # Verify file content
        with open(result, 'rb') as f:
            saved_data = f.read()
        self.assertEqual(saved_data, self.test_image_bytes)
    
    def test_download_character_image_skip_existing(self):
        """Test skipping download when image already exists."""
        # Create existing image
        character_name = "Test Character"
        filename = "Test Character.png"
        existing_path = os.path.join(self.images_dir, filename)
        
        with open(existing_path, 'wb') as f:
            f.write(self.test_image_bytes)
        
        # Configure to skip existing
        self.config.skip_existing_images = True
        
        image_url = "https://example.com/image.png"
        result = self.downloader.download_character_image(character_name, image_url)
        
        self.assertEqual(result, existing_path)
    
    @patch('requests.Session.get')
    def test_download_character_image_invalid_url(self, mock_get):
        """Test download with invalid URL."""
        character_name = "Test Character"
        invalid_url = "not-a-valid-url"
        
        result = self.downloader.download_character_image(character_name, invalid_url)
        self.assertIsNone(result)
        mock_get.assert_not_called()
    
    def test_validate_image_file_valid(self):
        """Test validation of valid image file."""
        # Create test image file
        file_path = os.path.join(self.images_dir, "test.png")
        with open(file_path, 'wb') as f:
            f.write(self.test_image_bytes)
        
        result = self.downloader.validate_image_file(file_path)
        self.assertTrue(result)
    
    def test_validate_image_file_nonexistent(self):
        """Test validation of non-existent file."""
        file_path = os.path.join(self.images_dir, "nonexistent.png")
        result = self.downloader.validate_image_file(file_path)
        self.assertFalse(result)
    
    def test_validate_image_file_corrupted(self):
        """Test validation of corrupted image file."""
        # Create corrupted image file
        file_path = os.path.join(self.images_dir, "corrupted.png")
        with open(file_path, 'wb') as f:
            f.write(b"This is not a valid image")
        
        result = self.downloader.validate_image_file(file_path)
        self.assertFalse(result)
    
    def test_get_image_path_existing(self):
        """Test getting path for existing image."""
        # Create test image file
        character_name = "Test Character"
        filename = "Test Character.png"
        file_path = os.path.join(self.images_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(self.test_image_bytes)
        
        result = self.downloader.get_image_path(character_name)
        self.assertEqual(result, file_path)
    
    def test_get_image_path_nonexistent(self):
        """Test getting path for non-existent image."""
        result = self.downloader.get_image_path("Nonexistent Character")
        self.assertIsNone(result)
    
    def test_cleanup_invalid_images(self):
        """Test cleanup of invalid image files."""
        # Create valid image
        valid_path = os.path.join(self.images_dir, "valid.png")
        with open(valid_path, 'wb') as f:
            f.write(self.test_image_bytes)
        
        # Create invalid image
        invalid_path = os.path.join(self.images_dir, "invalid.png")
        with open(invalid_path, 'wb') as f:
            f.write(b"Not an image")
        
        # Create non-image file (should be ignored)
        text_path = os.path.join(self.images_dir, "text.txt")
        with open(text_path, 'w') as f:
            f.write("This is text")
        
        removed_files = self.downloader.cleanup_invalid_images()
        
        # Check results
        self.assertIn(invalid_path, removed_files)
        self.assertTrue(os.path.exists(valid_path))  # Valid image should remain
        self.assertTrue(os.path.exists(text_path))   # Non-image should remain
        self.assertFalse(os.path.exists(invalid_path))  # Invalid image should be removed
    
    def test_get_download_stats(self):
        """Test getting download statistics."""
        # Create test images
        png_path = os.path.join(self.images_dir, "test1.png")
        jpg_path = os.path.join(self.images_dir, "test2.jpg")
        
        with open(png_path, 'wb') as f:
            f.write(self.test_image_bytes)
        
        # Create a JPEG image
        jpeg_image = Image.new('RGB', (200, 300), color='blue')
        jpeg_data = BytesIO()
        jpeg_image.save(jpeg_data, format='JPEG')
        
        with open(jpg_path, 'wb') as f:
            f.write(jpeg_data.getvalue())
        
        # Create invalid image
        invalid_path = os.path.join(self.images_dir, "invalid.png")
        with open(invalid_path, 'wb') as f:
            f.write(b"Not an image")
        
        stats = self.downloader.get_download_stats()
        
        self.assertEqual(stats['total_images'], 3)
        self.assertEqual(stats['valid_images'], 2)
        self.assertEqual(stats['invalid_images'], 1)
        self.assertGreater(stats['total_size_mb'], 0)
        self.assertEqual(stats['supported_formats']['.png'], 2)  # PNG and invalid PNG
        self.assertEqual(stats['supported_formats']['.jpg'], 1)
        self.assertEqual(stats['images_dir'], self.images_dir)
    
    def test_error_handling_integration(self):
        """Test integration with error handling system."""
        # Test that error handler is properly initialized
        self.assertIsNotNone(self.downloader.error_handler)
        
        # Test error handling during download failure
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = self.downloader.download_character_image("Test", "https://example.com/image.png")
            self.assertIsNone(result)
            
            # Check that error was recorded
            self.assertGreater(len(self.downloader.error_handler.error_history), 0)
            error = self.downloader.error_handler.error_history[-1]
            self.assertEqual(error.category, ErrorCategory.IMAGE_DOWNLOAD)


class TestImageDownloaderIntegration(unittest.TestCase):
    """Integration tests for ImageDownloader with real file operations."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.images_dir = os.path.join(self.temp_dir, 'images')
        
        self.config = DatabaseBuilderConfig(
            images_dir=self.images_dir,
            rate_limit_delay=0.5,
            max_retries=1,
            timeout=5
        )
        
        self.downloader = ImageDownloader(self.config)
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_download_workflow(self):
        """Test complete download workflow with mocked network."""
        # Create test image data
        test_image = Image.new('RGB', (400, 500), color='green')
        test_image_data = BytesIO()
        test_image.save(test_image_data, format='PNG')
        test_image_bytes = test_image_data.getvalue()
        
        with patch('requests.Session.get') as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.content = test_image_bytes
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Test download
            character_name = "Integration Test Character"
            image_url = "https://example.com/test.png"
            
            result = self.downloader.download_character_image(character_name, image_url)
            
            # Verify results
            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(result))
            
            # Verify image can be loaded and processed
            self.assertTrue(self.downloader.validate_image_file(result))
            
            # Verify stats
            stats = self.downloader.get_download_stats()
            self.assertEqual(stats['total_images'], 1)
            self.assertEqual(stats['valid_images'], 1)
            
            # Test finding existing image
            found_path = self.downloader.get_image_path(character_name)
            self.assertEqual(found_path, result)


if __name__ == '__main__':
    unittest.main()