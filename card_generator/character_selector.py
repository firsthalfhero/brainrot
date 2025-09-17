"""
Character selection and filtering functionality for the Trading Card Generator.
"""

from typing import List, Optional, Dict, Any
from .data_models import CharacterData
from .data_loader import CSVDataLoader


class CharacterSelector:
    """
    Handles character selection and filtering operations for card generation.
    """
    
    def __init__(self, data_loader: CSVDataLoader):
        """
        Initialize the character selector.
        
        Args:
            data_loader: CSVDataLoader instance for loading character data
        """
        self.data_loader = data_loader
        self._all_characters: Optional[List[CharacterData]] = None
    
    def get_all_characters(self) -> List[CharacterData]:
        """
        Get all characters, caching the result for performance.
        
        Returns:
            List of all CharacterData objects
        """
        if self._all_characters is None:
            self._all_characters = self.data_loader.load_characters()
        return self._all_characters
    
    def select_characters(self, selection_criteria: Dict[str, Any]) -> List[CharacterData]:
        """
        Select characters based on multiple criteria.
        
        Args:
            selection_criteria: Dictionary containing selection parameters:
                - names: List[str] - Specific character names
                - name_pattern: str - Pattern for name matching (supports wildcards)
                - tiers: List[str] - Tier filters
                - variants: List[str] - Variant filters
                - min_cost: int - Minimum cost
                - max_cost: int - Maximum cost
                - min_income: int - Minimum income
                - max_income: int - Maximum income
                - with_images_only: bool - Only characters with images
                - without_images_only: bool - Only characters without images
                - case_sensitive: bool - Case sensitive matching
                
        Returns:
            List of CharacterData objects matching the criteria
        """
        characters = self.get_all_characters()
        
        # Apply name filters
        if selection_criteria.get('names'):
            characters = self.data_loader.filter_characters_by_name(
                characters, 
                selection_criteria['names'],
                selection_criteria.get('case_sensitive', False)
            )
        
        if selection_criteria.get('name_pattern'):
            characters = self.data_loader.filter_characters_by_name_pattern(
                characters,
                selection_criteria['name_pattern'],
                selection_criteria.get('case_sensitive', False)
            )
        
        # Apply tier filters
        if selection_criteria.get('tiers'):
            characters = self.data_loader.filter_characters_by_tier(
                characters,
                selection_criteria['tiers'],
                selection_criteria.get('case_sensitive', False)
            )
        
        # Apply variant filters
        if selection_criteria.get('variants'):
            characters = self.data_loader.filter_characters_by_variant(
                characters,
                selection_criteria['variants'],
                selection_criteria.get('case_sensitive', False)
            )
        
        # Apply cost range filters
        if selection_criteria.get('min_cost') is not None or selection_criteria.get('max_cost') is not None:
            characters = self.data_loader.filter_characters_by_cost_range(
                characters,
                selection_criteria.get('min_cost'),
                selection_criteria.get('max_cost')
            )
        
        # Apply income range filters
        if selection_criteria.get('min_income') is not None or selection_criteria.get('max_income') is not None:
            characters = self.data_loader.filter_characters_by_income_range(
                characters,
                selection_criteria.get('min_income'),
                selection_criteria.get('max_income')
            )
        
        # Apply image availability filters
        if selection_criteria.get('with_images_only'):
            characters = self.data_loader.filter_characters_with_images_only(characters)
        elif selection_criteria.get('without_images_only'):
            characters = self.data_loader.filter_characters_without_images_only(characters)
        
        return characters
    
    def select_by_names(self, names: List[str], case_sensitive: bool = False) -> List[CharacterData]:
        """
        Select characters by exact name matches.
        
        Args:
            names: List of character names to select
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List of matching CharacterData objects
        """
        return self.select_characters({
            'names': names,
            'case_sensitive': case_sensitive
        })
    
    def select_by_name_pattern(self, pattern: str, case_sensitive: bool = False) -> List[CharacterData]:
        """
        Select characters by name pattern.
        
        Args:
            pattern: Pattern to match (supports wildcards and regex)
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List of matching CharacterData objects
        """
        return self.select_characters({
            'name_pattern': pattern,
            'case_sensitive': case_sensitive
        })
    
    def select_by_tiers(self, tiers: List[str], case_sensitive: bool = False) -> List[CharacterData]:
        """
        Select characters by tier.
        
        Args:
            tiers: List of tiers to include
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List of matching CharacterData objects
        """
        return self.select_characters({
            'tiers': tiers,
            'case_sensitive': case_sensitive
        })
    
    def select_by_cost_range(self, min_cost: Optional[int] = None, 
                            max_cost: Optional[int] = None) -> List[CharacterData]:
        """
        Select characters by cost range.
        
        Args:
            min_cost: Minimum cost (inclusive)
            max_cost: Maximum cost (inclusive)
            
        Returns:
            List of matching CharacterData objects
        """
        return self.select_characters({
            'min_cost': min_cost,
            'max_cost': max_cost
        })
    
    def select_by_income_range(self, min_income: Optional[int] = None, 
                              max_income: Optional[int] = None) -> List[CharacterData]:
        """
        Select characters by income range.
        
        Args:
            min_income: Minimum income (inclusive)
            max_income: Maximum income (inclusive)
            
        Returns:
            List of matching CharacterData objects
        """
        return self.select_characters({
            'min_income': min_income,
            'max_income': max_income
        })
    
    def select_with_images_only(self) -> List[CharacterData]:
        """
        Select only characters that have associated image files.
        
        Returns:
            List of CharacterData objects with images
        """
        return self.select_characters({'with_images_only': True})
    
    def select_without_images_only(self) -> List[CharacterData]:
        """
        Select only characters that don't have associated image files.
        
        Returns:
            List of CharacterData objects without images
        """
        return self.select_characters({'without_images_only': True})
    
    def get_selection_summary(self, characters: List[CharacterData]) -> Dict[str, Any]:
        """
        Get summary statistics for a character selection.
        
        Args:
            characters: List of selected characters
            
        Returns:
            Dictionary with selection statistics
        """
        if not characters:
            return {
                'total_selected': 0,
                'tiers': {},
                'variants': {},
                'with_images': 0,
                'without_images': 0,
                'cost_range': {'min': None, 'max': None},
                'income_range': {'min': None, 'max': None}
            }
        
        # Count by tier
        tier_counts = {}
        for char in characters:
            tier_counts[char.tier] = tier_counts.get(char.tier, 0) + 1
        
        # Count by variant
        variant_counts = {}
        for char in characters:
            variant_counts[char.variant] = variant_counts.get(char.variant, 0) + 1
        
        # Count image availability
        with_images = sum(1 for char in characters if char.has_image())
        without_images = len(characters) - with_images
        
        # Get cost and income ranges
        costs = [char.cost for char in characters]
        incomes = [char.income for char in characters]
        
        return {
            'total_selected': len(characters),
            'tiers': tier_counts,
            'variants': variant_counts,
            'with_images': with_images,
            'without_images': without_images,
            'cost_range': {'min': min(costs), 'max': max(costs)},
            'income_range': {'min': min(incomes), 'max': max(incomes)}
        }
    
    def get_available_options(self) -> Dict[str, List[str]]:
        """
        Get all available options for filtering.
        
        Returns:
            Dictionary with available tiers, variants, and character names
        """
        return {
            'tiers': self.data_loader.get_available_tiers(),
            'variants': self.data_loader.get_available_variants(),
            'character_names': self.data_loader.get_character_names()
        }