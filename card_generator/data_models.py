"""
Data models for the Trading Card Generator.
"""

from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CharacterData:
    """
    Represents a Brainrot character with all necessary data for card generation.
    
    Attributes:
        name: Character display name
        tier: Rarity tier (Common, Rare, Epic, etc.)
        cost: Purchase cost in game currency
        income: Income per second value
        variant: Standard/Special variant indicator
        image_path: Path to character image file (set after image matching)
        
        # Additional fields for database building
        wiki_url: URL to the character's wiki page
        image_url: URL to the character's image on the wiki
        extraction_timestamp: When the data was extracted
        extraction_success: Whether extraction was successful
        extraction_errors: List of errors encountered during extraction
    """
    name: str
    tier: str
    cost: int
    income: int
    variant: str
    image_path: Optional[str] = None
    
    # New fields for database building
    wiki_url: Optional[str] = None
    image_url: Optional[str] = None
    extraction_timestamp: Optional[datetime] = None
    extraction_success: bool = True
    extraction_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate character data after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Character name must be a non-empty string")
        
        if not self.tier or not isinstance(self.tier, str):
            raise ValueError("Character tier must be a non-empty string")
            
        if not isinstance(self.cost, int) or self.cost < 0:
            raise ValueError("Character cost must be a non-negative integer")
            
        if not isinstance(self.income, int) or self.income < 0:
            raise ValueError("Character income must be a non-negative integer")
            
        if not self.variant or not isinstance(self.variant, str):
            raise ValueError("Character variant must be a non-empty string")
    
    def has_image(self) -> bool:
        """Check if character has an associated image file."""
        return self.image_path is not None and self.image_path.strip() != ""
    
    def __str__(self) -> str:
        """String representation of character."""
        return f"{self.name} ({self.tier}) - Cost: {self.cost}, Income: {self.income}/s"