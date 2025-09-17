"""
Print layout management for arranging trading cards on printable sheets.
"""

import logging
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw

from .config import PrintConfig, CardConfig


logger = logging.getLogger(__name__)


class PrintLayoutManager:
    """
    Handles the arrangement of trading cards on A4 print sheets with proper
    margins, spacing, and cutting guides for efficient printing.
    """
    
    def __init__(self, print_config: Optional[PrintConfig] = None, card_config: Optional[CardConfig] = None):
        """
        Initialize the PrintLayoutManager with configuration.
        
        Args:
            print_config: Print layout configuration. Uses default if None.
            card_config: Card configuration for validation. Uses default if None.
        """
        self.print_config = print_config or PrintConfig()
        self.card_config = card_config or CardConfig()
        
        # Validate that cards will fit on the sheet
        self._validate_layout()
    
    def create_print_sheet(self, cards: List[Image.Image]) -> Image.Image:
        """
        Create a print sheet with up to 2 cards arranged for A4 landscape printing.
        
        Args:
            cards: List of card images to arrange (max 2 cards per sheet)
            
        Returns:
            PIL Image of the complete print sheet with cards and cutting guides
            
        Raises:
            ValueError: If more than 2 cards are provided or cards are wrong size
        """
        if len(cards) > self.print_config.cards_per_sheet:
            raise ValueError(f"Too many cards provided. Maximum {self.print_config.cards_per_sheet} cards per sheet.")
        
        if not cards:
            raise ValueError("No cards provided for print sheet.")
        
        # Validate card dimensions
        for i, card in enumerate(cards):
            if card.size != (self.card_config.width, self.card_config.height):
                raise ValueError(f"Card {i} has incorrect dimensions: {card.size}. Expected: ({self.card_config.width}, {self.card_config.height})")
        
        # Create blank print sheet
        sheet = Image.new('RGB', (self.print_config.sheet_width, self.print_config.sheet_height), '#FFFFFF')
        
        # Calculate card positions
        card_positions = self._calculate_card_positions(len(cards))
        
        # Place cards on sheet
        for card, position in zip(cards, card_positions):
            sheet.paste(card, position)
        
        # Add cutting guides if enabled
        if self.print_config.show_cut_guides:
            self._add_cutting_guides(sheet, card_positions, len(cards))
        
        return sheet
    
    def arrange_cards_for_printing(self, cards: List[Image.Image]) -> List[Image.Image]:
        """
        Arrange multiple cards into print sheets, creating as many sheets as needed.
        
        Args:
            cards: List of all card images to arrange
            
        Returns:
            List of print sheet images, each containing up to 2 cards
        """
        if not cards:
            return []
        
        print_sheets = []
        
        # Process cards in batches of cards_per_sheet
        for i in range(0, len(cards), self.print_config.cards_per_sheet):
            batch = cards[i:i + self.print_config.cards_per_sheet]
            sheet = self.create_print_sheet(batch)
            print_sheets.append(sheet)
        
        logger.info(f"Created {len(print_sheets)} print sheets for {len(cards)} cards")
        return print_sheets
    
    def _validate_layout(self) -> None:
        """
        Validate that the card dimensions will fit properly on the print sheet
        with the configured margins and spacing.
        
        Raises:
            ValueError: If cards won't fit with current configuration
        """
        # Calculate required space for 2 cards side by side
        total_card_width = (self.card_config.width * 2) + self.print_config.scaled_card_spacing
        total_margins = self.print_config.scaled_sheet_margin * 2
        required_width = total_card_width + total_margins
        
        if required_width > self.print_config.sheet_width:
            raise ValueError(
                f"Cards won't fit on sheet width. Required: {required_width}px, "
                f"Available: {self.print_config.sheet_width}px"
            )
        
        # Check height
        required_height = self.card_config.height + total_margins
        if required_height > self.print_config.sheet_height:
            raise ValueError(
                f"Cards won't fit on sheet height. Required: {required_height}px, "
                f"Available: {self.print_config.sheet_height}px"
            )
        
        logger.debug("Print layout validation passed")
    
    def _calculate_card_positions(self, num_cards: int) -> List[Tuple[int, int]]:
        """
        Calculate the positions for cards on the print sheet.
        
        Args:
            num_cards: Number of cards to position (1 or 2)
            
        Returns:
            List of (x, y) positions for each card
        """
        positions = []
        
        # Calculate available space for cards
        available_width = self.print_config.sheet_width - (2 * self.print_config.scaled_sheet_margin)
        available_height = self.print_config.sheet_height - (2 * self.print_config.scaled_sheet_margin)
        
        if num_cards == 1:
            # Center single card on sheet
            x = (self.print_config.sheet_width - self.card_config.width) // 2
            y = (self.print_config.sheet_height - self.card_config.height) // 2
            positions.append((x, y))
            
        elif num_cards == 2:
            # Arrange 2 cards side by side with spacing
            total_card_width = (self.card_config.width * 2) + self.print_config.scaled_card_spacing
            start_x = (self.print_config.sheet_width - total_card_width) // 2
            y = (self.print_config.sheet_height - self.card_config.height) // 2
            
            # First card
            positions.append((start_x, y))
            
            # Second card
            second_x = start_x + self.card_config.width + self.print_config.scaled_card_spacing
            positions.append((second_x, y))
        
        return positions
    
    def _add_cutting_guides(self, sheet: Image.Image, card_positions: List[Tuple[int, int]], num_cards: int) -> None:
        """
        Add cutting guides around cards for precise cutting.
        
        Args:
            sheet: Print sheet image to add guides to
            card_positions: List of card positions on the sheet
            num_cards: Number of cards on the sheet
        """
        draw = ImageDraw.Draw(sheet)
        
        for x, y in card_positions:
            # Calculate card boundaries
            card_left = x
            card_right = x + self.card_config.width
            card_top = y
            card_bottom = y + self.card_config.height
            
            # Draw corner cutting guides
            self._draw_corner_guides(draw, card_left, card_right, card_top, card_bottom)
            
            # Draw edge guides for shared edges (between cards)
            if num_cards == 2:
                # Add guides on the shared edge between cards
                self._draw_shared_edge_guides(draw, card_positions)
    
    def _draw_corner_guides(self, draw: ImageDraw.Draw, left: int, right: int, top: int, bottom: int) -> None:
        """
        Draw cutting guides at the corners of a card.
        
        Args:
            draw: ImageDraw object for the sheet
            left, right, top, bottom: Card boundaries
        """
        guide_length = self.print_config.scaled_cut_guide_length
        guide_width = self.print_config.scaled_cut_guide_width
        guide_color = self.print_config.cut_guide_color
        
        # Top-left corner
        # Horizontal line
        draw.rectangle(
            [left - guide_length, top - guide_width//2, left, top + guide_width//2],
            fill=guide_color
        )
        # Vertical line
        draw.rectangle(
            [left - guide_width//2, top - guide_length, left + guide_width//2, top],
            fill=guide_color
        )
        
        # Top-right corner
        # Horizontal line
        draw.rectangle(
            [right, top - guide_width//2, right + guide_length, top + guide_width//2],
            fill=guide_color
        )
        # Vertical line
        draw.rectangle(
            [right - guide_width//2, top - guide_length, right + guide_width//2, top],
            fill=guide_color
        )
        
        # Bottom-left corner
        # Horizontal line
        draw.rectangle(
            [left - guide_length, bottom - guide_width//2, left, bottom + guide_width//2],
            fill=guide_color
        )
        # Vertical line
        draw.rectangle(
            [left - guide_width//2, bottom, left + guide_width//2, bottom + guide_length],
            fill=guide_color
        )
        
        # Bottom-right corner
        # Horizontal line
        draw.rectangle(
            [right, bottom - guide_width//2, right + guide_length, bottom + guide_width//2],
            fill=guide_color
        )
        # Vertical line
        draw.rectangle(
            [right - guide_width//2, bottom, right + guide_width//2, bottom + guide_length],
            fill=guide_color
        )
    
    def _draw_shared_edge_guides(self, draw: ImageDraw.Draw, card_positions: List[Tuple[int, int]]) -> None:
        """
        Draw cutting guides on the shared edge between two cards.
        
        Args:
            draw: ImageDraw object for the sheet
            card_positions: List of card positions
        """
        if len(card_positions) != 2:
            return
        
        # Calculate the shared edge (vertical line between cards)
        left_card_x, card_y = card_positions[0]
        right_card_x, _ = card_positions[1]
        
        shared_edge_x = left_card_x + self.card_config.width + (self.print_config.scaled_card_spacing // 2)
        
        guide_length = self.print_config.scaled_cut_guide_length
        guide_width = self.print_config.scaled_cut_guide_width
        guide_color = self.print_config.cut_guide_color
        
        # Top guide on shared edge
        draw.rectangle(
            [shared_edge_x - guide_width//2, card_y - guide_length, 
             shared_edge_x + guide_width//2, card_y],
            fill=guide_color
        )
        
        # Bottom guide on shared edge
        card_bottom = card_y + self.card_config.height
        draw.rectangle(
            [shared_edge_x - guide_width//2, card_bottom, 
             shared_edge_x + guide_width//2, card_bottom + guide_length],
            fill=guide_color
        )
        
        # Middle guides (optional - for extra precision)
        card_middle_y = card_y + (self.card_config.height // 2)
        draw.rectangle(
            [shared_edge_x - guide_width//2, card_middle_y - guide_length//2,
             shared_edge_x + guide_width//2, card_middle_y + guide_length//2],
            fill=guide_color
        )
    
    def get_sheet_info(self) -> dict:
        """
        Get information about the print sheet layout.
        
        Returns:
            Dictionary with layout information
        """
        return {
            'sheet_dimensions': (self.print_config.sheet_width, self.print_config.sheet_height),
            'card_dimensions': (self.card_config.width, self.card_config.height),
            'cards_per_sheet': self.print_config.cards_per_sheet,
            'sheet_margin': self.print_config.scaled_sheet_margin,
            'card_spacing': self.print_config.scaled_card_spacing,
            'dpi': self.card_config.dpi,
            'physical_sheet_size': '210mm x 297mm (A4 Landscape)',
            'physical_card_size': '148mm x 210mm (A5)'
        }