"""
Image downloader module for the Database Builder.

This module provides a class-based wrapper around the existing image download
functionality, integrating it with the database builder system while maintaining
compatibility with the existing image processing pipeline.
"""

import os
import re
import time
import requests
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import logging

from .config import DatabaseBuilderConfig
from .error_handling import ErrorHandler, ErrorCategory, ErrorSeverity
from .image_processor import ImageProcessor


class ImageDownloader:
    """
    Handles character image downloading for the database builder.
    
    This class wraps the existing image download functionality from download_images.py
    and integrates it with the database builder system, providing proper error handling,
    validation, and integration with existing image processing components.
    """
    
    def __init__(self, config: Optional[DatabaseBuilderConfig] = None):
        """
        Initialize the ImageDownloader.
        
        Args:
            config: Database builder configuration. If None, uses default config.
        """
        self.config = config or DatabaseBuilderConfig()
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(__name__)
        self.image_processor = ImageProcessor()
        
        # Set up requests session with proper headers
        self.session = requests.Session()
        self.session.headers.update(self.config.request_headers)
        
        # Ensure images directory exists
        os.makedirs(self.config.images_dir, exist_ok=True)
        
        # Image validation settings
        self.min_width = 150
        self.min_height = 150
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    def download_character_image(self, character_name: str, image_url: str) -> Optional[str]:
        """
        Download and save a character image.
        
        Args:
            character_name: Name of the character
            image_url: URL of the image to download
            
        Returns:
            Local file path if successful, None if failed
        """
        try:
            # Check if image already exists and skip if configured to do so
            if self.config.skip_existing_images:
                existing_path = self._find_existing_image(character_name)
                if existing_path:
                    self.logger.info(f"Skipping {character_name} - image already exists: {existing_path}")
                    return existing_path
            
            # Clean and validate the image URL
            clean_url = self._get_original_image_url(image_url)
            if not clean_url:
                self.logger.warning(f"Invalid image URL for {character_name}: {image_url}")
                return None
            
            self.logger.info(f"Downloading image for {character_name}: {clean_url}")
            
            # Download the image with retries
            image_data = self._download_with_retries(clean_url)
            if not image_data:
                return None
            
            # Validate the image
            if self.config.validate_images:
                if not self._validate_image_data(image_data, character_name):
                    return None
            
            # Generate file path and save
            file_path = self._generate_image_path(character_name, clean_url)
            if not file_path:
                return None
            
            # Save the image
            try:
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                
                self.logger.info(f"Successfully downloaded image for {character_name}: {file_path}")
                return file_path
                
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.IMAGE_DOWNLOAD, ErrorSeverity.MEDIUM,
                    context={'character': character_name, 'file_path': file_path}
                )
                return None
        
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.IMAGE_DOWNLOAD, ErrorSeverity.MEDIUM,
                context={'character': character_name, 'image_url': image_url}
            )
            return None
    
    def _find_existing_image(self, character_name: str) -> Optional[str]:
        """
        Find existing image file for a character.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Path to existing image file, or None if not found
        """
        clean_name = self._clean_filename(character_name)
        
        try:
            for filename in os.listdir(self.config.images_dir):
                if filename.lower().startswith(clean_name.lower()):
                    # Check if it has a valid image extension
                    _, ext = os.path.splitext(filename.lower())
                    if ext in self.supported_extensions:
                        full_path = os.path.join(self.config.images_dir, filename)
                        if os.path.isfile(full_path):
                            return full_path
        except OSError as e:
            self.logger.warning(f"Error checking for existing images: {e}")
        
        return None
    
    def _get_original_image_url(self, img_src: str) -> Optional[str]:
        """
        Convert scaled/thumbnail image URLs to original full-size URLs.
        
        This method replicates the logic from download_images.py to ensure
        we get the highest quality images available.
        
        Args:
            img_src: Original image source URL
            
        Returns:
            Cleaned URL for original image, or None if invalid
        """
        if not img_src:
            return None
        
        try:
            # Remove scaling parameters
            if 'scale-to-width-down' in img_src:
                img_src = re.sub(r'/scale-to-width-down/\d+', '', img_src)
            if 'scale-to-height-down' in img_src:
                img_src = re.sub(r'/scale-to-height-down/\d+', '', img_src)
            
            # Clean revision URLs
            if '/revision/latest/' in img_src:
                parts = img_src.split('/revision/latest/')
                if len(parts) == 2:
                    base = parts[0]
                    remainder = parts[1]
                    if '?' in remainder:
                        callback = remainder.split('?cb=')[-1] if '?cb=' in remainder else None
                        if callback:
                            img_src = f"{base}/revision/latest?cb={callback}"
                        else:
                            img_src = f"{base}/revision/latest"
                    else:
                        # Remove trailing slash if no query params
                        img_src = f"{base}/revision/latest"
            
            # Ensure absolute URL
            if img_src.startswith('//'):
                img_src = 'https:' + img_src
            elif img_src.startswith('/'):
                img_src = urljoin(self.config.base_url, img_src)
            
            # Validate URL format
            if not img_src.startswith(('http://', 'https://')):
                return None
            
            # Check for valid image extension
            if not any(ext in img_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return None
            
            return img_src
            
        except Exception as e:
            self.logger.warning(f"Error cleaning image URL {img_src}: {e}")
            return None
    
    def _download_with_retries(self, url: str) -> Optional[bytes]:
        """
        Download image data with retry logic.
        
        Args:
            url: Image URL to download
            
        Returns:
            Image data as bytes, or None if failed
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Apply rate limiting
                if attempt > 0:
                    delay = self.config.get_retry_delay(attempt - 1)
                    self.logger.info(f"Retrying download after {delay:.1f}s delay (attempt {attempt + 1}/{self.config.max_retries})")
                    time.sleep(delay)
                else:
                    time.sleep(self.config.rate_limit_delay)
                
                # Make the request
                response = self.session.get(url, timeout=self.config.timeout)
                response.raise_for_status()
                
                # Check content length
                content_length = len(response.content)
                if content_length > self.max_file_size:
                    self.logger.warning(f"Image too large: {content_length / 1024 / 1024:.1f}MB")
                    return None
                
                if content_length == 0:
                    self.logger.warning("Empty image response")
                    continue
                
                return response.content
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                self.logger.warning(f"Download timeout (attempt {attempt + 1}/{self.config.max_retries}): {url}")
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                self.logger.warning(f"Connection error (attempt {attempt + 1}/{self.config.max_retries}): {e}")
                
            except requests.exceptions.HTTPError as e:
                last_exception = e
                if e.response.status_code == 429:  # Rate limited
                    self.logger.warning(f"Rate limited (attempt {attempt + 1}/{self.config.max_retries})")
                    # Increase delay for rate limiting
                    time.sleep(self.config.rate_limit_delay * 2)
                elif e.response.status_code in (404, 403):
                    # Don't retry for client errors
                    self.logger.warning(f"Image not accessible ({e.response.status_code}): {url}")
                    break
                else:
                    self.logger.warning(f"HTTP error {e.response.status_code} (attempt {attempt + 1}/{self.config.max_retries})")
                    
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Unexpected error (attempt {attempt + 1}/{self.config.max_retries}): {e}")
        
        # Log final failure
        if last_exception:
            self.error_handler.handle_error(
                last_exception, ErrorCategory.IMAGE_DOWNLOAD, ErrorSeverity.MEDIUM,
                context={'url': url, 'attempts': self.config.max_retries}
            )
        
        return None
    
    def _validate_image_data(self, image_data: bytes, character_name: str) -> bool:
        """
        Validate downloaded image data.
        
        Args:
            image_data: Raw image data
            character_name: Character name for logging
            
        Returns:
            True if image is valid, False otherwise
        """
        try:
            # Try to open and validate the image
            image = Image.open(BytesIO(image_data))
            width, height = image.size
            
            # Check minimum dimensions
            if width < self.min_width or height < self.min_height:
                self.logger.warning(f"Image too small for {character_name}: {width}x{height}")
                return False
            
            # Check aspect ratio
            aspect_ratio = width / height
            if aspect_ratio > 3.0 or aspect_ratio < 0.33:
                self.logger.warning(f"Unusual aspect ratio for {character_name}: {aspect_ratio:.2f}")
                return False
            
            # Verify image is not corrupted by accessing properties
            _ = image.mode
            _ = image.format
            
            self.logger.debug(f"Valid image for {character_name}: {width}x{height}, format: {image.format}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Invalid image data for {character_name}: {e}")
            return False
    
    def _generate_image_path(self, character_name: str, image_url: str) -> Optional[str]:
        """
        Generate local file path for character image.
        
        Args:
            character_name: Name of the character
            image_url: Original image URL
            
        Returns:
            Local file path, or None if generation failed
        """
        try:
            # Clean character name for filename
            clean_name = self._clean_filename(character_name)
            
            # Determine file extension from URL or content type
            extension = self._determine_file_extension(image_url)
            if not extension:
                extension = '.png'  # Default fallback
            
            # Generate filename
            filename = f"{clean_name}{extension}"
            file_path = os.path.join(self.config.images_dir, filename)
            
            return file_path
            
        except Exception as e:
            self.logger.warning(f"Error generating image path for {character_name}: {e}")
            return None
    
    def _clean_filename(self, filename: str) -> str:
        """
        Clean filename to be filesystem-safe.
        
        This method replicates the logic from download_images.py.
        
        Args:
            filename: Original filename
            
        Returns:
            Cleaned filename safe for filesystem
        """
        return re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    def _determine_file_extension(self, image_url: str) -> Optional[str]:
        """
        Determine appropriate file extension from image URL.
        
        Args:
            image_url: Image URL
            
        Returns:
            File extension including dot, or None if undetermined
        """
        url_lower = image_url.lower()
        
        if '.png' in url_lower:
            return '.png'
        elif '.jpg' in url_lower or '.jpeg' in url_lower:
            return '.jpg'
        elif '.gif' in url_lower:
            return '.gif'
        elif '.webp' in url_lower:
            return '.webp'
        
        return None
    
    def get_image_path(self, character_name: str) -> Optional[str]:
        """
        Get the expected local path for a character's image.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Expected local image path, or None if not found
        """
        return self._find_existing_image(character_name)
    
    def validate_image_file(self, file_path: str) -> bool:
        """
        Validate an existing image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if image is valid, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            # Use the existing image processor for validation
            image = self.image_processor.load_image(file_path)
            return image is not None
            
        except Exception as e:
            self.logger.warning(f"Error validating image file {file_path}: {e}")
            return False
    
    def cleanup_invalid_images(self) -> List[str]:
        """
        Clean up invalid or corrupted image files.
        
        Returns:
            List of removed file paths
        """
        removed_files = []
        
        try:
            for filename in os.listdir(self.config.images_dir):
                file_path = os.path.join(self.config.images_dir, filename)
                
                # Skip directories
                if not os.path.isfile(file_path):
                    continue
                
                # Check if it's an image file
                _, ext = os.path.splitext(filename.lower())
                if ext not in self.supported_extensions:
                    continue
                
                # Validate the image
                if not self.validate_image_file(file_path):
                    try:
                        os.remove(file_path)
                        removed_files.append(file_path)
                        self.logger.info(f"Removed invalid image: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove invalid image {file_path}: {e}")
        
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.FILE_SYSTEM, ErrorSeverity.MEDIUM,
                context={'images_dir': self.config.images_dir}
            )
        
        return removed_files
    
    def get_download_stats(self) -> Dict[str, Any]:
        """
        Get statistics about downloaded images.
        
        Returns:
            Dictionary with download statistics
        """
        stats = {
            'total_images': 0,
            'valid_images': 0,
            'invalid_images': 0,
            'total_size_mb': 0.0,
            'supported_formats': {},
            'images_dir': self.config.images_dir
        }
        
        try:
            for filename in os.listdir(self.config.images_dir):
                file_path = os.path.join(self.config.images_dir, filename)
                
                # Skip directories
                if not os.path.isfile(file_path):
                    continue
                
                # Check if it's an image file
                _, ext = os.path.splitext(filename.lower())
                if ext not in self.supported_extensions:
                    continue
                
                stats['total_images'] += 1
                
                # Get file size
                try:
                    file_size = os.path.getsize(file_path)
                    stats['total_size_mb'] += file_size / (1024 * 1024)
                except:
                    pass
                
                # Count format
                stats['supported_formats'][ext] = stats['supported_formats'].get(ext, 0) + 1
                
                # Validate image
                if self.validate_image_file(file_path):
                    stats['valid_images'] += 1
                else:
                    stats['invalid_images'] += 1
        
        except Exception as e:
            self.logger.warning(f"Error collecting download stats: {e}")
        
        return stats