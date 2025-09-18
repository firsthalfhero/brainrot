"""
Character data extractor module for extracting detailed information from individual brainrot character pages.

This module provides the CharacterDataExtractor class that handles fetching and parsing
individual character pages to extract detailed information including cost, income, and image URLs.
"""

import requests
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote, unquote
import logging
from datetime import datetime

from .data_models import CharacterData
from .error_handling import ErrorHandler, ErrorCategory, ErrorSeverity
from .wiki_scraper import RateLimiter


class CharacterDataExtractor:
    """
    Extractor for detailed character data from individual wiki pages.
    
    Handles character page discovery, infobox parsing, and data extraction
    with fallback mechanisms for missing or differently structured pages.
    """
    
    def __init__(self, base_url: str = "https://stealabrainrot.fandom.com"):
        """
        Initialize the CharacterDataExtractor.
        
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
        
        # Cache for successful page URLs to avoid repeated discovery
        self._url_cache: Dict[str, str] = {}
    
    def extract_character_data(self, character_name: str, tier: str) -> Optional[CharacterData]:
        """
        Extract complete character data from individual page.
        
        Args:
            character_name: Name of the character to extract data for
            tier: Tier/rarity of the character
            
        Returns:
            CharacterData object if successful, None otherwise
        """
        try:
            logging.info(f"Extracting data for character: {character_name} ({tier})")
            
            # Find the character page URL
            page_url = self._find_character_page(character_name)
            if not page_url:
                logging.warning(f"Could not find page for character: {character_name}")
                return None
            
            # Fetch and parse the character page
            soup = self._fetch_page_with_retry(page_url)
            if not soup:
                logging.error(f"Failed to fetch character page: {page_url}")
                return None
            
            # Extract infobox data
            infobox_data = self._extract_infobox_data(soup)
            
            # Create character data object
            character_data = CharacterData(
                name=character_name,
                tier=tier,
                cost=infobox_data.get('cost', 0),
                income=infobox_data.get('income', 0),
                variant="Standard",  # Default variant for scraped characters
                image_path=None  # Will be set after image download
            )
            
            # Add additional fields for database building
            character_data.wiki_url = page_url
            character_data.image_url = infobox_data.get('image_url')
            character_data.extraction_timestamp = datetime.now()
            character_data.extraction_success = True
            character_data.extraction_errors = infobox_data.get('errors', [])
            
            logging.info(f"Successfully extracted data for {character_name}: Cost={character_data.cost}, Income={character_data.income}")
            
            return character_data
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CHARACTER_EXTRACTION,
                ErrorSeverity.MEDIUM,
                context={'character_name': character_name, 'tier': tier}
            )
            
            # Return partial data object with error information
            try:
                character_data = CharacterData(
                    name=character_name,
                    tier=tier,
                    cost=0,
                    income=0,
                    variant="Standard"
                )
                character_data.extraction_timestamp = datetime.now()
                character_data.extraction_success = False
                character_data.extraction_errors = [str(e)]
                return character_data
            except:
                return None
    
    def _find_character_page(self, character_name: str) -> Optional[str]:
        """
        Find the correct wiki page URL for a character.
        
        Tries multiple URL variations and fallback search methods.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Full URL to character page if found, None otherwise
        """
        # Check cache first
        if character_name in self._url_cache:
            return self._url_cache[character_name]
        
        # Generate possible URL variations
        url_variations = self._generate_url_variations(character_name)
        
        # Try each URL variation
        for url in url_variations:
            try:
                logging.debug(f"Trying URL: {url}")
                
                # Apply rate limiting
                self.rate_limiter.wait()
                
                response = self.session.head(url, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    final_url = response.url
                    logging.debug(f"Found character page: {final_url}")
                    
                    # Cache the successful URL
                    self._url_cache[character_name] = final_url
                    return final_url
                    
            except requests.exceptions.RequestException as e:
                logging.debug(f"URL {url} failed: {str(e)}")
                continue
            except Exception as e:
                logging.debug(f"Unexpected error checking URL {url}: {str(e)}")
                continue
        
        # If direct URLs fail, try search fallback
        search_url = self._search_character_fallback(character_name)
        if search_url:
            self._url_cache[character_name] = search_url
            return search_url
        
        logging.warning(f"Could not find any valid URL for character: {character_name}")
        return None
    
    def _generate_url_variations(self, character_name: str) -> List[str]:
        """
        Generate possible URL variations for a character name.
        
        Args:
            character_name: Name of the character
            
        Returns:
            List of possible URLs to try
        """
        variations = []
        
        # Clean the character name for URL encoding
        clean_name = character_name.strip()
        
        # Variation 1: Direct name with spaces as underscores
        url_name = clean_name.replace(' ', '_')
        variations.append(urljoin(self.base_url, f"/wiki/{quote(url_name)}"))
        
        # Variation 2: Direct name with spaces as %20
        variations.append(urljoin(self.base_url, f"/wiki/{quote(clean_name)}"))
        
        # Variation 3: Remove special characters and try again
        clean_alphanumeric = re.sub(r'[^a-zA-Z0-9\s]', '', clean_name)
        if clean_alphanumeric != clean_name:
            url_name = clean_alphanumeric.replace(' ', '_')
            variations.append(urljoin(self.base_url, f"/wiki/{quote(url_name)}"))
        
        # Variation 4: Try with "Character:" prefix (some wikis use this)
        variations.append(urljoin(self.base_url, f"/wiki/Character:{quote(url_name)}"))
        
        # Variation 5: Try with first letter capitalized
        if clean_name and not clean_name[0].isupper():
            capitalized = clean_name[0].upper() + clean_name[1:]
            url_name = capitalized.replace(' ', '_')
            variations.append(urljoin(self.base_url, f"/wiki/{quote(url_name)}"))
        
        # Variation 6: Try all lowercase
        if clean_name != clean_name.lower():
            lowercase = clean_name.lower()
            url_name = lowercase.replace(' ', '_')
            variations.append(urljoin(self.base_url, f"/wiki/{quote(url_name)}"))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for url in variations:
            if url not in seen:
                seen.add(url)
                unique_variations.append(url)
        
        return unique_variations
    
    def _search_character_fallback(self, character_name: str) -> Optional[str]:
        """
        Implement fallback search functionality when direct pages don't exist.
        
        Uses the wiki's search functionality to find character pages.
        
        Args:
            character_name: Name of the character to search for
            
        Returns:
            URL to character page if found via search, None otherwise
        """
        try:
            # Construct search URL
            search_query = quote(character_name)
            search_url = urljoin(self.base_url, f"/wiki/Special:Search?query={search_query}")
            
            logging.debug(f"Trying search fallback: {search_url}")
            
            # Apply rate limiting
            self.rate_limiter.wait()
            
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for search results
            search_results = soup.find_all('a', href=True)
            
            for link in search_results:
                href = link.get('href', '')
                link_text = link.get_text().strip()
                
                # Check if this looks like a character page
                if (href.startswith('/wiki/') and 
                    character_name.lower() in link_text.lower() and
                    not any(skip in href.lower() for skip in [
                        'category:', 'file:', 'template:', 'help:', 'special:',
                        'user:', 'talk:', 'search'
                    ])):
                    
                    full_url = urljoin(self.base_url, href)
                    logging.debug(f"Found character via search: {full_url}")
                    return full_url
            
            logging.debug(f"No character page found via search for: {character_name}")
            return None
            
        except Exception as e:
            logging.debug(f"Search fallback failed for {character_name}: {str(e)}")
            return None
    
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
    
    def _extract_infobox_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract cost, income, and image from character infobox.
        
        Args:
            soup: BeautifulSoup object of the character page
            
        Returns:
            Dictionary containing extracted data and any errors
        """
        data = {
            'cost': 0,
            'income': 0,
            'image_url': None,
            'errors': []
        }
        
        try:
            # Find the infobox - try multiple selectors
            infobox = None
            infobox_selectors = [
                'table.infobox',
                'div.infobox',
                'table.wikitable.infobox',
                'aside.portable-infobox',
                'div.portable-infobox'
            ]
            
            for selector in infobox_selectors:
                infobox = soup.select_one(selector)
                if infobox:
                    logging.debug(f"Found infobox using selector: {selector}")
                    break
            
            if not infobox:
                # Try to find any table or div that might contain character info
                possible_infoboxes = soup.find_all(['table', 'div'], class_=re.compile(r'info|character|stats', re.I))
                if possible_infoboxes:
                    infobox = possible_infoboxes[0]
                    logging.debug("Found potential infobox via fallback search")
            
            if not infobox:
                data['errors'].append("No infobox found on character page")
                logging.warning("No infobox found on character page")
                return data
            
            # Extract image URL
            image_url = self._extract_image_url(infobox, soup)
            if image_url:
                data['image_url'] = image_url
            else:
                data['errors'].append("No character image found")
            
            # Extract cost and income from infobox
            cost = self._extract_numeric_field(infobox, ['cost', 'price', 'buy'])
            if cost is not None:
                data['cost'] = cost
            else:
                data['errors'].append("Cost not found or could not be parsed")
            
            income = self._extract_numeric_field(infobox, ['income', 'earn', 'profit', 'per second', 'per_second'])
            if income is not None:
                data['income'] = income
            else:
                data['errors'].append("Income not found or could not be parsed")
            
            logging.debug(f"Extracted infobox data: cost={data['cost']}, income={data['income']}, image_url={bool(data['image_url'])}")
            
        except Exception as e:
            error_msg = f"Error extracting infobox data: {str(e)}"
            data['errors'].append(error_msg)
            logging.error(error_msg)
        
        return data
    
    def _extract_image_url(self, infobox: BeautifulSoup, full_soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the main character image URL from infobox or page.
        
        Args:
            infobox: BeautifulSoup object of the infobox
            full_soup: BeautifulSoup object of the full page
            
        Returns:
            Full URL to character image if found, None otherwise
        """
        try:
            # Try to find image in infobox first
            image_selectors = [
                'figure.pi-item.pi-image img',
                'div.pi-image img',
                'img.pi-image-thumbnail',
                'td img',
                'div.image img',
                'figure img',
                'img'
            ]
            
            for selector in image_selectors:
                img_element = infobox.select_one(selector)
                if img_element:
                    src = img_element.get('src') or img_element.get('data-src')
                    if src:
                        # Convert relative URLs to absolute
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        
                        # Filter out icon/UI images
                        if not any(skip in src.lower() for skip in ['icon', 'ui', 'button', 'arrow', 'edit']):
                            logging.debug(f"Found character image: {src}")
                            return src
            
            # If no image in infobox, try the full page
            page_images = full_soup.find_all('img')
            for img in page_images:
                src = img.get('src') or img.get('data-src')
                alt = img.get('alt', '').lower()
                
                if (src and 
                    not any(skip in src.lower() for skip in ['icon', 'ui', 'button', 'arrow', 'edit', 'logo']) and
                    any(indicator in alt for indicator in ['character', 'brainrot', 'image'])):
                    
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    
                    logging.debug(f"Found character image on page: {src}")
                    return src
            
            logging.debug("No character image found")
            return None
            
        except Exception as e:
            logging.error(f"Error extracting image URL: {str(e)}")
            return None
    
    def _extract_numeric_field(self, infobox: BeautifulSoup, field_names: List[str]) -> Optional[int]:
        """
        Extract a numeric field from the infobox.
        
        Args:
            infobox: BeautifulSoup object of the infobox
            field_names: List of possible field names to look for
            
        Returns:
            Extracted integer value if found, None otherwise
        """
        try:
            # Look for table rows or data elements
            rows = infobox.find_all(['tr', 'div', 'dt', 'dd'])
            
            for row in rows:
                row_text = row.get_text().lower()
                
                # Check if this row contains one of our target fields
                for field_name in field_names:
                    if field_name.lower() in row_text:
                        # Extract numeric value from this row
                        value = self._parse_numeric_value(row.get_text())
                        if value is not None:
                            logging.debug(f"Found {field_name}: {value}")
                            return value
            
            # Alternative approach: look for specific data attributes or classes
            for field_name in field_names:
                elements = infobox.find_all(attrs={'data-source': re.compile(field_name, re.I)})
                for element in elements:
                    value = self._parse_numeric_value(element.get_text())
                    if value is not None:
                        logging.debug(f"Found {field_name} via data-source: {value}")
                        return value
            
            return None
            
        except Exception as e:
            logging.error(f"Error extracting numeric field {field_names}: {str(e)}")
            return None
    
    def _parse_numeric_value(self, text: str) -> Optional[int]:
        """
        Parse a numeric value from text, handling various formats.
        
        Args:
            text: Text containing numeric value
            
        Returns:
            Parsed integer value if found, None otherwise
        """
        try:
            # Clean the text
            clean_text = text.strip()
            
            # Remove common prefixes/suffixes
            clean_text = re.sub(r'[^\d.,k]', ' ', clean_text, flags=re.I)
            
            # Find numeric patterns
            patterns = [
                r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*k',  # Numbers with 'k' suffix (thousands)
                r'(\d+(?:,\d{3})*(?:\.\d+)?)',      # Regular numbers with commas
                r'(\d+\.?\d*)',                     # Simple decimal numbers
                r'(\d+)'                            # Simple integers
            ]
            
            for pattern in patterns:
                match = re.search(pattern, clean_text, re.I)
                if match:
                    value_str = match.group(1).replace(',', '')
                    
                    # Handle 'k' suffix (thousands)
                    if 'k' in clean_text.lower():
                        value = float(value_str) * 1000
                    else:
                        value = float(value_str)
                    
                    # Convert to integer
                    return int(value)
            
            return None
            
        except (ValueError, AttributeError) as e:
            logging.debug(f"Could not parse numeric value from '{text}': {str(e)}")
            return None
    
    def close(self):
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()
            logging.debug("CharacterDataExtractor session closed")