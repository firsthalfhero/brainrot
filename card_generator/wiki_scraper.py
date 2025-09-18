"""
Wiki scraper module for extracting brainrot character data from the Steal a Brainrot wiki.

This module provides the WikiScraper class that handles fetching and parsing the main
brainrots page to extract character names organized by tier.
"""

import requests
import time
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from dataclasses import dataclass

from .error_handling import ErrorHandler, ErrorCategory, ErrorSeverity


@dataclass
class RateLimiter:
    """Rate limiter for respectful web scraping."""
    base_delay: float = 2.0
    current_delay: float = None
    max_delay: float = 30.0
    backoff_factor: float = 1.5
    
    def __post_init__(self):
        """Initialize current_delay to base_delay if not set."""
        if self.current_delay is None:
            self.current_delay = self.base_delay
    
    def wait(self):
        """Wait for the current delay period."""
        time.sleep(self.current_delay)
    
    def increase_delay(self):
        """Increase delay due to rate limiting detection."""
        self.current_delay = min(self.current_delay * self.backoff_factor, self.max_delay)
        logging.warning(f"Rate limiting detected, increasing delay to {self.current_delay}s")
    
    def reset_delay(self):
        """Reset delay to base value after successful requests."""
        if self.current_delay > self.base_delay:
            self.current_delay = self.base_delay
            logging.info("Delay reset to base value")


class WikiScraper:
    """
    Scraper for the Steal a Brainrot wiki main page.
    
    Handles fetching and parsing the main brainrots page to extract character names
    organized by tier sections.
    """
    
    def __init__(self, base_url: str = "https://stealabrainrot.fandom.com"):
        """
        Initialize the WikiScraper.
        
        Args:
            base_url: Base URL for the wiki
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.rate_limiter = RateLimiter()
        self.error_handler = ErrorHandler(__name__)
        
        # Set up session headers for respectful scraping
        self.session.headers.update({
            'User-Agent': 'Brainrot Database Builder Research Tool 1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Tier mappings based on wiki structure
        self.tier_headings = {
            'Common': 'Common',
            'Rare': 'Rare',
            'Epic': 'Epic', 
            'Legendary': 'Legendary',
            'Mythic': 'Mythic',
            'Brainrot God': 'Brainrot God',
            'Secret': 'Secret',
            'OG': 'OG'
        }
    
    def scrape_brainrots_page(self) -> Dict[str, List[str]]:
        """
        Scrape the main brainrots page and extract character names by tier.
        
        Returns:
            Dictionary mapping tier names to lists of character names
            
        Raises:
            Exception: If the page cannot be fetched or parsed
        """
        url = urljoin(self.base_url, "/wiki/Brainrots")
        
        try:
            logging.info(f"Fetching main brainrots page: {url}")
            
            # Fetch the page with retry logic
            soup = self._fetch_page_with_retry(url)
            if not soup:
                raise Exception("Failed to fetch main brainrots page after retries")
            
            # Find the tabber section
            tabber_section = soup.find('div', class_='tabber wds-tabber')
            if not tabber_section:
                raise Exception("Could not find tabber section with class 'tabber wds-tabber'")
            
            logging.info("Found tabber section, extracting tier data")
            
            # Extract character names from each tier tab
            tier_data = {}
            for tier_name in self.tier_headings.keys():
                try:
                    characters = self._parse_tier_section(tabber_section, tier_name)
                    if characters:
                        tier_data[tier_name] = characters
                        logging.info(f"Found {len(characters)} characters in {tier_name} tier")
                    else:
                        logging.warning(f"No characters found in {tier_name} tier")
                except Exception as e:
                    self.error_handler.handle_error(
                        e, ErrorCategory.WIKI_SCRAPING, 
                        ErrorSeverity.MEDIUM,
                        context={'tier': tier_name}
                    )
                    continue
            
            if not tier_data:
                raise Exception("No character data extracted from any tier")
            
            total_characters = sum(len(chars) for chars in tier_data.values())
            logging.info(f"Successfully extracted {total_characters} characters across {len(tier_data)} tiers")
            
            return tier_data
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.WIKI_SCRAPING,
                ErrorSeverity.HIGH,
                context={'url': url}
            )
            raise
    
    def _fetch_page_with_retry(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch a page with retry logic and rate limiting.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            
        Returns:
            BeautifulSoup object if successful, None otherwise
        """
        for attempt in range(max_retries + 1):
            try:
                # Apply rate limiting
                if attempt > 0:
                    self.rate_limiter.wait()
                
                logging.debug(f"Fetching {url} (attempt {attempt + 1}/{max_retries + 1})")
                
                response = self.session.get(url, timeout=30)
                
                # Check for rate limiting indicators
                if response.status_code == 429:
                    self.rate_limiter.increase_delay()
                    if attempt < max_retries:
                        logging.warning(f"Rate limited (429), retrying in {self.rate_limiter.current_delay}s")
                        continue
                    else:
                        logging.error("Rate limited and max retries exceeded")
                        return None
                
                # Check for successful response
                response.raise_for_status()
                
                # Reset delay on successful request
                self.rate_limiter.reset_delay()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup
                
            except requests.exceptions.Timeout:
                logging.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
                if attempt < max_retries:
                    self.rate_limiter.wait()
                    continue
                else:
                    logging.error(f"Max retries exceeded for {url}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request error fetching {url}: {str(e)} (attempt {attempt + 1})")
                if attempt < max_retries:
                    self.rate_limiter.wait()
                    continue
                else:
                    logging.error(f"Max retries exceeded for {url}")
                    return None
                    
            except Exception as e:
                logging.error(f"Unexpected error fetching {url}: {str(e)}")
                return None
        
        return None
    
    def _parse_tier_section(self, tabber_section: BeautifulSoup, tier_name: str) -> List[str]:
        """
        Parse character names from a specific tier section.
        
        Args:
            tabber_section: BeautifulSoup object containing the tabber
            tier_name: Name of the tier to parse
            
        Returns:
            List of character names found in the tier
        """
        characters = []
        
        try:
            # Find the tab panel for this tier
            # Look for data-tab-name attribute or similar
            tab_panel = None
            
            # Try multiple approaches to find the tier section
            possible_selectors = [
                f'[data-tab-name="{tier_name}"]',
                f'[data-tab="{tier_name}"]',
                f'div[title="{tier_name}"]'
            ]
            
            for selector in possible_selectors:
                tab_panel = tabber_section.select_one(selector)
                if tab_panel:
                    break
            
            # If direct selection fails, look for text content
            if not tab_panel:
                # Find all tab panels and check their content
                tab_panels = tabber_section.find_all('div', class_='wds-tab__content')
                for panel in tab_panels:
                    # Look for tier heading in the panel
                    headings = panel.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    for heading in headings:
                        if tier_name.lower() in heading.get_text().lower():
                            tab_panel = panel
                            break
                    if tab_panel:
                        break
            
            if not tab_panel:
                logging.warning(f"Could not find tab panel for tier: {tier_name}")
                return characters
            
            # Extract character names from the panel
            # Look for links that might be character pages
            links = tab_panel.find_all('a')
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # Filter out navigation links and keep character links
                if (text and 
                    '/wiki/' in href and 
                    not any(skip in href.lower() for skip in [
                        'category:', 'file:', 'template:', 'help:', 'special:',
                        'user:', 'talk:', 'brainrots', 'main_page'
                    ])):
                    
                    # Clean up character name
                    character_name = text.strip()
                    if character_name and character_name not in characters:
                        characters.append(character_name)
            
            # Also look for list items that might contain character names
            list_items = tab_panel.find_all('li')
            for item in list_items:
                text = item.get_text().strip()
                # Look for character links within list items
                item_links = item.find_all('a')
                for link in item_links:
                    href = link.get('href', '')
                    link_text = link.get_text().strip()
                    
                    if (link_text and 
                        '/wiki/' in href and 
                        not any(skip in href.lower() for skip in [
                            'category:', 'file:', 'template:', 'help:', 'special:',
                            'user:', 'talk:', 'brainrots', 'main_page'
                        ])):
                        
                        character_name = link_text.strip()
                        if character_name and character_name not in characters:
                            characters.append(character_name)
            
            logging.debug(f"Extracted {len(characters)} characters from {tier_name}: {characters}")
            
        except Exception as e:
            logging.error(f"Error parsing tier section {tier_name}: {str(e)}")
            
        return characters
    
    def close(self):
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()
            logging.debug("WikiScraper session closed")