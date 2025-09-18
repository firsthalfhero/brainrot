"""
Unit tests for the CharacterDataExtractor module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
import requests

from card_generator.character_data_extractor import CharacterDataExtractor
from card_generator.data_models import CharacterData


class TestCharacterDataExtractor(unittest.TestCase):
    """Test cases for CharacterDataExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = CharacterDataExtractor()
    
    def tearDown(self):
        """Clean up after tests."""
        self.extractor.close()
    
    def test_init(self):
        """Test CharacterDataExtractor initialization."""
        self.assertEqual(self.extractor.base_url, "https://stealabrainrot.fandom.com")
        self.assertIsNotNone(self.extractor.session)
        self.assertIsNotNone(self.extractor.rate_limiter)
        self.assertIsNotNone(self.extractor.error_handler)
    
    def test_generate_url_variations(self):
        """Test URL variation generation."""
        variations = self.extractor._generate_url_variations("Test Character")
        
        self.assertIsInstance(variations, list)
        self.assertTrue(len(variations) > 0)
        
        # Check that variations contain expected patterns
        variation_strings = [str(v) for v in variations]
        self.assertTrue(any("Test_Character" in v for v in variation_strings))
        self.assertTrue(any("Test%20Character" in v for v in variation_strings))
    
    def test_generate_url_variations_special_characters(self):
        """Test URL variation generation with special characters."""
        variations = self.extractor._generate_url_variations("Test-Character!")
        
        self.assertIsInstance(variations, list)
        self.assertTrue(len(variations) > 0)
        
        # Should handle special characters
        variation_strings = [str(v) for v in variations]
        self.assertTrue(any("Test-Character" in v for v in variation_strings))
    
    def test_parse_numeric_value_simple(self):
        """Test parsing simple numeric values."""
        self.assertEqual(self.extractor._parse_numeric_value("100"), 100)
        self.assertEqual(self.extractor._parse_numeric_value("1,500"), 1500)
        self.assertEqual(self.extractor._parse_numeric_value("2.5k"), 2500)
        self.assertEqual(self.extractor._parse_numeric_value("Cost: 500"), 500)
    
    def test_parse_numeric_value_complex(self):
        """Test parsing complex numeric formats."""
        self.assertEqual(self.extractor._parse_numeric_value("Income: $1,200 per second"), 1200)
        self.assertEqual(self.extractor._parse_numeric_value("Price: 3.5k coins"), 3500)
        self.assertIsNone(self.extractor._parse_numeric_value("No numbers here"))
    
    def test_extract_image_url_from_infobox(self):
        """Test image URL extraction from infobox."""
        # Mock HTML with image in infobox
        html = """
        <table class="infobox">
            <tr>
                <td>
                    <figure class="pi-item pi-image">
                        <img src="/images/test_character.png" alt="Test Character">
                    </figure>
                </td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        infobox = soup.find('table', class_='infobox')
        
        image_url = self.extractor._extract_image_url(infobox, soup)
        self.assertIsNotNone(image_url)
        self.assertTrue(image_url.endswith('test_character.png'))
    
    def test_extract_numeric_field_from_infobox(self):
        """Test numeric field extraction from infobox."""
        # Mock HTML with cost and income data
        html = """
        <table class="infobox">
            <tr>
                <td>Cost</td>
                <td>1,500</td>
            </tr>
            <tr>
                <td>Income per second</td>
                <td>75</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        infobox = soup.find('table', class_='infobox')
        
        cost = self.extractor._extract_numeric_field(infobox, ['cost'])
        income = self.extractor._extract_numeric_field(infobox, ['income', 'per second'])
        
        self.assertEqual(cost, 1500)
        self.assertEqual(income, 75)
    
    def test_extract_infobox_data_complete(self):
        """Test complete infobox data extraction."""
        # Mock HTML with complete infobox
        html = """
        <table class="infobox">
            <tr>
                <td colspan="2">
                    <figure class="pi-item pi-image">
                        <img src="/images/test_character.png" alt="Test Character">
                    </figure>
                </td>
            </tr>
            <tr>
                <td>Cost</td>
                <td>2,000</td>
            </tr>
            <tr>
                <td>Income per second</td>
                <td>100</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        data = self.extractor._extract_infobox_data(soup)
        
        self.assertEqual(data['cost'], 2000)
        self.assertEqual(data['income'], 100)
        self.assertIsNotNone(data['image_url'])
        self.assertTrue(data['image_url'].endswith('test_character.png'))
        self.assertIsInstance(data['errors'], list)
    
    def test_extract_infobox_data_missing_elements(self):
        """Test infobox data extraction with missing elements."""
        # Mock HTML with incomplete infobox
        html = """
        <table class="infobox">
            <tr>
                <td>Some other field</td>
                <td>Some value</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        data = self.extractor._extract_infobox_data(soup)
        
        self.assertEqual(data['cost'], 0)
        self.assertEqual(data['income'], 0)
        self.assertIsNone(data['image_url'])
        self.assertTrue(len(data['errors']) > 0)
    
    @patch('card_generator.character_data_extractor.requests.Session.head')
    def test_find_character_page_success(self, mock_head):
        """Test successful character page discovery."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://stealabrainrot.fandom.com/wiki/Test_Character"
        mock_head.return_value = mock_response
        
        # Mock rate limiter to avoid delays in tests
        self.extractor.rate_limiter.wait = Mock()
        
        url = self.extractor._find_character_page("Test Character")
        
        self.assertIsNotNone(url)
        self.assertEqual(url, "https://stealabrainrot.fandom.com/wiki/Test_Character")
        
        # Should be cached
        cached_url = self.extractor._find_character_page("Test Character")
        self.assertEqual(cached_url, url)
    
    @patch('card_generator.character_data_extractor.requests.Session.head')
    def test_find_character_page_not_found(self, mock_head):
        """Test character page discovery when page doesn't exist."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        # Mock rate limiter and search fallback
        self.extractor.rate_limiter.wait = Mock()
        self.extractor._search_character_fallback = Mock(return_value=None)
        
        url = self.extractor._find_character_page("Nonexistent Character")
        
        self.assertIsNone(url)
        self.extractor._search_character_fallback.assert_called_once()
    
    @patch('card_generator.character_data_extractor.CharacterDataExtractor._fetch_page_with_retry')
    @patch('card_generator.character_data_extractor.CharacterDataExtractor._find_character_page')
    def test_extract_character_data_success(self, mock_find_page, mock_fetch_page):
        """Test successful character data extraction."""
        # Mock successful page discovery
        mock_find_page.return_value = "https://stealabrainrot.fandom.com/wiki/Test_Character"
        
        # Mock HTML response with complete data
        html = """
        <html>
            <body>
                <table class="infobox">
                    <tr>
                        <td colspan="2">
                            <figure class="pi-item pi-image">
                                <img src="/images/test_character.png" alt="Test Character">
                            </figure>
                        </td>
                    </tr>
                    <tr>
                        <td>Cost</td>
                        <td>1,500</td>
                    </tr>
                    <tr>
                        <td>Income per second</td>
                        <td>75</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mock_soup = BeautifulSoup(html, 'html.parser')
        mock_fetch_page.return_value = mock_soup
        
        character_data = self.extractor.extract_character_data("Test Character", "Common")
        
        self.assertIsNotNone(character_data)
        self.assertIsInstance(character_data, CharacterData)
        self.assertEqual(character_data.name, "Test Character")
        self.assertEqual(character_data.tier, "Common")
        self.assertEqual(character_data.cost, 1500)
        self.assertEqual(character_data.income, 75)
        self.assertEqual(character_data.variant, "Standard")
        self.assertTrue(character_data.extraction_success)
        self.assertIsNotNone(character_data.wiki_url)
        self.assertIsNotNone(character_data.image_url)
        self.assertIsNotNone(character_data.extraction_timestamp)
    
    @patch('card_generator.character_data_extractor.CharacterDataExtractor._find_character_page')
    def test_extract_character_data_page_not_found(self, mock_find_page):
        """Test character data extraction when page is not found."""
        # Mock page not found
        mock_find_page.return_value = None
        
        character_data = self.extractor.extract_character_data("Nonexistent Character", "Common")
        
        self.assertIsNone(character_data)
    
    @patch('card_generator.character_data_extractor.CharacterDataExtractor._fetch_page_with_retry')
    @patch('card_generator.character_data_extractor.CharacterDataExtractor._find_character_page')
    def test_extract_character_data_fetch_failure(self, mock_find_page, mock_fetch_page):
        """Test character data extraction when page fetch fails."""
        # Mock successful page discovery but failed fetch
        mock_find_page.return_value = "https://stealabrainrot.fandom.com/wiki/Test_Character"
        mock_fetch_page.return_value = None
        
        character_data = self.extractor.extract_character_data("Test Character", "Common")
        
        self.assertIsNone(character_data)
    
    @patch('card_generator.character_data_extractor.CharacterDataExtractor._fetch_page_with_retry')
    @patch('card_generator.character_data_extractor.CharacterDataExtractor._find_character_page')
    def test_extract_character_data_with_errors(self, mock_find_page, mock_fetch_page):
        """Test character data extraction with parsing errors."""
        # Mock successful page discovery
        mock_find_page.return_value = "https://stealabrainrot.fandom.com/wiki/Test_Character"
        
        # Mock HTML response with incomplete data
        html = """
        <html>
            <body>
                <div>No infobox here</div>
            </body>
        </html>
        """
        mock_soup = BeautifulSoup(html, 'html.parser')
        mock_fetch_page.return_value = mock_soup
        
        character_data = self.extractor.extract_character_data("Test Character", "Common")
        
        self.assertIsNotNone(character_data)
        self.assertEqual(character_data.name, "Test Character")
        self.assertEqual(character_data.tier, "Common")
        self.assertEqual(character_data.cost, 0)  # Default values due to parsing failure
        self.assertEqual(character_data.income, 0)
        self.assertTrue(character_data.extraction_success)  # Still successful extraction, just with missing data
        self.assertTrue(len(character_data.extraction_errors) > 0)


if __name__ == '__main__':
    unittest.main()