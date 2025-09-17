#!/usr/bin/env python3
"""
Selective generation example for the Trading Card Generator.
Demonstrates generating cards for specific characters or tiers.
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


def filter_by_tier(characters, tier):
    """Filter characters by tier."""
    return [c for c in characters if c.tier.lower() == tier.lower()]


def filter_by_names(characters, names):
    """Filter characters by specific names."""
    name_set = {name.lower() for name in names}
    return [c for c in characters if c.name.lower() in name_set]


def filter_by_cost_range(characters, min_cost, max_cost):
    """Filter characters by cost range."""
    return [c for c in characters if min_cost <= c.cost <= max_cost]


def main():
    """Demonstrate selective card generation."""
    print("Trading Card Generator - Selective Generation Example")
    print("=" * 60)
    
    # Configuration
    csv_path = 'steal_a_brainrot_complete_database.csv'
    images_dir = 'images'
    output_dir = 'output_selective'
    
    # Check if required files exist
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found!")
        return 1
    
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
    
    # Load all characters
    print(f"Loading characters from {csv_path}...")
    all_characters = data_loader.load_characters()
    print(f"Loaded {len(all_characters)} total characters")
    
    # Example 1: Generate cards for specific tier
    print("\n" + "-" * 40)
    print("Example 1: Generating cards for 'Legendary' tier")
    legendary_characters = filter_by_tier(all_characters, 'Legendary')
    print(f"Found {len(legendary_characters)} Legendary characters")
    
    if legendary_characters:
        generate_cards_for_characters(
            legendary_characters, 
            image_processor, 
            card_designer, 
            print_layout, 
            output_manager,
            "legendary"
        )
    
    # Example 2: Generate cards for specific characters
    print("\n" + "-" * 40)
    print("Example 2: Generating cards for specific characters")
    target_names = ["Noobini Pizzanini", "Tim Cheese", "FluriFlura", "Matteo"]
    specific_characters = filter_by_names(all_characters, target_names)
    print(f"Found {len(specific_characters)} of {len(target_names)} requested characters")
    
    for char in specific_characters:
        print(f"  - {char.name} ({char.tier})")
    
    if specific_characters:
        generate_cards_for_characters(
            specific_characters,
            image_processor,
            card_designer,
            print_layout,
            output_manager,
            "specific"
        )
    
    # Example 3: Generate cards for cost range
    print("\n" + "-" * 40)
    print("Example 3: Generating cards for characters costing 1000-5000")
    mid_cost_characters = filter_by_cost_range(all_characters, 1000, 5000)
    print(f"Found {len(mid_cost_characters)} characters in cost range 1000-5000")
    
    if mid_cost_characters:
        # Show first few characters in this range
        print("Sample characters in this range:")
        for char in mid_cost_characters[:5]:
            print(f"  - {char.name}: {char.cost} cost, {char.income} income/sec ({char.tier})")
        
        generate_cards_for_characters(
            mid_cost_characters,
            image_processor,
            card_designer,
            print_layout,
            output_manager,
            "mid_cost"
        )
    
    # Example 4: Generate cards for multiple tiers
    print("\n" + "-" * 40)
    print("Example 4: Generating cards for Rare and Epic tiers")
    rare_epic_characters = []
    rare_epic_characters.extend(filter_by_tier(all_characters, 'Rare'))
    rare_epic_characters.extend(filter_by_tier(all_characters, 'Epic'))
    print(f"Found {len(rare_epic_characters)} Rare and Epic characters")
    
    if rare_epic_characters:
        generate_cards_for_characters(
            rare_epic_characters,
            image_processor,
            card_designer,
            print_layout,
            output_manager,
            "rare_epic"
        )
    
    print("\n" + "=" * 60)
    print("Selective generation examples complete!")
    print(f"Check the '{output_dir}' directory for generated cards.")


def generate_cards_for_characters(characters, image_processor, card_designer, 
                                print_layout, output_manager, suffix):
    """Generate cards for a list of characters."""
    print(f"Generating {len(characters)} cards...")
    
    generated_cards = []
    
    for i, character in enumerate(characters, 1):
        print(f"  Processing {i}/{len(characters)}: {character.name}")
        
        # Load image or create placeholder
        if character.image_path and os.path.exists(character.image_path):
            try:
                image = image_processor.load_image(character.image_path)
            except Exception as e:
                print(f"    Error loading image: {e}")
                image = image_processor.create_placeholder(
                    character.name, character.tier, (400, 400)
                )
        else:
            image = image_processor.create_placeholder(
                character.name, character.tier, (400, 400)
            )
        
        # Generate card
        try:
            card = card_designer.create_card(character, image)
            generated_cards.append((character, card))
        except Exception as e:
            print(f"    Error generating card: {e}")
            continue
    
    if not generated_cards:
        print("  No cards generated!")
        return
    
    # Create print layouts
    print(f"  Creating print layouts...")
    cards_only = [card for _, card in generated_cards]
    print_sheets = print_layout.arrange_cards_for_printing(cards_only)
    
    # Save individual cards with suffix
    print(f"  Saving individual cards...")
    for character, card in generated_cards:
        try:
            # Modify filename to include suffix
            filename = f"{character.name}_{character.tier}_{suffix}_card.png"
            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            filepath = os.path.join(output_manager.config.individual_cards_dir, safe_filename)
            
            # Ensure directory exists
            os.makedirs(output_manager.config.individual_cards_dir, exist_ok=True)
            card.save(filepath, 'PNG', quality=95)
        except Exception as e:
            print(f"    Error saving card for {character.name}: {e}")
    
    # Save print sheets with suffix
    print(f"  Saving print sheets...")
    for i, sheet in enumerate(print_sheets, 1):
        try:
            filename = f"print_sheet_{suffix}_{i:03d}.png"
            filepath = os.path.join(output_manager.config.print_sheets_dir, filename)
            
            # Ensure directory exists
            os.makedirs(output_manager.config.print_sheets_dir, exist_ok=True)
            sheet.save(filepath, 'PNG', quality=95)
        except Exception as e:
            print(f"    Error saving print sheet {i}: {e}")
    
    print(f"  Generated {len(generated_cards)} cards and {len(print_sheets)} print sheets")


if __name__ == '__main__':
    exit(main())