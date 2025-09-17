"""
Unit tests for the ImageProcessor class.

Tests image loading, resizing, cropping, validation, and placeholder generation
with various image formats and sizes.
"""

import unittest
import os
import tempfile
import shutil
from PIL import Image, ImageDraw
from unittest.mock import patch, MagicMock

from card_generator.image_processor import ImageProcessor
from card_generator.config import CardConfig, TIER_COLORS


class TestImageProcessor(unittest.TestCase):
    """Test cases for ImageProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = ImageProcessor()
        self.test_dir = tempfile.mkdtemp()
        self.config = CardConfig()
        
        # Create test images
        self.create_test_images()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_images(self):
        """Create test images with various formats and sizes."""
        # Standard RGB image
        self.rgb_image_path = os.path.join(self.test_dir, 'test_rgb.png')
        rgb_image = Image.new('RGB', (800, 600), 'red')
        rgb_image.save(self.rgb_image_path)
        
        # RGBA image (with transparency)
        self.rgba_image_path = os.path.join(self.test_dir, 'test_rgba.png')
        rgba_image = Image.new('RGBA', (400, 400), (0, 255, 0, 128))
        rgba_image.save(self.rgba_image_path)
        
        # Small image (below minimum quality)
        self.small_image_path = os.path.join(self.test_dir, 'test_small.png')
        small_image = Image.new('RGB', (100, 100), 'blue')
        small_image.save(self.small_image_path)
        
        # Wide aspect ratio image
        self.wide_image_path = os.path.join(self.test_dir, 'test_wide.png')
        wide_image = Image.new('RGB', (1200, 300), 'yellow')
        wide_image.save(self.wide_image_path)
        
        # Tall aspect ratio image
        self.tall_image_path = os.path.join(self.test_dir, 'test_tall.png')
        tall_image = Image.new('RGB', (300, 1200), 'purple')
        tall_image.save(self.tall_image_path)
        
        # JPEG image
        self.jpeg_image_path = os.path.join(self.test_dir, 'test.jpg')
        jpeg_image = Image.new('RGB', (600, 800), 'orange')
        jpeg_image.save(self.jpeg_image_path, 'JPEG')
        
        # Extreme aspect ratio (should fail validation)
        self.extreme_image_path = os.path.join(self.test_dir, 'test_extreme.png')
        extreme_image = Image.new('RGB', (2000, 100), 'cyan')
        extreme_image.save(self.extreme_image_path)
    
    def test_init_default_config(self):
        """Test ImageProcessor initialization with default config."""
        processor = ImageProcessor()
        self.assertIsInstance(processor.config, CardConfig)
        # Calculate expected target size: (width - 2*margin, image_height - 2*margin)
        expected_width = processor.config.width - (2 * processor.config.scaled_margin)
        expected_height = processor.config.image_height - (2 * processor.config.scaled_margin)
        self.assertEqual(processor.target_image_size, (expected_width, expected_height))
    
    def test_init_custom_config(self):
        """Test ImageProcessor initialization with custom config."""
        custom_config = CardConfig(dpi=150, margin=25)  # Use valid CardConfig parameters
        processor = ImageProcessor(custom_config)
        self.assertEqual(processor.config, custom_config)
        # Calculate expected target size based on the custom config
        expected_width = custom_config.width - (2 * custom_config.scaled_margin)
        expected_height = custom_config.image_height - (2 * custom_config.scaled_margin)
        self.assertEqual(processor.target_image_size, (expected_width, expected_height))
    
    def test_load_image_success(self):
        """Test successful image loading."""
        image = self.processor.load_image(self.rgb_image_path)
        self.assertIsNotNone(image)
        self.assertEqual(image.mode, 'RGB')
        self.assertEqual(image.size, (800, 600))
    
    def test_load_image_rgba_conversion(self):
        """Test RGBA image conversion to RGB."""
        image = self.processor.load_image(self.rgba_image_path)
        self.assertIsNotNone(image)
        self.assertEqual(image.mode, 'RGB')
    
    def test_load_image_jpeg(self):
        """Test JPEG image loading."""
        image = self.processor.load_image(self.jpeg_image_path)
        self.assertIsNotNone(image)
        self.assertEqual(image.mode, 'RGB')
        self.assertEqual(image.size, (600, 800))
    
    def test_load_image_file_not_found(self):
        """Test loading non-existent image file."""
        with self.assertRaises(FileNotFoundError):
            self.processor.load_image('nonexistent.png')
    
    def test_load_image_unsupported_format(self):
        """Test loading unsupported image format."""
        unsupported_path = os.path.join(self.test_dir, 'test.txt')
        with open(unsupported_path, 'w') as f:
            f.write('not an image')
        
        with self.assertRaises(ValueError):
            self.processor.load_image(unsupported_path)
    
    def test_load_image_quality_validation_fail(self):
        """Test image quality validation failure."""
        image = self.processor.load_image(self.small_image_path)
        self.assertIsNone(image)  # Should return None for low quality
    
    def test_load_image_extreme_aspect_ratio(self):
        """Test image with extreme aspect ratio."""
        image = self.processor.load_image(self.extreme_image_path)
        self.assertIsNone(image)  # Should return None for extreme aspect ratio
    
    def test_resize_and_crop_wide_image(self):
        """Test resizing a wide image with height-based scaling."""
        original_image = Image.new('RGB', (1200, 600), 'red')
        target_size = (400, 400)
        
        result = self.processor.resize_and_crop(original_image, target_size)
        
        # With height-based scaling, should scale to target height and maintain aspect ratio
        aspect_ratio = original_image.width / original_image.height
        expected_width = int(400 * aspect_ratio)  # Scale based on height
        if expected_width > 400:  # If too wide, constrain by width
            expected_width = 400
            expected_height = int(400 / aspect_ratio)
            self.assertEqual(result.size, (expected_width, expected_height))
        else:
            self.assertEqual(result.size, (expected_width, 400))
        self.assertEqual(result.mode, 'RGB')
    
    def test_resize_and_crop_tall_image(self):
        """Test resizing a tall image with height-based scaling."""
        original_image = Image.new('RGB', (600, 1200), 'blue')
        target_size = (400, 400)
        
        result = self.processor.resize_and_crop(original_image, target_size)
        
        # With height-based scaling, should scale to target height and maintain aspect ratio
        aspect_ratio = original_image.width / original_image.height
        expected_width = int(400 * aspect_ratio)  # Scale based on height
        self.assertEqual(result.size, (expected_width, 400))
        self.assertEqual(result.mode, 'RGB')
    
    def test_resize_and_crop_default_size(self):
        """Test resizing with default target size using height-based scaling."""
        original_image = Image.new('RGB', (800, 600), 'green')
        
        result = self.processor.resize_and_crop(original_image)
        
        # With height-based scaling, calculate expected size
        target_width, target_height = self.processor.target_image_size
        aspect_ratio = original_image.width / original_image.height
        expected_width = int(target_height * aspect_ratio)
        
        if expected_width > target_width:
            # Constrained by width
            scale_factor = target_width / expected_width
            expected_width = target_width
            expected_height = int(target_height * scale_factor)
            self.assertEqual(result.size, (expected_width, expected_height))
        else:
            # Scale to height
            self.assertEqual(result.size, (expected_width, target_height))
    
    def test_resize_and_crop_square_to_square(self):
        """Test resizing square image to square target."""
        original_image = Image.new('RGB', (600, 600), 'yellow')
        target_size = (400, 400)
        
        result = self.processor.resize_and_crop(original_image, target_size)
        
        self.assertEqual(result.size, target_size)
    
    def test_resize_and_crop_height_based_scaling(self):
        """Test that resize_and_crop uses height-based scaling without cropping."""
        # Create a portrait image
        portrait_image = Image.new('RGB', (400, 800), 'magenta')
        target_size = (600, 600)
        
        result = self.processor.resize_and_crop(portrait_image, target_size)
        
        # Should scale to target height while maintaining aspect ratio
        expected_width = int(600 * (400 / 800))  # Scale based on height
        self.assertEqual(result.size, (expected_width, 600))
        
        # Verify aspect ratio is preserved
        original_ratio = portrait_image.width / portrait_image.height
        result_ratio = result.width / result.height
        self.assertAlmostEqual(original_ratio, result_ratio, places=2)
    
    def test_resize_and_crop_portrait_no_cropping(self):
        """Test that portrait images are not cropped with height-based scaling."""
        # Create a very tall portrait image
        tall_portrait = Image.new('RGB', (200, 1000), 'cyan')
        target_size = (400, 600)
        
        result = self.processor.resize_and_crop(tall_portrait, target_size)
        
        # Should maintain aspect ratio without cropping
        original_ratio = tall_portrait.width / tall_portrait.height
        result_ratio = result.width / result.height
        self.assertAlmostEqual(original_ratio, result_ratio, places=2)
        
        # Should scale to fit height
        expected_width = int(600 * original_ratio)
        self.assertEqual(result.size, (expected_width, 600))
    
    def test_resize_and_crop_wide_image_constraint(self):
        """Test height-based scaling with width constraint for very wide images."""
        # Create a very wide image
        wide_image = Image.new('RGB', (2000, 500), 'lime')
        target_size = (400, 600)
        
        result = self.processor.resize_and_crop(wide_image, target_size)
        
        # Should be constrained by target width when calculated width exceeds it
        aspect_ratio = wide_image.width / wide_image.height
        expected_width_unconstrained = int(600 * aspect_ratio)
        
        if expected_width_unconstrained > 400:
            # Should be constrained to target width
            self.assertEqual(result.width, 400)
            # Height should be scaled proportionally
            scale_factor = 400 / expected_width_unconstrained
            expected_height = int(600 * scale_factor)
            self.assertEqual(result.height, expected_height)
        else:
            # Should use height-based scaling
            self.assertEqual(result.height, 600)
            self.assertEqual(result.width, expected_width_unconstrained)
    
    def test_resize_and_crop_maintains_content(self):
        """Test that height-based scaling preserves image content without cropping."""
        # Create an image with distinctive content
        test_image = Image.new('RGB', (300, 900), 'white')
        draw = ImageDraw.Draw(test_image)
        
        # Add content at top, middle, and bottom
        draw.rectangle([50, 50, 250, 150], fill='red')      # Top
        draw.rectangle([50, 400, 250, 500], fill='green')   # Middle  
        draw.rectangle([50, 750, 250, 850], fill='blue')    # Bottom
        
        target_size = (400, 600)
        result = self.processor.resize_and_crop(test_image, target_size)
        
        # Should maintain aspect ratio (no cropping)
        original_ratio = test_image.width / test_image.height
        result_ratio = result.width / result.height
        self.assertAlmostEqual(original_ratio, result_ratio, places=2)
        
        # Should scale to fit height
        expected_width = int(600 * original_ratio)
        self.assertEqual(result.size, (expected_width, 600))
    
    def test_create_placeholder_common_tier(self):
        """Test placeholder creation for common tier."""
        placeholder = self.processor.create_placeholder('Test Character', 'Common')
        
        self.assertEqual(placeholder.size, self.processor.target_image_size)
        self.assertEqual(placeholder.mode, 'RGB')
    
    def test_create_placeholder_legendary_tier(self):
        """Test placeholder creation for legendary tier."""
        placeholder = self.processor.create_placeholder('Epic Hero', 'Legendary')
        
        self.assertEqual(placeholder.size, self.processor.target_image_size)
        self.assertEqual(placeholder.mode, 'RGB')
    
    def test_create_placeholder_unknown_tier(self):
        """Test placeholder creation for unknown tier (should default to Common)."""
        placeholder = self.processor.create_placeholder('Unknown Character', 'UnknownTier')
        
        self.assertEqual(placeholder.size, self.processor.target_image_size)
        self.assertEqual(placeholder.mode, 'RGB')
    
    def test_create_placeholder_custom_size(self):
        """Test placeholder creation with custom size."""
        custom_size = (300, 400)
        placeholder = self.processor.create_placeholder('Custom Character', 'Epic', custom_size)
        
        self.assertEqual(placeholder.size, custom_size)
    
    def test_create_placeholder_long_name(self):
        """Test placeholder creation with very long character name."""
        long_name = 'This Is A Very Long Character Name That Should Be Wrapped'
        placeholder = self.processor.create_placeholder(long_name, 'Rare')
        
        self.assertEqual(placeholder.size, self.processor.target_image_size)
        self.assertEqual(placeholder.mode, 'RGB')
    
    def test_validate_image_quality_good_image(self):
        """Test image quality validation for good image."""
        good_image = Image.new('RGB', (800, 600), 'red')
        self.assertTrue(self.processor._validate_image_quality(good_image))
    
    def test_validate_image_quality_too_small(self):
        """Test image quality validation for too small image."""
        small_image = Image.new('RGB', (100, 100), 'red')
        self.assertFalse(self.processor._validate_image_quality(small_image))
    
    def test_validate_image_quality_extreme_aspect_ratio(self):
        """Test image quality validation for extreme aspect ratio."""
        extreme_image = Image.new('RGB', (2000, 100), 'red')
        self.assertFalse(self.processor._validate_image_quality(extreme_image))
    
    def test_darken_color(self):
        """Test color darkening function."""
        # Test with red color
        darkened = self.processor._darken_color('#FF0000', 0.5)
        self.assertEqual(darkened, '#7f0000')
        
        # Test with no darkening
        no_change = self.processor._darken_color('#FF0000', 0.0)
        self.assertEqual(no_change, '#ff0000')
        
        # Test with full darkening
        black = self.processor._darken_color('#FF0000', 1.0)
        self.assertEqual(black, '#000000')
    
    def test_wrap_text_short_text(self):
        """Test text wrapping with short text."""
        from PIL import ImageFont
        font = ImageFont.load_default()
        
        lines = self.processor._wrap_text('Short', font, 1000)
        self.assertEqual(lines, ['Short'])
    
    def test_wrap_text_long_text(self):
        """Test text wrapping with long text."""
        from PIL import ImageFont
        font = ImageFont.load_default()
        
        long_text = 'This is a very long text that should be wrapped into multiple lines'
        lines = self.processor._wrap_text(long_text, font, 100)
        
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(isinstance(line, str) for line in lines))
    
    def test_wrap_text_single_long_word(self):
        """Test text wrapping with single very long word."""
        from PIL import ImageFont
        font = ImageFont.load_default()
        
        long_word = 'Supercalifragilisticexpialidocious'
        lines = self.processor._wrap_text(long_word, font, 50)
        
        self.assertEqual(lines, [long_word])  # Should include the word even if too long
    
    @patch('card_generator.image_processor.logging.getLogger')
    def test_logging_integration(self, mock_logger):
        """Test that logging is properly integrated."""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        processor = ImageProcessor()
        
        # Test successful image load logging
        image = processor.load_image(self.rgb_image_path)
        mock_logger_instance.info.assert_called()
        
        # Test placeholder creation logging
        placeholder = processor.create_placeholder('Test', 'Common')
        mock_logger_instance.info.assert_called()


class TestImageProcessorIntegration(unittest.TestCase):
    """Integration tests for ImageProcessor with real image processing."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.processor = ImageProcessor()
        self.test_dir = tempfile.mkdtemp()
        
        # Create a realistic test image
        self.test_image_path = os.path.join(self.test_dir, 'character.png')
        test_image = Image.new('RGB', (512, 512), 'red')
        
        # Add some detail to make it more realistic
        draw = ImageDraw.Draw(test_image)
        draw.rectangle([100, 100, 400, 400], fill='blue')
        draw.ellipse([150, 150, 350, 350], fill='yellow')
        
        test_image.save(self.test_image_path)
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_image_processing_pipeline(self):
        """Test complete image processing pipeline."""
        # Load image
        image = self.processor.load_image(self.test_image_path)
        self.assertIsNotNone(image)
        
        # Resize using height-based scaling
        target_size = (400, 300)
        processed_image = self.processor.resize_and_crop(image, target_size)
        
        # With height-based scaling, calculate expected size
        aspect_ratio = image.width / image.height  # 512/512 = 1.0 (square)
        expected_width = int(300 * aspect_ratio)  # 300 * 1.0 = 300
        self.assertEqual(processed_image.size, (expected_width, 300))
        
        # Verify image quality is maintained
        self.assertEqual(processed_image.mode, 'RGB')
    
    def test_placeholder_vs_real_image_consistency(self):
        """Test that placeholder and real images have consistent properties."""
        # Load real image
        real_image = self.processor.load_image(self.test_image_path)
        processed_real = self.processor.resize_and_crop(real_image)
        
        # Create placeholder
        placeholder = self.processor.create_placeholder('Test Character', 'Epic')
        
        # Both should have same mode, but sizes may differ due to height-based scaling
        # The placeholder uses the full target size, while processed real image uses height-based scaling
        self.assertEqual(processed_real.mode, placeholder.mode)
        
        # Verify both are valid images
        self.assertIsInstance(processed_real, Image.Image)
        self.assertIsInstance(placeholder, Image.Image)


if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    unittest.main()