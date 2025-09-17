#!/usr/bin/env python3
"""
Basic usage example for the Trading Card Generator.
Demonstrates generating cards for all characters in the database.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import card_generator
sys.path.insert(0, str(Path(__file__).parent.parent))

from card_generator.data_loader import CSVDataLoader
from card_generator.image_processor import ImageProcessor
from card_generator.card_designer import CardDesigner
from card_generator.print_layout import PrintLayoutManager
from card_generator.output_manager import OutputManager
from card_generator.config import CardConfig, PrintConfig, OutputConfig


def main():
    """Generate cards for all characters in the database."""
    print("Trading Card Generator - Basic Usage Example")
    print("=" * 50)
    
    # Configuration
    csv_path = 'steal_a_brainrot_complete_database.csv'
    images_dir = 'images'
    output_dir = 'output'
    
    # Check if required files exist
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found!")
        print("Please ensure the character database file is in the current directory.")
        return 1
    
    if not os.path.exists(images_dir):
        print(f"Warning: Images directory '{images_dir}' not found!")
        print("Cards will be generated with placeholder images.")
    
    # Initialize components
    print("Initializing components...")
    data_loader = CSVDataLoader(csv_path, images_dir)
    image_processor = ImageProcessor()
    card_designer = CardDesigner(CardConfig())
    print_layout = PrintLayoutManager(PrintConfig())
    output_manager = OutputManager(OutputConfig(
        individual_cards_dir=os.path.join(output_dir, 'individual_cards'),
        print_sheets_dir=os.path.join(output_dir, 'print_sheets')
    ))
    
    # Load character data
    print(f"Loading characters from {csv_path}...")
    characters = data_loader.load_characters()
    print(f"Loaded {len(characters)} characters")
    
    if not characters:
        print("No characters loaded! Please check your CSV file.")
        return 1
    
    # Generate cards
    print("Generating cards...")
    generated_cards = []
    
    for i, character in enumerate(characters, 1):
        print(f"Processing {i}/{len(characters)}: {character.name}")
        
        # Load character image or create placeholder
        if character.image_path and os.path.exists(character.image_path):
            try:
                image = image_processor.load_image(character.image_path)
                print(f"  Using image: {character.image_path}")
            except Exception as e:
                print(f"  Error loading image: {e}")
                image = image_processor.create_placeholder(
                    character.name, character.tier, (400, 400)
                )
                print(f"  Using placeholder image")
        else:
            image = image_processor.create_placeholder(
                character.name, character.tier, (400, 400)
            )
            print(f"  Using placeholder image (no image file found)")
        
        # Generate card
        try:
            card = card_designer.create_card(character, image)
            generated_cards.append((character, card))
            print(f"  Card generated successfully")
        except Exception as e:
            print(f"  Error generating card: {e}")
            continue
    
    print(f"Successfully generated {len(generated_cards)} cards")
    
    # Create print layouts
    print("Creating print layouts...")
    cards_only = [card for _, card in generated_cards]
    print_sheets = print_layout.arrange_cards_for_printing(cards_only)
    print(f"Created {len(print_sheets)} print sheets")
    
    # Save outputs
    print("Saving individual cards...")
    for character, card in generated_cards:
        try:
            output_manager.save_individual_card(card, character)
        except Exception as e:
            print(f"Error saving card for {character.name}: {e}")
    
    print("Saving print sheets...")
    for i, sheet in enumerate(print_sheets, 1):
        try:
            output_manager.save_print_sheet(sheet, i)
        except Exception as e:
            print(f"Error saving print sheet {i}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Generation Complete!")
    print(f"Individual cards: {output_manager.config.individual_cards_dir}")
    print(f"Print sheets: {output_manager.config.print_sheets_dir}")
    print(f"Total cards generated: {len(generated_cards)}")
    print(f"Total print sheets: {len(print_sheets)}")
    
    return 0


if __name__ == '__main__':
    exit(main())