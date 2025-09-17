"""
Card layout and design engine for generating trading cards.
"""

import logging
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

from .config import CardConfig, TIER_COLORS
from .data_models import CharacterData


logger = logging.getLogger(__name__)


class CardDesigner:
    """
    Handles the creation of individual trading card layouts with character images,
    names, stats, and tier-based styling.
    """
    
    def __init__(self, config: Optional[CardConfig] = None):
        """
        Initialize the CardDesigner with configuration.
        
        Args:
            config: Card configuration settings. Uses default if None.
        """
        self.config = config or CardConfig()
        self._font_cache = {}
        
    def create_card(self, character: CharacterData, image: Optional[Image.Image] = None) -> Image.Image:
        """
        Create a complete trading card for a character with new top-to-bottom layout:
        title, image, rarity, income, cost.
        
        Args:
            character: Character data to display on the card
            image: Character image. If None, creates a placeholder.
            
        Returns:
            PIL Image of the complete trading card
        """
        # Create base card (no border as per requirements)
        card = Image.new('RGB', (self.config.width, self.config.height), self.config.background_color)
        draw = ImageDraw.Draw(card)
        
        # Calculate layout positions for new top-to-bottom design
        current_y = self.config.scaled_margin
        
        # 1. Character name (title) - large bold font, center aligned, 60% width constraint
        current_y = self._render_character_name_new_layout(draw, character.name, current_y)
        current_y += self.config.scaled_inner_margin
        
        # 2. Character image - center aligned, height-based scaling maintained
        image_area_height = int(self.config.height * 0.4)  # Allocate 40% of card height for image
        if image:
            processed_image = self._prepare_character_image(image, image_area_height)
        else:
            processed_image = self._create_placeholder_image(character, image_area_height)
            
        # Center the image horizontally
        image_x = (self.config.width - processed_image.width) // 2
        card.paste(processed_image, (image_x, current_y))
        current_y += processed_image.height + self.config.scaled_inner_margin
        
        # 3. Tier/Rarity - Heading 3 equivalent, center aligned, large font
        current_y = self._render_tier_display(draw, character.tier, current_y)
        current_y += self.config.scaled_inner_margin
        
        # 4. Income per second - Heading 5 bold, center aligned, formatted as "1 / sec" or "1b / sec"
        current_y = self._render_income_display(draw, character.income, current_y)
        current_y += self.config.scaled_inner_margin // 2
        
        # 5. Cost - Heading 5 bold, center aligned, formatted as "$100k" or "$1b"
        self._render_cost_display(draw, character.cost, current_y)
        
        return card
    

    
    def _prepare_character_image(self, image: Image.Image, target_height: int) -> Image.Image:
        """
        Resize character image to fit the card layout using height-based scaling.
        
        This method scales images to 100% of the available height while maintaining
        aspect ratio, preventing cropping of portrait images. Images are centered
        horizontally with acceptable white space on the sides if needed.
        
        Args:
            image: Original character image
            target_height: Height for the image area (100% height scaling)
            
        Returns:
            Processed image ready for card placement
        """
        # Calculate target width maintaining aspect ratio based on height
        aspect_ratio = image.width / image.height
        target_width = int(target_height * aspect_ratio)
        
        # Check if the calculated width exceeds card boundaries
        max_width = self.config.width - (2 * self.config.scaled_margin)
        if target_width > max_width:
            # If image would be too wide, scale down proportionally
            # This maintains aspect ratio while fitting within card bounds
            scale_factor = max_width / target_width
            target_width = max_width
            target_height = int(target_height * scale_factor)
        
        # Resize image using height-based scaling approach
        resized_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        return resized_image
    
    def _create_placeholder_image(self, character: CharacterData, target_height: int) -> Image.Image:
        """
        Create a placeholder image when character image is not available.
        
        Args:
            character: Character data for placeholder styling
            target_height: Height for the placeholder
            
        Returns:
            Placeholder image with tier-appropriate styling
        """
        placeholder_width = self.config.width - (2 * self.config.scaled_margin)
        placeholder_height = min(target_height, placeholder_width)  # Keep it square-ish
        
        # Create placeholder with tier color
        tier_color = TIER_COLORS.get(character.tier, '#CCCCCC')
        placeholder = Image.new('RGB', (placeholder_width, placeholder_height), tier_color)
        draw = ImageDraw.Draw(placeholder)
        
        # Add character name to placeholder
        try:
            font = self._get_font(36)
            
            # Calculate text position (centered)
            bbox = draw.textbbox((0, 0), character.name, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = (placeholder_width - text_width) // 2
            text_y = (placeholder_height - text_height) // 2
            
            # Draw text with contrasting color
            text_color = '#FFFFFF' if tier_color != '#FFD700' else '#000000'  # White text except on gold
            draw.text((text_x, text_y), character.name, fill=text_color, font=font)
            
        except Exception as e:
            logger.warning(f"Could not add text to placeholder for {character.name}: {e}")
        
        return placeholder
    
    def _render_character_name_new_layout(self, draw: ImageDraw.Draw, name: str, y_position: int) -> int:
        """
        Render character name with new layout: large bold font (Heading 1 equivalent),
        center aligned, 60% width constraint.
        
        Args:
            draw: ImageDraw object for the card
            name: Character name to render
            y_position: Y position to start rendering
            
        Returns:
            Y position after the rendered name
        """
        # 60% width constraint for text area
        max_width = int(self.config.width * 0.6)
        
        # Use large font size (Heading 1 equivalent)
        font_size = int(self.config.scaled_title_font_size * 1.2)  # Make it larger for Heading 1
        font = self._get_font(font_size)
        
        # Check if name fits on one line within 60% width
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        if text_width <= max_width:
            # Single line - center it
            text_x = (self.config.width - text_width) // 2
            draw.text((text_x, y_position), name, fill=self.config.text_color, font=font)
            return y_position + text_height
        else:
            # Try smaller font sizes if needed
            for smaller_size in [font_size - 8, font_size - 16, font_size - 24]:
                if smaller_size < 20:
                    break
                font = self._get_font(smaller_size)
                bbox = draw.textbbox((0, 0), name, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                if text_width <= max_width:
                    text_x = (self.config.width - text_width) // 2
                    draw.text((text_x, y_position), name, fill=self.config.text_color, font=font)
                    return y_position + text_height
            
            # If still too long, wrap text within 60% width
            wrapped_lines = self._wrap_text(name, font, max_width, force=True)
            return self._draw_wrapped_text_centered(draw, wrapped_lines[:2], font, y_position)
    
    def _render_tier_display(self, draw: ImageDraw.Draw, tier: str, y_position: int) -> int:
        """
        Render tier/rarity display with Heading 3 equivalent font, center aligned.
        
        Args:
            draw: ImageDraw object for the card
            tier: Tier name to display
            y_position: Y position to start rendering
            
        Returns:
            Y position after the rendered tier
        """
        # Heading 3 equivalent font size
        font_size = int(self.config.scaled_title_font_size * 0.8)
        font = self._get_font(font_size)
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), tier, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center align
        text_x = (self.config.width - text_width) // 2
        
        # Use tier color for text
        tier_color = TIER_COLORS.get(tier, self.config.text_color)
        draw.text((text_x, y_position), tier, fill=tier_color, font=font)
        
        return y_position + text_height
    
    def _render_income_display(self, draw: ImageDraw.Draw, income: int, y_position: int) -> int:
        """
        Render income per second with Heading 5 bold font, center aligned,
        formatted as "1 / sec" or "1b / sec".
        
        Args:
            draw: ImageDraw object for the card
            income: Income value to display
            y_position: Y position to start rendering
            
        Returns:
            Y position after the rendered income
        """
        # Heading 5 equivalent font size
        font_size = int(self.config.scaled_stats_font_size * 0.9)
        font = self._get_font(font_size)
        
        # Format income with appropriate scaling
        income_text = self._format_income_value(income)
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), income_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center align
        text_x = (self.config.width - text_width) // 2
        draw.text((text_x, y_position), income_text, fill=self.config.text_color, font=font)
        
        return y_position + text_height
    
    def _render_cost_display(self, draw: ImageDraw.Draw, cost: int, y_position: int) -> int:
        """
        Render cost with Heading 5 bold font, center aligned,
        formatted as "$100k" or "$1b".
        
        Args:
            draw: ImageDraw object for the card
            cost: Cost value to display
            y_position: Y position to start rendering
            
        Returns:
            Y position after the rendered cost
        """
        # Heading 5 equivalent font size
        font_size = int(self.config.scaled_stats_font_size * 0.9)
        font = self._get_font(font_size)
        
        # Format cost with appropriate scaling
        cost_text = self._format_cost_value(cost)
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), cost_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center align
        text_x = (self.config.width - text_width) // 2
        draw.text((text_x, y_position), cost_text, fill=self.config.text_color, font=font)
        
        return y_position + text_height
    
    def _format_income_value(self, income: int) -> str:
        """
        Format income value with appropriate scaling (1 / sec, 1k / sec, 1b / sec).
        
        Args:
            income: Income value to format
            
        Returns:
            Formatted income string
        """
        if income >= 1_000_000_000:
            formatted = f"{income / 1_000_000_000:.1f}".rstrip('0').rstrip('.')
            return f"{formatted}b / sec"
        elif income >= 1_000_000:
            formatted = f"{income / 1_000_000:.1f}".rstrip('0').rstrip('.')
            return f"{formatted}m / sec"
        elif income >= 1_000:
            formatted = f"{income / 1_000:.1f}".rstrip('0').rstrip('.')
            return f"{formatted}k / sec"
        else:
            return f"{income} / sec"
    
    def _format_cost_value(self, cost: int) -> str:
        """
        Format cost value with appropriate scaling ($100k, $1b).
        
        Args:
            cost: Cost value to format
            
        Returns:
            Formatted cost string
        """
        if cost >= 1_000_000_000:
            formatted = f"{cost / 1_000_000_000:.1f}".rstrip('0').rstrip('.')
            return f"${formatted}b"
        elif cost >= 1_000_000:
            formatted = f"{cost / 1_000_000:.1f}".rstrip('0').rstrip('.')
            return f"${formatted}m"
        elif cost >= 1_000:
            formatted = f"{cost / 1_000:.1f}".rstrip('0').rstrip('.')
            return f"${formatted}k"
        else:
            return f"${cost}"
    
    def _draw_wrapped_text_centered(self, draw: ImageDraw.Draw, lines: list[str], font: FreeTypeFont, y_position: int) -> int:
        """
        Draw multiple lines of wrapped text with center alignment.
        
        Args:
            draw: ImageDraw object
            lines: List of text lines to draw
            font: Font to use
            y_position: Starting Y position
            
        Returns:
            Y position after all lines
        """
        current_y = y_position
        line_height = font.getbbox('Ay')[3] - font.getbbox('Ay')[1] + 5  # Add some line spacing
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (self.config.width - text_width) // 2
            
            draw.text((text_x, current_y), line, fill=self.config.text_color, font=font)
            current_y += line_height
        
        return current_y
    
    def _render_character_name(self, draw: ImageDraw.Draw, name: str, y_position: int) -> int:
        """
        Render character name with automatic sizing and wrapping.
        
        Args:
            draw: ImageDraw object for the card
            name: Character name to render
            y_position: Y position to start rendering
            
        Returns:
            Y position after the rendered name
        """
        max_width = self.config.width - (2 * self.config.scaled_margin)
        
        # Try different font sizes to fit the name
        for font_size in [self.config.scaled_title_font_size, 42, 36, 30, 24]:
            font = self._get_font(font_size)
            
            # Check if name fits on one line
            bbox = draw.textbbox((0, 0), name, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                # Single line - center it
                text_x = (self.config.width - text_width) // 2
                draw.text((text_x, y_position), name, fill=self.config.text_color, font=font)
                return y_position + (bbox[3] - bbox[1]) + 10
            
            # Try wrapping for smaller fonts
            if font_size <= 36:
                wrapped_lines = self._wrap_text(name, font, max_width)
                if len(wrapped_lines) <= 2:  # Max 2 lines
                    return self._draw_wrapped_text(draw, wrapped_lines, font, y_position)
        
        # Fallback: force wrap with smallest font
        font = self._get_font(24)
        wrapped_lines = self._wrap_text(name, font, max_width, force=True)
        return self._draw_wrapped_text(draw, wrapped_lines[:2], font, y_position)  # Max 2 lines
    
    def _wrap_text(self, text: str, font: FreeTypeFont, max_width: int, force: bool = False) -> list[str]:
        """
        Wrap text to fit within specified width.
        
        Args:
            text: Text to wrap
            font: Font to use for measurement
            max_width: Maximum width in pixels
            force: If True, force wrap even if it breaks words
            
        Returns:
            List of wrapped text lines
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word too long
                    if force:
                        # Break the word
                        for i in range(len(word), 0, -1):
                            partial = word[:i]
                            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), partial, font=font)
                            if bbox[2] - bbox[0] <= max_width:
                                lines.append(partial)
                                current_line = [word[i:]] if i < len(word) else []
                                break
                    else:
                        current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _draw_wrapped_text(self, draw: ImageDraw.Draw, lines: list[str], font: FreeTypeFont, y_position: int) -> int:
        """
        Draw multiple lines of wrapped text.
        
        Args:
            draw: ImageDraw object
            lines: List of text lines to draw
            font: Font to use
            y_position: Starting Y position
            
        Returns:
            Y position after all lines
        """
        current_y = y_position
        line_height = font.getbbox('Ay')[3] - font.getbbox('Ay')[1] + 5  # Add some line spacing
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (self.config.width - text_width) // 2
            
            draw.text((text_x, current_y), line, fill=self.config.text_color, font=font)
            current_y += line_height
        
        return current_y + 10  # Extra spacing after name
    

    
    def _get_font(self, size: int) -> FreeTypeFont:
        """
        Get font with caching. Falls back to default font if custom font not available.
        
        Args:
            size: Font size in pixels
            
        Returns:
            Font object
        """
        if size in self._font_cache:
            return self._font_cache[size]
        
        try:
            # Try to load a system font
            font = ImageFont.truetype("arial.ttf", size)
        except (OSError, IOError):
            try:
                # Try alternative system fonts
                for font_name in ["Arial.ttf", "arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]:
                    try:
                        font = ImageFont.truetype(font_name, size)
                        break
                    except (OSError, IOError):
                        continue
                else:
                    # Fall back to default font
                    font = ImageFont.load_default()
                    logger.warning(f"Could not load system font, using default font for size {size}")
            except Exception as e:
                font = ImageFont.load_default()
                logger.warning(f"Font loading failed, using default: {e}")
        
        self._font_cache[size] = font
        return font