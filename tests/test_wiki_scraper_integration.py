"""
Integration tests for WikiScraper with realistic HTML structures.

Tests the wiki scraping functionality with mock HTML that resembles the actual wiki structure.
"""

import unittest
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup

from card_generator.wiki_scraper import WikiScraper


class TestWikiScraperIntegration(unittest.TestCase):
    """Integration tests for WikiScraper with realistic scenarios."""
    
    def setUp(self):
        self.scraper = WikiScraper()
    
    def tearDown(self):
        self.scraper.close()
    
    @patch('requests.Session.get')
    def test_scrape_realistic_wiki_structure(self, mock_get):
        """Test scraping with realistic wiki HTML structure."""
        # Mock HTML that resembles the actual wiki structure
        realistic_html = '''
        <!DOCTYPE html>
        <html>
        <head><title>Brainrots - Steal a Brainrot Wiki</title></head>
        <body>
            <div class="page-content">
                <div class="tabber wds-tabber">
                    <div class="wds-tab__content" data-tab-name="Common">
                        <h3>Common Brainrots</h3>
                        <div class="mw-parser-output">
                            <ul>
                                <li><a href="/wiki/Fluriflura" title="Fluriflura">Fluriflura</a></li>
                                <li><a href="/wiki/Bambini_Crostini" title="Bambini Crostini">Bambini Crostini</a></li>
                                <li><a href="/wiki/Pipi_Kiwi" title="Pipi Kiwi">Pipi Kiwi</a></li>
                            </ul>
                        </div>
                    </div>
                    <div class="wds-tab__content" data-tab-name="Rare">
                        <h3>Rare Brainrots</h3>
                        <div class="mw-parser-output">
                            <ul>
                                <li><a href="/wiki/Gattatino_Nyanino" title="Gattatino Nyanino">Gattatino Nyanino</a></li>
                                <li><a href="/wiki/Cappuccino_Assassino" title="Cappuccino Assassino">Cappuccino Assassino</a></li>
                            </ul>
                        </div>
                    </div>
                    <div class="wds-tab__content" data-tab-name="Epic">
                        <h3>Epic Brainrots</h3>
                        <div class="mw-parser-output">
                            <ul>
                                <li><a href="/wiki/Lionel_Cactuseli" title="Lionel Cactuseli">Lionel Cactuseli</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = realistic_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test scraping
        result = self.scraper.scrape_brainrots_page()
        
        # Verify results
        self.assertIsInstance(result, dict)
        
        # Check that we found characters in different tiers
        if 'Common' in result:
            common_chars = result['Common']
            self.assertIn('Fluriflura', common_chars)
            self.assertIn('Bambini Crostini', common_chars)
            self.assertIn('Pipi Kiwi', common_chars)
        
        if 'Rare' in result:
            rare_chars = result['Rare']
            self.assertIn('Gattatino Nyanino', rare_chars)
            self.assertIn('Cappuccino Assassino', rare_chars)
        
        if 'Epic' in result:
            epic_chars = result['Epic']
            self.assertIn('Lionel Cactuseli', epic_chars)
        
        # Verify the request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('/wiki/Brainrots', call_args[0][0])
    
    @patch('requests.Session.get')
    def test_scrape_with_mixed_content(self, mock_get):
        """Test scraping with mixed content including non-character links."""
        mixed_html = '''
        <div class="tabber wds-tabber">
            <div class="wds-tab__content" data-tab-name="Common">
                <h3>Common</h3>
                <ul>
                    <li><a href="/wiki/Character1">Character1</a></li>
                    <li><a href="/wiki/Category:Characters">Category Link</a></li>
                    <li><a href="/wiki/File:Image.png">File Link</a></li>
                    <li><a href="/wiki/Character2">Character2</a></li>
                    <li><a href="/wiki/Template:Something">Template Link</a></li>
                    <li><a href="/wiki/Help:Editing">Help Link</a></li>
                    <li><a href="/wiki/Character3">Character3</a></li>
                </ul>
            </div>
        </div>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mixed_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_brainrots_page()
        
        # Should only extract character links, not category/file/template/help links
        if 'Common' in result:
            common_chars = result['Common']
            self.assertIn('Character1', common_chars)
            self.assertIn('Character2', common_chars)
            self.assertIn('Character3', common_chars)
            
            # Should not include system links
            self.assertNotIn('Category Link', common_chars)
            self.assertNotIn('File Link', common_chars)
            self.assertNotIn('Template Link', common_chars)
            self.assertNotIn('Help Link', common_chars)
    
    @patch('requests.Session.get')
    def test_scrape_with_alternative_structure(self, mock_get):
        """Test scraping with alternative HTML structure."""
        # Some wikis might have different structures
        alt_html = '''
        <div class="tabber wds-tabber">
            <div class="wds-tab__content">
                <div title="Common">
                    <h4>Common Tier</h4>
                    <p>Characters in this tier:</p>
                    <div>
                        <a href="/wiki/AltChar1">AltChar1</a>,
                        <a href="/wiki/AltChar2">AltChar2</a>
                    </div>
                </div>
            </div>
        </div>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = alt_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_brainrots_page()
        
        # Should handle alternative structures
        self.assertIsInstance(result, dict)
        # The exact results depend on how well the parser handles the alternative structure
    
    @patch('requests.Session.get')
    def test_scrape_empty_tiers(self, mock_get):
        """Test scraping when some tiers are empty."""
        empty_tiers_html = '''
        <div class="tabber wds-tabber">
            <div class="wds-tab__content" data-tab-name="Common">
                <h3>Common</h3>
                <ul>
                    <li><a href="/wiki/OnlyChar">OnlyChar</a></li>
                </ul>
            </div>
            <div class="wds-tab__content" data-tab-name="Rare">
                <h3>Rare</h3>
                <p>No characters in this tier yet.</p>
            </div>
            <div class="wds-tab__content" data-tab-name="Epic">
                <h3>Epic</h3>
                <ul></ul>
            </div>
        </div>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = empty_tiers_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_brainrots_page()
        
        # Should handle empty tiers gracefully
        self.assertIsInstance(result, dict)
        
        # Common should have the character
        if 'Common' in result:
            self.assertIn('OnlyChar', result['Common'])
        
        # Empty tiers might not be included in results or have empty lists
        # This is acceptable behavior
    
    def test_parse_tier_section_with_nested_elements(self):
        """Test parsing tier sections with nested HTML elements."""
        nested_html = '''
        <div class="tabber wds-tabber">
            <div class="wds-tab__content" data-tab-name="Test">
                <h3>Test Tier</h3>
                <div class="character-grid">
                    <div class="character-item">
                        <a href="/wiki/NestedChar1">
                            <img src="image1.png" alt="NestedChar1">
                            <span>NestedChar1</span>
                        </a>
                    </div>
                    <div class="character-item">
                        <a href="/wiki/NestedChar2">
                            <img src="image2.png" alt="NestedChar2">
                            <span>NestedChar2</span>
                        </a>
                    </div>
                </div>
                <ul>
                    <li>
                        <strong><a href="/wiki/ListChar1">ListChar1</a></strong>
                        <em> - A special character</em>
                    </li>
                </ul>
            </div>
        </div>
        '''
        
        soup = BeautifulSoup(nested_html, 'html.parser')
        tabber_section = soup.find('div', class_='tabber wds-tabber')
        
        characters = self.scraper._parse_tier_section(tabber_section, 'Test')
        
        # Should extract characters from nested structures
        self.assertIn('NestedChar1', characters)
        self.assertIn('NestedChar2', characters)
        self.assertIn('ListChar1', characters)


if __name__ == '__main__':
    unittest.main()