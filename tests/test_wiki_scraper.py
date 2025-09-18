"""
Unit tests for the WikiScraper class.

Tests the wiki scraping functionality with mock HTML responses.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup

from card_generator.wiki_scraper import WikiScraper, RateLimiter


class TestRateLimiter(unittest.TestCase):
    """Test the RateLimiter class."""
    
    def setUp(self):
        self.rate_limiter = RateLimiter(base_delay=1.0)
    
    def test_initial_delay(self):
        """Test initial delay values."""
        self.assertEqual(self.rate_limiter.base_delay, 1.0)
        self.assertEqual(self.rate_limiter.current_delay, 1.0)
    
    def test_increase_delay(self):
        """Test delay increase functionality."""
        initial_delay = self.rate_limiter.current_delay
        self.rate_limiter.increase_delay()
        self.assertGreater(self.rate_limiter.current_delay, initial_delay)
    
    def test_reset_delay(self):
        """Test delay reset functionality."""
        self.rate_limiter.increase_delay()
        self.rate_limiter.reset_delay()
        self.assertEqual(self.rate_limiter.current_delay, self.rate_limiter.base_delay)
    
    @patch('time.sleep')
    def test_wait(self, mock_sleep):
        """Test wait functionality."""
        self.rate_limiter.wait()
        mock_sleep.assert_called_once_with(self.rate_limiter.current_delay)


class TestWikiScraper(unittest.TestCase):
    """Test the WikiScraper class."""
    
    def setUp(self):
        self.scraper = WikiScraper()
    
    def tearDown(self):
        self.scraper.close()
    
    def test_initialization(self):
        """Test WikiScraper initialization."""
        self.assertEqual(self.scraper.base_url, "https://stealabrainrot.fandom.com")
        self.assertIsNotNone(self.scraper.session)
        self.assertIsNotNone(self.scraper.rate_limiter)
        self.assertIsNotNone(self.scraper.error_handler)
    
    def test_session_headers(self):
        """Test that session has appropriate headers."""
        headers = self.scraper.session.headers
        self.assertIn('User-Agent', headers)
        self.assertIn('Accept', headers)
        self.assertIn('Accept-Language', headers)
    
    @patch('requests.Session.get')
    def test_fetch_page_with_retry_success(self, mock_get):
        """Test successful page fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>Test content</body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.scraper._fetch_page_with_retry('http://test.com')
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, BeautifulSoup)
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_fetch_page_with_retry_rate_limit(self, mock_get):
        """Test handling of rate limiting."""
        # Mock rate limited response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        result = self.scraper._fetch_page_with_retry('http://test.com', max_retries=1)
        
        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, 2)  # Initial + 1 retry
    
    @patch('requests.Session.get')
    def test_fetch_page_with_retry_timeout(self, mock_get):
        """Test handling of timeout errors."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = self.scraper._fetch_page_with_retry('http://test.com', max_retries=1)
        
        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, 2)  # Initial + 1 retry
    
    def test_parse_tier_section_with_links(self):
        """Test parsing tier section with character links."""
        # Create mock HTML with character links
        html_content = '''
        <div class="tabber wds-tabber">
            <div class="wds-tab__content">
                <h3>Common</h3>
                <ul>
                    <li><a href="/wiki/Character1">Character1</a></li>
                    <li><a href="/wiki/Character2">Character2</a></li>
                    <li><a href="/wiki/Category:Something">Category Link</a></li>
                </ul>
            </div>
        </div>
        '''
        
        soup = BeautifulSoup(html_content, 'html.parser')
        tabber_section = soup.find('div', class_='tabber wds-tabber')
        
        characters = self.scraper._parse_tier_section(tabber_section, 'Common')
        
        # Should extract character names but filter out category links
        self.assertIn('Character1', characters)
        self.assertIn('Character2', characters)
        self.assertNotIn('Category Link', characters)
    
    def test_parse_tier_section_empty(self):
        """Test parsing empty tier section."""
        html_content = '<div class="tabber wds-tabber"></div>'
        soup = BeautifulSoup(html_content, 'html.parser')
        tabber_section = soup.find('div', class_='tabber wds-tabber')
        
        characters = self.scraper._parse_tier_section(tabber_section, 'Common')
        
        self.assertEqual(len(characters), 0)
    
    @patch.object(WikiScraper, '_fetch_page_with_retry')
    @patch.object(WikiScraper, '_parse_tier_section')
    def test_scrape_brainrots_page_success(self, mock_parse_tier, mock_fetch):
        """Test successful scraping of brainrots page."""
        # Mock successful page fetch
        mock_html = '''
        <html>
            <body>
                <div class="tabber wds-tabber">
                    <div class="wds-tab__content">Test content</div>
                </div>
            </body>
        </html>
        '''
        mock_soup = BeautifulSoup(mock_html, 'html.parser')
        mock_fetch.return_value = mock_soup
        
        # Mock tier parsing to return characters
        mock_parse_tier.return_value = ['Character1', 'Character2']
        
        result = self.scraper.scrape_brainrots_page()
        
        # Should return dictionary with tier data
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        mock_fetch.assert_called_once()
    
    @patch.object(WikiScraper, '_fetch_page_with_retry')
    def test_scrape_brainrots_page_no_tabber(self, mock_fetch):
        """Test handling of page without tabber section."""
        # Mock page without tabber section
        mock_html = '<html><body><div>No tabber here</div></body></html>'
        mock_soup = BeautifulSoup(mock_html, 'html.parser')
        mock_fetch.return_value = mock_soup
        
        with self.assertRaises(Exception) as context:
            self.scraper.scrape_brainrots_page()
        
        self.assertIn('tabber section', str(context.exception))
    
    @patch.object(WikiScraper, '_fetch_page_with_retry')
    def test_scrape_brainrots_page_fetch_failure(self, mock_fetch):
        """Test handling of page fetch failure."""
        mock_fetch.return_value = None
        
        with self.assertRaises(Exception) as context:
            self.scraper.scrape_brainrots_page()
        
        self.assertIn('Failed to fetch', str(context.exception))
    
    def test_close(self):
        """Test session cleanup."""
        # Create a mock session to verify close is called
        mock_session = Mock()
        self.scraper.session = mock_session
        
        self.scraper.close()
        
        mock_session.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()