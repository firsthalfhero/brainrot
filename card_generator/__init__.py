"""
Trading Card Generator Package

A system for generating printable A5 trading cards from Brainrot character data.
"""

__version__ = "1.0.0"
__author__ = "Trading Card Generator"

from .data_models import CharacterData
from .config import CardConfig, PrintConfig, OutputConfig, ConfigurationManager
from .data_loader import CSVDataLoader
from .character_selector import CharacterSelector
from .card_designer import CardDesigner
from .print_layout import PrintLayoutManager
from .output_manager import OutputManager
from .cli import CardGeneratorCLI

__all__ = [
    'CharacterData',
    'CardConfig', 
    'PrintConfig',
    'OutputConfig',
    'ConfigurationManager',
    'CSVDataLoader',
    'CharacterSelector',
    'CardDesigner',
    'PrintLayoutManager',
    'OutputManager',
    'CardGeneratorCLI'
]