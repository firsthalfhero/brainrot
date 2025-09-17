"""
Image processing module for the Trading Card Generator.

This module handles loading, resizing, cropping, and validation of character images,
as well as generating placeholder images for missing characters.
"""

import os
from typing import Tuple, Optional, Union
from PIL import Image, ImageDraw, ImageFont
import logging

from .config import TIER_COLORS, CardConfig
from .error_handling import ErrorHandler, ErrorCategory, ErrorSeverity


class ImageProcessor:
    """
    Handles all image processing operations for trading card generation.
    
    This class provides methods for loading character images, resizing and cropping
    them to fit card layouts, validating image quality, and generating placeholder
    images for missing characters with tier-appropriate colors.
    """
    
    def __init__(self, card_config: Optional[CardConfig] = None):
        """
        Initialize the ImageProcessor.
        
        Args:
            card_config: Configuration for card dimensions and layout.
                        If None, uses default CardConfig.
        """
        self.config = card_config or CardConfig()
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(__name__)
        
        # Calculate target image dimensions based on card config
        self.target_image_size = (
            self.config.width - (2 * self.config.scaled_margin),
            self.config.image_height - (2 * self.config.scaled_margin)
        )
        
        # Minimum quality standards
        self.min_width = 200
        self.min_height = 200
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
    
    def load_image(self, image_path: str) -> Optional[Image.Image]:
        """
        Load an image from the specified path with validation.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            PIL Image object if successful, None if failed
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image format is not supported
        """
        if not os.path.exists(image_path):
            self.logger.error(f"Image file not found: {image_path}")
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Check file extension
        _, ext = os.path.splitext(image_path.lower())
        if ext not in self.supported_formats:
            self.logger.error(f"Unsupported image format: {ext}")
            raise ValueError(f"Unsupported image format: {ext}")
        
        try:
            # Check file size to avoid loading extremely large files
            file_size = os.path.getsize(image_path)
            max_file_size = 50 * 1024 * 1024  # 50MB limit
            if file_size > max_file_size:
                self.logger.warning(f"Image file too large ({file_size / 1024 / 1024:.1f}MB): {image_path}")
                return None
            
            image = Image.open(image_path)
            
            # Verify image is not corrupted by accessing basic properties
            _ = image.size
            _ = image.mode
            
            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if image.mode != 'RGB':
                try:
                    image = image.convert('RGB')
                except Exception as e:
                    self.logger.error(f"Failed to convert image to RGB {image_path}: {e}")
                    return None
            
            # Validate minimum quality standards
            if not self._validate_image_quality(image):
                self.logger.warning(f"Image quality below minimum standards: {image_path}")
                return None
            
            self.logger.info(f"Successfully loaded image: {image_path} ({image.size})")
            return image
            
        except FileNotFoundError:
            self.logger.error(f"Image file not found: {image_path}")
            raise
        except PermissionError:
            self.logger.error(f"Permission denied accessing image: {image_path}")
            return None
        except OSError as e:
            self.logger.error(f"OS error loading image {image_path}: {e}")
            return None
        except Image.UnidentifiedImageError:
            self.logger.error(f"Corrupted or invalid image format: {image_path}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error loading image {image_path}: {str(e)}")
            return None
    
    def resize_and_crop(self, image: Image.Image, target_size: Optional[Tuple[int, int]] = None) -> Image.Image:
        """
        Resize image using height-based scaling while maintaining aspect ratio.
        
        This method scales images to fit the target height without cropping,
        allowing for horizontal white space if the image is narrower than the target width.
        This prevents cropping of portrait images and maintains their full content.
        
        Args:
            image: PIL Image object to process
            target_size: Target dimensions (width, height). If None, uses default card image size.
            
        Returns:
            Processed PIL Image object
        """
        if target_size is None:
            target_size = self.target_image_size
        
        target_width, target_height = target_size
        original_width, original_height = image.size
        
        # Calculate new dimensions based on height scaling
        aspect_ratio = original_width / original_height
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
        
        # If the calculated width exceeds target width, scale down proportionally
        if new_width > target_width:
            scale_factor = target_width / new_width
            new_width = target_width
            new_height = int(target_height * scale_factor)
        
        # Resize image using height-based scaling
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        self.logger.debug(f"Resized image from {image.size} to {resized_image.size} using height-based scaling")
        return resized_image
    
    def create_placeholder(self, character_name: str, tier: str, 
                          size: Optional[Tuple[int, int]] = None) -> Image.Image:
        """
        Create a placeholder image for missing character images.
        
        The placeholder uses tier-appropriate colors and displays the character name.
        
        Args:
            character_name: Name of the character
            tier: Character tier for color selection
            size: Image dimensions. If None, uses default card image size.
            
        Returns:
            PIL Image object with placeholder design
        """
        if size is None:
            size = self.target_image_size
        
        width, height = size
        
        # Get tier color, default to gray if tier not found
        tier_color = TIER_COLORS.get(tier, TIER_COLORS['Common'])
        
        # Create image with tier-colored background
        image = Image.new('RGB', size, tier_color)
        draw = ImageDraw.Draw(image)
        
        # Add darker border
        border_color = self._darken_color(tier_color, 0.3)
        border_width = max(2, width // 100)
        draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=border_width)
        
        # Add "NO IMAGE" text
        try:
            # Try to use a system font
            font_size = min(width, height) // 8
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            # Fall back to default font
            font = ImageFont.load_default()
        
        # Draw "NO IMAGE" text
        no_image_text = "NO IMAGE"
        bbox = draw.textbbox((0, 0), no_image_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (width - text_width) // 2
        text_y = height // 3
        
        # Add text shadow
        shadow_offset = 2
        draw.text((text_x + shadow_offset, text_y + shadow_offset), no_image_text, 
                 fill='black', font=font)
        draw.text((text_x, text_y), no_image_text, fill='white', font=font)
        
        # Draw character name
        name_font_size = min(width, height) // 12
        try:
            name_font = ImageFont.truetype("arial.ttf", name_font_size)
        except (OSError, IOError):
            name_font = ImageFont.load_default()
        
        # Wrap long names
        wrapped_name = self._wrap_text(character_name, name_font, width - 20)
        
        name_y = text_y + text_height + 20
        for line in wrapped_name:
            bbox = draw.textbbox((0, 0), line, font=name_font)
            line_width = bbox[2] - bbox[0]
            line_x = (width - line_width) // 2
            
            # Add text shadow
            draw.text((line_x + 1, name_y + 1), line, fill='black', font=name_font)
            draw.text((line_x, name_y), line, fill='white', font=name_font)
            
            name_y += bbox[3] - bbox[1] + 5
        
        self.logger.info(f"Created placeholder image for {character_name} ({tier})")
        return image
    
    def _validate_image_quality(self, image: Image.Image) -> bool:
        """
        Validate that image meets minimum quality standards.
        
        Args:
            image: PIL Image object to validate
            
        Returns:
            True if image meets standards, False otherwise
        """
        width, height = image.size
        
        # Check minimum dimensions
        if width < self.min_width or height < self.min_height:
            self.logger.warning(f"Image too small: {width}x{height} (minimum: {self.min_width}x{self.min_height})")
            return False
        
        # Check aspect ratio isn't too extreme
        aspect_ratio = width / height
        if aspect_ratio < 0.2 or aspect_ratio > 5.0:
            self.logger.warning(f"Extreme aspect ratio: {aspect_ratio}")
            return False
        
        return True
    
    def _darken_color(self, hex_color: str, factor: float) -> str:
        """
        Darken a hex color by the specified factor.
        
        Args:
            hex_color: Hex color string (e.g., '#FF0000')
            factor: Darkening factor (0.0 = no change, 1.0 = black)
            
        Returns:
            Darkened hex color string
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Darken
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> list:
        """
        Wrap text to fit within specified width.
        
        Args:
            text: Text to wrap
            font: Font to use for measurement
            max_width: Maximum width in pixels
            
        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines