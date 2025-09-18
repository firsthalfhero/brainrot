"""
Unit tests for the DatabaseBuilder orchestrator class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from card_generator.database_builder import DatabaseBuilder, DatabaseBuildResult, ProcessingProgress
from card_generator.config import DatabaseBuilderConfig
from card_generator.data_models import CharacterData
from card_generator.error_handling import ErrorCategory, ErrorSeverity


class TestDatabaseBuilder(unittest.TestCase):
    """Test cases for DatabaseBuilder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = DatabaseBuilderConfig(
            output_dir=str(Path(self.temp_dir) / "databases"),
            images_dir=str(Path(self.temp_dir) / "images"),
            rate_limit_delay=0.5,  # Minimum allowed for testing
            max_retries=1  # Fewer retries for testing
        )
        
        # Create test directories
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.images_dir).mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_database_builder_initialization(self):
        """Test DatabaseBuilder initialization."""
        builder = DatabaseBuilder(self.config)
        
        self.assertIsNotNone(builder.config)
        self.assertIsNotNone(builder.wiki_scraper)
        self.assertIsNotNone(builder.character_extractor)
        self.assertIsNotNone(builder.image_downloader)
        self.assertIsNotNone(builder.csv_generator)
        self.assertIsNotNone(builder.progress)
        self.assertIsNotNone(builder.build_result)
    
    @patch('card_generator.database_builder.WikiScraper')
    @patch('card_generator.database_builder.CharacterDataExtractor')
    @patch('card_generator.database_builder.ImageDownloader')
    @patch('card_generator.database_builder.CSVGenerator')
    def test_build_database_success(self, mock_csv_gen, mock_img_dl, mock_char_ext, mock_wiki):
        """Test successful database build process."""
        # Mock wiki scraper
        mock_wiki_instance = Mock()
        mock_wiki.return_value = mock_wiki_instance
        mock_wiki_instance.scrape_brainrots_page.return_value = {
            'Common': ['Character1', 'Character2'],
            'Rare': ['Character3']
        }
        
        # Mock character extractor
        mock_char_ext_instance = Mock()
        mock_char_ext.return_value = mock_char_ext_instance
        
        def mock_extract_character_data(name, tier):
            character = CharacterData(
                name=name,
                tier=tier,
                cost=100,
                income=10,
                variant="Standard"
            )
            character.extraction_success = True
            character.image_url = f"http://example.com/{name}.png"
            return character
        
        mock_char_ext_instance.extract_character_data.side_effect = mock_extract_character_data
        
        # Mock image downloader
        mock_img_dl_instance = Mock()
        mock_img_dl.return_value = mock_img_dl_instance
        mock_img_dl_instance.download_character_image.return_value = f"{self.config.images_dir}/test.png"
        
        # Mock CSV generator
        mock_csv_gen_instance = Mock()
        mock_csv_gen.return_value = mock_csv_gen_instance
        mock_csv_gen_instance.generate_csv.return_value = f"{self.config.output_dir}/test.csv"
        
        # Build database
        builder = DatabaseBuilder(self.config)
        result = builder.build_database()
        
        # Verify results
        self.assertIsInstance(result, DatabaseBuildResult)
        self.assertEqual(result.total_characters, 3)
        self.assertEqual(result.successful_extractions, 3)
        self.assertEqual(result.failed_extractions, 0)
        self.assertEqual(result.images_downloaded, 3)
        self.assertEqual(result.images_failed, 0)
        self.assertTrue(result.csv_file_path.endswith('test.csv'))
        self.assertGreater(result.processing_time, 0)
        
        # Verify method calls
        mock_wiki_instance.scrape_brainrots_page.assert_called_once()
        self.assertEqual(mock_char_ext_instance.extract_character_data.call_count, 3)
        self.assertEqual(mock_img_dl_instance.download_character_image.call_count, 3)
        mock_csv_gen_instance.generate_csv.assert_called_once()
    
    @patch('card_generator.database_builder.WikiScraper')
    def test_build_database_wiki_scraping_failure(self, mock_wiki):
        """Test database build with wiki scraping failure."""
        # Mock wiki scraper to fail
        mock_wiki_instance = Mock()
        mock_wiki.return_value = mock_wiki_instance
        mock_wiki_instance.scrape_brainrots_page.side_effect = Exception("Wiki scraping failed")
        
        builder = DatabaseBuilder(self.config)
        
        with self.assertRaises(Exception) as context:
            builder.build_database()
        
        self.assertIn("Could not scrape main wiki page", str(context.exception))
    
    @patch('card_generator.database_builder.WikiScraper')
    @patch('card_generator.database_builder.CharacterDataExtractor')
    @patch('card_generator.database_builder.ImageDownloader')
    @patch('card_generator.database_builder.CSVGenerator')
    def test_build_database_partial_failures(self, mock_csv_gen, mock_img_dl, mock_char_ext, mock_wiki):
        """Test database build with partial character extraction failures."""
        # Mock wiki scraper
        mock_wiki_instance = Mock()
        mock_wiki.return_value = mock_wiki_instance
        mock_wiki_instance.scrape_brainrots_page.return_value = {
            'Common': ['Character1', 'Character2', 'Character3']
        }
        
        # Mock character extractor with mixed results
        mock_char_ext_instance = Mock()
        mock_char_ext.return_value = mock_char_ext_instance
        
        def mock_extract_character_data(name, tier):
            if name == 'Character2':
                # Simulate extraction failure
                return None
            elif name == 'Character3':
                # Simulate partial failure
                character = CharacterData(
                    name=name,
                    tier=tier,
                    cost=0,
                    income=0,
                    variant="Standard"
                )
                character.extraction_success = False
                character.extraction_errors = ["Failed to extract cost"]
                return character
            else:
                # Successful extraction
                character = CharacterData(
                    name=name,
                    tier=tier,
                    cost=100,
                    income=10,
                    variant="Standard"
                )
                character.extraction_success = True
                character.image_url = f"http://example.com/{name}.png"
                return character
        
        mock_char_ext_instance.extract_character_data.side_effect = mock_extract_character_data
        
        # Mock image downloader with mixed results
        mock_img_dl_instance = Mock()
        mock_img_dl.return_value = mock_img_dl_instance
        
        def mock_download_image(name, url):
            if name == 'Character1':
                return f"{self.config.images_dir}/{name}.png"
            else:
                return None  # Download failure
        
        mock_img_dl_instance.download_character_image.side_effect = mock_download_image
        
        # Mock CSV generator
        mock_csv_gen_instance = Mock()
        mock_csv_gen.return_value = mock_csv_gen_instance
        mock_csv_gen_instance.generate_csv.return_value = f"{self.config.output_dir}/test.csv"
        
        # Build database
        builder = DatabaseBuilder(self.config)
        result = builder.build_database()
        
        # Verify results show partial failures
        self.assertEqual(result.total_characters, 3)
        self.assertEqual(result.successful_extractions, 1)  # Only Character1 fully successful
        self.assertEqual(result.failed_extractions, 2)
        self.assertEqual(result.images_downloaded, 1)  # Only Character1 image downloaded
        self.assertEqual(result.images_failed, 0)  # Character2 and 3 didn't have image URLs to fail
        self.assertGreater(len(result.warnings), 0)
    
    def test_processing_progress_tracking(self):
        """Test progress tracking functionality."""
        import time
        
        progress = ProcessingProgress()
        progress.total_characters = 100
        progress.characters_processed = 25
        
        # Wait a tiny bit to ensure elapsed time > 0
        time.sleep(0.001)
        
        self.assertEqual(progress.get_progress_percentage(), 25.0)
        self.assertGreaterEqual(progress.get_elapsed_time(), 0)
        
        # Test estimated remaining time
        remaining = progress.get_estimated_remaining_time()
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 0)
    
    def test_database_build_result_calculations(self):
        """Test DatabaseBuildResult calculation methods."""
        result = DatabaseBuildResult()
        result.total_characters = 100
        result.successful_extractions = 80
        result.images_downloaded = 70
        result.images_failed = 10
        
        self.assertEqual(result.get_success_rate(), 80.0)
        self.assertEqual(result.get_image_success_rate(), 87.5)  # 70/(70+10) * 100
    
    def test_get_progress_info(self):
        """Test progress information retrieval."""
        builder = DatabaseBuilder(self.config)
        builder.progress.current_tier = "Common"
        builder.progress.current_character = "TestCharacter"
        builder.progress.characters_processed = 5
        builder.progress.total_characters = 20
        
        progress_info = builder.get_progress_info()
        
        self.assertEqual(progress_info['current_tier'], "Common")
        self.assertEqual(progress_info['current_character'], "TestCharacter")
        self.assertEqual(progress_info['characters_processed'], 5)
        self.assertEqual(progress_info['total_characters'], 20)
        self.assertEqual(progress_info['progress_percentage'], 25.0)
        self.assertIn('elapsed_time', progress_info)
        self.assertIn('estimated_remaining_time', progress_info)
    
    @patch('card_generator.database_builder.WikiScraper')
    @patch('card_generator.database_builder.CharacterDataExtractor')
    @patch('card_generator.database_builder.ImageDownloader')
    @patch('card_generator.database_builder.CSVGenerator')
    def test_tier_statistics_tracking(self, mock_csv_gen, mock_img_dl, mock_char_ext, mock_wiki):
        """Test tier-by-tier statistics tracking."""
        # Mock wiki scraper
        mock_wiki_instance = Mock()
        mock_wiki.return_value = mock_wiki_instance
        mock_wiki_instance.scrape_brainrots_page.return_value = {
            'Common': ['Char1', 'Char2'],
            'Rare': ['Char3']
        }
        
        # Mock character extractor
        mock_char_ext_instance = Mock()
        mock_char_ext.return_value = mock_char_ext_instance
        
        def mock_extract_character_data(name, tier):
            character = CharacterData(
                name=name,
                tier=tier,
                cost=100,
                income=10,
                variant="Standard"
            )
            character.extraction_success = True
            character.image_url = f"http://example.com/{name}.png"
            return character
        
        mock_char_ext_instance.extract_character_data.side_effect = mock_extract_character_data
        
        # Mock image downloader
        mock_img_dl_instance = Mock()
        mock_img_dl.return_value = mock_img_dl_instance
        mock_img_dl_instance.download_character_image.return_value = f"{self.config.images_dir}/test.png"
        
        # Mock CSV generator
        mock_csv_gen_instance = Mock()
        mock_csv_gen.return_value = mock_csv_gen_instance
        mock_csv_gen_instance.generate_csv.return_value = f"{self.config.output_dir}/test.csv"
        
        # Build database
        builder = DatabaseBuilder(self.config)
        result = builder.build_database()
        
        # Verify tier statistics
        self.assertIn('Common', result.tier_statistics)
        self.assertIn('Rare', result.tier_statistics)
        
        common_stats = result.tier_statistics['Common']
        self.assertEqual(common_stats['total'], 2)
        self.assertEqual(common_stats['successful'], 2)
        self.assertEqual(common_stats['failed'], 0)
        self.assertEqual(common_stats['images_downloaded'], 2)
        
        rare_stats = result.tier_statistics['Rare']
        self.assertEqual(rare_stats['total'], 1)
        self.assertEqual(rare_stats['successful'], 1)
        self.assertEqual(rare_stats['failed'], 0)
        self.assertEqual(rare_stats['images_downloaded'], 1)


if __name__ == '__main__':
    unittest.main()