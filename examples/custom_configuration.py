#!/usr/bin/env python3
"""
Custom configuration example for the Trading Card Generator.
Demonstrates using different configurations for various output needs.
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


def create_high_quality_config():
    """Create configuration for high-quality printing."""
    return CardConfig(
        width=2480,   # A5 at 420 DPI for extra quality
        height=3508,
        dpi=420,
        margin=80,
        background_color='#FFFFFF',
        image_ratio=0.65,  # Slightly larger image area
        font_size_name=120,
        font_size_stats=60
    )


def create_draft_config():
    """Create configuration for draft/preview quality."""
    return CardConfig(
        width=874,    # A5 at 150 DPI for faster processing
        height=1240,
        dpi=150,
        margin=25,
        background_color='#FFFFFF',
        image_ratio=0.6,
        font_size_name=60,
        font_size_stats=30
    )


def create_compact_print_config():
    """Create configuration for more cards per sheet."""
    return PrintConfig(
        sheet_width=3508,   # A4 at 300 DPI
        sheet_height=2480,
        cards_per_sheet=4,  # 4 cards per sheet instead of 2
        margin=30,
        cut_guide_width=1,
        cut_guide_color='#CCCCCC'  # Lighter cut guides
    )


def main():
    """Demonstrate custom configuration usage."""
    print("Trading Card Generator - Custom Configuration Example")
    print("=" * 65)
    
    # Configuration
    csv_path = 'steal_a_brainrot_complete_database.csv'
    images_dir = 'images'
    base_output_dir = 'output_custom'
    
    # Check if required files exist
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found!")
        return 1
    
    # Load character data once
    print("Loading character data...")
    data_loader = CSVDataLoader(csv_path, images_dir)
    all_characters = data_loader.load_characters()
    
    # Use first 5 characters for demonstration
    demo_characters = all_characters[:5]
    print(f"Using {len(demo_characters)} characters for demonstration:")
    for char in demo_characters:
        print(f"  - {char.name} ({char.tier})")
    
    # Example 1: High-quality configuration
    print("\n" + "-" * 50)
    print("Example 1: High-Quality Configuration (420 DPI)")
    
    high_quality_config = create_high_quality_config()
    output_dir_hq = os.path.join(base_output_dir, 'high_quality')
    
    generate_with_config(
        demo_characters,
        high_quality_config,
        PrintConfig(),  # Standard print config
        OutputConfig(
            individual_cards_dir=os.path.join(output_dir_hq, 'cards'),
            print_sheets_dir=os.path.join(output_dir_hq, 'sheets')
        ),
        "high_quality"
    )
    
    # Example 2: Draft configuration
    print("\n" + "-" * 50)
    print("Example 2: Draft Configuration (150 DPI)")
    
    draft_config = create_draft_config()
    output_dir_draft = os.path.join(base_output_dir, 'draft')
    
    generate_with_config(
        demo_characters,
        draft_config,
        PrintConfig(),  # Standard print config
        OutputConfig(
            individual_cards_dir=os.path.join(output_dir_draft, 'cards'),
            print_sheets_dir=os.path.join(output_dir_draft, 'sheets')
        ),
        "draft"
    )
    
    # Example 3: Compact print layout
    print("\n" + "-" * 50)
    print("Example 3: Compact Print Layout (4 cards per sheet)")
    
    compact_print_config = create_compact_print_config()
    output_dir_compact = os.path.join(base_output_dir, 'compact')
    
    generate_with_config(
        demo_characters,
        CardConfig(),  # Standard card config
        compact_print_config,
        OutputConfig(
            individual_cards_dir=os.path.join(output_dir_compact, 'cards'),
            print_sheets_dir=os.path.join(output_dir_compact, 'sheets')
        ),
        "compact"
    )
    
    # Example 4: Custom colors and styling
    print("\n" + "-" * 50)
    print("Example 4: Custom Colors and Styling")
    
    custom_config = CardConfig(
        background_color='#F5F5F5',  # Light gray background
        margin=60,
        image_ratio=0.55,  # Smaller image, more space for text
        font_size_name=100,
        font_size_stats=50
    )
    
    output_dir_custom = os.path.join(base_output_dir, 'custom_style')
    
    generate_with_config(
        demo_characters,
        custom_config,
        PrintConfig(),
        OutputConfig(
            individual_cards_dir=os.path.join(output_dir_custom, 'cards'),
            print_sheets_dir=os.path.join(output_dir_custom, 'sheets')
        ),
        "custom_style"
    )
    
    print("\n" + "=" * 65)
    print("Custom configuration examples complete!")
    print(f"Check the '{base_output_dir}' directory for different outputs:")
    print("  - high_quality/: 420 DPI cards for premium printing")
    print("  - draft/: 150 DPI cards for quick previews")
    print("  - compact/: 4 cards per sheet layout")
    print("  - custom_style/: Custom colors and styling")


def generate_with_config(characters, card_config, print_config, output_config, label):
    """Generate cards with specific configuration."""
    print(f"Generating cards with {label} configuration...")
    
    # Initialize components with custom configs
    image_processor = ImageProcessor()
    card_designer = CardDesigner(card_config)
    print_layout = PrintLayoutManager(print_config)
    output_manager = OutputManager(output_config)
    
    generated_cards = []
    
    # Generate cards
    for i, character in enumerate(characters, 1):
        print(f"  Processing {i}/{len(characters)}: {character.name}")
        
        # Create placeholder image (for consistent demonstration)
        image = image_processor.create_placeholder(
            character.name, character.tier, (400, 400)
        )
        
        try:
            card = card_designer.create_card(character, image)
            generated_cards.append((character, card))
            
            # Print card dimensions for verification
            print(f"    Card size: {card.size[0]}x{card.size[1]} pixels")
            
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
    
    print(f"    Print sheet size: {print_sheets[0].size if print_sheets else 'N/A'}")
    print(f"    Cards per sheet: {print_config.cards_per_sheet}")
    
    # Save outputs
    print(f"  Saving outputs...")
    
    # Save individual cards
    for character, card in generated_cards:
        try:
            output_manager.save_individual_card(card, character)
        except Exception as e:
            print(f"    Error saving card for {character.name}: {e}")
    
    # Save print sheets
    for i, sheet in enumerate(print_sheets, 1):
        try:
            output_manager.save_print_sheet(sheet, i)
        except Exception as e:
            print(f"    Error saving print sheet {i}: {e}")
    
    print(f"  Generated {len(generated_cards)} cards and {len(print_sheets)} print sheets")
    
    # Show file sizes for comparison
    if generated_cards:
        sample_card_path = os.path.join(
            output_config.individual_cards_dir,
            f"{generated_cards[0][0].name}_{generated_cards[0][0].tier}_card.png"
        )
        sample_card_path = "".join(c for c in sample_card_path if c.isalnum() or c in (' ', '-', '_', '.', '/', '\\')).rstrip()
        
        if os.path.exists(sample_card_path):
            file_size = os.path.getsize(sample_card_path) / 1024  # KB
            print(f"  Sample card file size: {file_size:.1f} KB")


if __name__ == '__main__':
    exit(main())