"""
Unit tests for configuration classes and validation.
"""

import unittest
from card_generator.config import (
    CardConfig, PrintConfig, OutputConfig, ConfigurationManager
)


class TestCardConfig(unittest.TestCase):
    """Test CardConfig class and validation."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CardConfig()
        
        self.assertEqual(config.base_width, 1745)
        self.assertEqual(config.base_height, 2468)
        self.assertEqual(config.dpi, 300)
        self.assertEqual(config.image_ratio, 0.6)
        self.assertEqual(config.margin, 50)
        self.assertEqual(config.inner_margin, 20)
        self.assertEqual(config.title_font_size, 48)
        self.assertEqual(config.stats_font_size, 36)
    
    def test_dpi_scaling(self):
        """Test DPI scaling calculations."""
        # Test 150 DPI (half scale)
        config = CardConfig(dpi=150)
        self.assertEqual(config.width, int(1745 * 0.5))
        self.assertEqual(config.height, int(2468 * 0.5))
        self.assertEqual(config.scaled_margin, int(50 * 0.5))
        self.assertEqual(config.scaled_title_font_size, int(48 * 0.5))
        
        # Test 600 DPI (double scale)
        config = CardConfig(dpi=600)
        self.assertEqual(config.width, int(1745 * 2.0))
        self.assertEqual(config.height, int(2468 * 2.0))
        self.assertEqual(config.scaled_margin, int(50 * 2.0))
        self.assertEqual(config.scaled_title_font_size, int(48 * 2.0))
    
    def test_calculated_properties(self):
        """Test calculated properties."""
        config = CardConfig()
        
        # Test image and text height calculations
        expected_image_height = int(config.height * 0.6)
        expected_text_height = config.height - expected_image_height
        
        self.assertEqual(config.image_height, expected_image_height)
        self.assertEqual(config.text_height, expected_text_height)
    
    def test_dpi_validation(self):
        """Test DPI validation."""
        # Valid DPI values
        CardConfig(dpi=72)  # Should not raise
        CardConfig(dpi=300)  # Should not raise
        CardConfig(dpi=600)  # Should not raise
        
        # Invalid DPI values
        with self.assertRaises(ValueError):
            CardConfig(dpi=50)  # Too low
        
        with self.assertRaises(ValueError):
            CardConfig(dpi=700)  # Too high
    
    def test_image_ratio_validation(self):
        """Test image ratio validation."""
        # Valid ratios
        CardConfig(image_ratio=0.3)  # Should not raise
        CardConfig(image_ratio=0.6)  # Should not raise
        CardConfig(image_ratio=0.8)  # Should not raise
        
        # Invalid ratios
        with self.assertRaises(ValueError):
            CardConfig(image_ratio=0.2)  # Too low
        
        with self.assertRaises(ValueError):
            CardConfig(image_ratio=0.9)  # Too high
    
    def test_margin_validation(self):
        """Test margin validation."""
        # Valid margins
        CardConfig(margin=10)  # Should not raise
        CardConfig(margin=50)  # Should not raise
        CardConfig(margin=200)  # Should not raise
        
        # Invalid margins
        with self.assertRaises(ValueError):
            CardConfig(margin=5)  # Too low
        
        with self.assertRaises(ValueError):
            CardConfig(margin=250)  # Too high
    
    def test_inner_margin_validation(self):
        """Test inner margin validation."""
        # Valid inner margins
        CardConfig(inner_margin=5)  # Should not raise
        CardConfig(inner_margin=20)  # Should not raise
        CardConfig(inner_margin=100)  # Should not raise
        
        # Invalid inner margins
        with self.assertRaises(ValueError):
            CardConfig(inner_margin=3)  # Too low
        
        with self.assertRaises(ValueError):
            CardConfig(inner_margin=150)  # Too high
    
    def test_font_size_validation(self):
        """Test font size validation."""
        # Valid font sizes
        CardConfig(title_font_size=20, stats_font_size=16)  # Should not raise
        CardConfig(title_font_size=100, stats_font_size=80)  # Should not raise
        
        # Invalid title font size
        with self.assertRaises(ValueError):
            CardConfig(title_font_size=15)  # Too low
        
        with self.assertRaises(ValueError):
            CardConfig(title_font_size=150)  # Too high
        
        # Invalid stats font size
        with self.assertRaises(ValueError):
            CardConfig(stats_font_size=10)  # Too low
        
        with self.assertRaises(ValueError):
            CardConfig(stats_font_size=100)  # Too high


class TestPrintConfig(unittest.TestCase):
    """Test PrintConfig class and validation."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PrintConfig()
        
        self.assertEqual(config.base_sheet_width, 3508)
        self.assertEqual(config.base_sheet_height, 2480)
        self.assertEqual(config.dpi, 300)
        self.assertEqual(config.cards_per_sheet, 2)
        self.assertEqual(config.sheet_margin, 6)
        self.assertEqual(config.card_spacing, 6)
        self.assertEqual(config.cut_guide_width, 2)
        self.assertEqual(config.cut_guide_length, 20)
        self.assertTrue(config.show_cut_guides)
    
    def test_dpi_scaling(self):
        """Test DPI scaling calculations."""
        # Test 150 DPI (half scale)
        config = PrintConfig(dpi=150)
        self.assertEqual(config.sheet_width, int(3508 * 0.5))
        self.assertEqual(config.sheet_height, int(2480 * 0.5))
        self.assertEqual(config.scaled_sheet_margin, int(6 * 0.5))
        self.assertEqual(config.scaled_card_spacing, int(6 * 0.5))
        
        # Test 600 DPI (double scale)
        config = PrintConfig(dpi=600)
        self.assertEqual(config.sheet_width, int(3508 * 2.0))
        self.assertEqual(config.sheet_height, int(2480 * 2.0))
        self.assertEqual(config.scaled_sheet_margin, int(6 * 2.0))
        self.assertEqual(config.scaled_card_spacing, int(6 * 2.0))
    
    def test_cards_per_sheet_validation(self):
        """Test cards per sheet validation."""
        # Valid values
        PrintConfig(cards_per_sheet=1)  # Should not raise
        PrintConfig(cards_per_sheet=6)  # Should not raise
        
        # Invalid values
        with self.assertRaises(ValueError):
            PrintConfig(cards_per_sheet=0)  # Too low
        
        with self.assertRaises(ValueError):
            PrintConfig(cards_per_sheet=7)  # Too high
    
    def test_margin_validation(self):
        """Test margin validation."""
        # Valid margins
        PrintConfig(sheet_margin=0)  # Should not raise
        PrintConfig(sheet_margin=100)  # Should not raise
        
        # Invalid margins
        with self.assertRaises(ValueError):
            PrintConfig(sheet_margin=-1)  # Negative
        
        with self.assertRaises(ValueError):
            PrintConfig(sheet_margin=150)  # Too high
    
    def test_spacing_validation(self):
        """Test spacing validation."""
        # Valid spacing
        PrintConfig(card_spacing=0)  # Should not raise
        PrintConfig(card_spacing=50)  # Should not raise
        
        # Invalid spacing
        with self.assertRaises(ValueError):
            PrintConfig(card_spacing=-1)  # Negative
        
        with self.assertRaises(ValueError):
            PrintConfig(card_spacing=60)  # Too high
    
    def test_cut_guide_validation(self):
        """Test cut guide validation."""
        # Valid cut guide settings
        PrintConfig(cut_guide_width=1, cut_guide_length=5)  # Should not raise
        PrintConfig(cut_guide_width=10, cut_guide_length=100)  # Should not raise
        
        # Invalid cut guide width
        with self.assertRaises(ValueError):
            PrintConfig(cut_guide_width=0)  # Too low
        
        with self.assertRaises(ValueError):
            PrintConfig(cut_guide_width=15)  # Too high
        
        # Invalid cut guide length
        with self.assertRaises(ValueError):
            PrintConfig(cut_guide_length=3)  # Too low
        
        with self.assertRaises(ValueError):
            PrintConfig(cut_guide_length=150)  # Too high


class TestOutputConfig(unittest.TestCase):
    """Test OutputConfig class and validation."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = OutputConfig()
        
        self.assertEqual(config.individual_cards_dir, 'output/individual_cards')
        self.assertEqual(config.print_sheets_dir, 'output/print_sheets')
        self.assertEqual(config.formats, ('PNG',))
        self.assertEqual(config.image_quality, 95)
        self.assertEqual(config.pdf_quality, 95)
        self.assertTrue(config.create_subdirectories)
        self.assertTrue(config.overwrite_existing)
    
    def test_format_validation(self):
        """Test format validation."""
        # Valid formats
        OutputConfig(formats=('PNG',))  # Should not raise
        OutputConfig(formats=('PDF',))  # Should not raise
        OutputConfig(formats=('JPEG',))  # Should not raise
        OutputConfig(formats=('PNG', 'PDF'))  # Should not raise
        OutputConfig(formats=('png', 'pdf'))  # Should not raise (case insensitive)
        
        # Invalid formats
        with self.assertRaises(ValueError):
            OutputConfig(formats=('BMP',))  # Unsupported format
        
        with self.assertRaises(ValueError):
            OutputConfig(formats=('PNG', 'INVALID'))  # Mixed valid/invalid
    
    def test_quality_validation(self):
        """Test quality validation."""
        # Valid quality values
        OutputConfig(image_quality=1, pdf_quality=1)  # Should not raise
        OutputConfig(image_quality=100, pdf_quality=100)  # Should not raise
        
        # Invalid image quality
        with self.assertRaises(ValueError):
            OutputConfig(image_quality=0)  # Too low
        
        with self.assertRaises(ValueError):
            OutputConfig(image_quality=101)  # Too high
        
        # Invalid PDF quality
        with self.assertRaises(ValueError):
            OutputConfig(pdf_quality=0)  # Too low
        
        with self.assertRaises(ValueError):
            OutputConfig(pdf_quality=101)  # Too high
    
    def test_filename_template_validation(self):
        """Test filename template validation."""
        # Valid templates
        OutputConfig(
            card_filename_template='{name}_{tier}_card',
            sheet_filename_template='sheet_{batch_number:03d}'
        )  # Should not raise
        
        # Invalid card template (missing required variables)
        with self.assertRaises(ValueError):
            OutputConfig(card_filename_template='{name}_card')  # Missing {tier}
        
        with self.assertRaises(ValueError):
            OutputConfig(card_filename_template='{tier}_card')  # Missing {name}
        
        # Invalid sheet template (missing required variable)
        with self.assertRaises(ValueError):
            OutputConfig(sheet_filename_template='sheet')  # Missing {batch_number}
        
        # Empty templates
        with self.assertRaises(ValueError):
            OutputConfig(card_filename_template='')
        
        with self.assertRaises(ValueError):
            OutputConfig(sheet_filename_template='')
    
    def test_normalized_formats(self):
        """Test format normalization."""
        config = OutputConfig(formats=('png', 'pdf', 'jpeg'))
        normalized = config.normalized_formats
        
        self.assertEqual(normalized, ('PNG', 'PDF', 'JPEG'))
    
    def test_filename_generation(self):
        """Test filename generation methods."""
        config = OutputConfig()
        
        # Test card filename generation
        card_filename = config.get_card_filename('Test Character', 'Rare', 'PNG')
        self.assertEqual(card_filename, 'Test_Character_Rare_card.png')
        
        # Test with special characters
        card_filename = config.get_card_filename('Test & Character!', 'Epic', 'PDF')
        self.assertEqual(card_filename, 'Test__Character_Epic_card.pdf')
        
        # Test sheet filename generation
        sheet_filename = config.get_sheet_filename(5, 'PNG')
        self.assertEqual(sheet_filename, 'print_sheet_005.png')


class TestConfigurationManager(unittest.TestCase):
    """Test ConfigurationManager factory methods."""
    
    def test_create_card_config(self):
        """Test card config creation with overrides."""
        config = ConfigurationManager.create_card_config(
            dpi=150,
            image_ratio=0.7,
            margin=30
        )
        
        self.assertEqual(config.dpi, 150)
        self.assertEqual(config.image_ratio, 0.7)
        self.assertEqual(config.margin, 30)
        # Other values should be defaults
        self.assertEqual(config.inner_margin, 20)
    
    def test_create_print_config(self):
        """Test print config creation with overrides."""
        config = ConfigurationManager.create_print_config(
            dpi=150,
            cards_per_sheet=4,
            show_cut_guides=False
        )
        
        self.assertEqual(config.dpi, 150)
        self.assertEqual(config.cards_per_sheet, 4)
        self.assertFalse(config.show_cut_guides)
        # Other values should be defaults
        self.assertEqual(config.sheet_margin, 6)
    
    def test_create_output_config(self):
        """Test output config creation with overrides."""
        config = ConfigurationManager.create_output_config(
            formats=('PNG', 'PDF'),
            image_quality=85,
            create_subdirectories=False
        )
        
        self.assertEqual(config.formats, ('PNG', 'PDF'))
        self.assertEqual(config.image_quality, 85)
        self.assertFalse(config.create_subdirectories)
        # Other values should be defaults
        self.assertEqual(config.pdf_quality, 95)
    
    def test_dpi_compatibility_validation(self):
        """Test DPI compatibility validation."""
        card_config = CardConfig(dpi=300)
        print_config = PrintConfig(dpi=300)
        
        # Should not raise with matching DPI
        self.assertTrue(
            ConfigurationManager.validate_dpi_compatibility(card_config, print_config)
        )
        
        # Should raise with mismatched DPI
        print_config_different = PrintConfig(dpi=150)
        with self.assertRaises(ValueError):
            ConfigurationManager.validate_dpi_compatibility(card_config, print_config_different)
    
    def test_invalid_overrides(self):
        """Test that invalid overrides still raise validation errors."""
        # Invalid DPI should still raise error
        with self.assertRaises(ValueError):
            ConfigurationManager.create_card_config(dpi=50)
        
        # Invalid cards per sheet should still raise error
        with self.assertRaises(ValueError):
            ConfigurationManager.create_print_config(cards_per_sheet=10)
        
        # Invalid format should still raise error
        with self.assertRaises(ValueError):
            ConfigurationManager.create_output_config(formats=('INVALID',))


if __name__ == '__main__':
    unittest.main()