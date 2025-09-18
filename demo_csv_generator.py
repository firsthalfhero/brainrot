#!/usr/bin/env python3
"""
Demo script for the CSVGenerator functionality.

This script demonstrates how to use the CSVGenerator to create database files
from character data that can be used by the existing card generation system.
"""

import os
import tempfile
from datetime import datetime

from card_generator.csv_generator import CSVGenerator
from card_generator.config import DatabaseBuilderConfig
from card_generator.data_models import CharacterData
from card_generator.data_loader import CSVDataLoader


def main():
    """Demonstrate CSVGenerator functionality."""
    print("=== CSV Generator Demo ===\n")
    
    # Create temporary directory for demo output
    temp_dir = tempfile.mkdtemp()
    print(f"Demo output directory: {temp_dir}")
    
    # Create configuration
    config = DatabaseBuilderConfig(
        output_dir=temp_dir,
        include_timestamp=True,
        csv_filename_template="demo_database_{timestamp}.csv"
    )
    
    # Create CSVGenerator
    csv_generator = CSVGenerator(config)
    print("✓ CSVGenerator initialized")
    
    # Create sample character data
    sample_characters = [
        CharacterData(
            name="Demo Character 1",
            tier="Common",
            cost=100,
            income=5,
            variant="Standard",
            image_path="images/Demo_Character_1.png"
        ),
        CharacterData(
            name="Demo Character 2",
            tier="Rare",
            cost=500,
            income=25,
            variant="Standard",
            image_path="images/Demo_Character_2.png"
        ),
        CharacterData(
            name="Special Demo Character",
            tier="Epic",
            cost=1000,
            income=50,
            variant="Special",
            image_path=None  # No image
        ),
        CharacterData(
            name="Legendary Demo",
            tier="Legendary",
            cost=2500,
            income=125,
            variant="Standard",
            image_path="images/Legendary_Demo.png"
        )
    ]
    
    print(f"✓ Created {len(sample_characters)} sample characters")
    
    # Generate CSV file
    print("\n--- Generating CSV Database ---")
    csv_path = csv_generator.generate_csv(sample_characters)
    print(f"✓ CSV generated: {os.path.basename(csv_path)}")
    
    # Display CSV content
    print("\n--- CSV Content ---")
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
    
    # Get CSV statistics
    print("--- CSV Statistics ---")
    stats = csv_generator.get_csv_statistics(csv_path)
    print(f"Total characters: {stats['total_characters']}")
    print(f"Characters with images: {stats['characters_with_images']}")
    print(f"Characters without images: {stats['characters_without_images']}")
    print(f"File size: {stats['file_size']} bytes")
    print(f"Tier breakdown: {stats['characters_by_tier']}")
    
    # Validate CSV format
    print("\n--- CSV Validation ---")
    try:
        is_valid = csv_generator.validate_csv_format(csv_path)
        print(f"✓ CSV format validation: {'PASSED' if is_valid else 'FAILED'}")
    except Exception as e:
        print(f"✗ CSV format validation: FAILED - {e}")
    
    # Test compatibility with existing CSVDataLoader
    print("\n--- Compatibility Test ---")
    try:
        data_loader = CSVDataLoader(csv_path)
        loaded_characters = data_loader.load_characters()
        print(f"✓ CSVDataLoader compatibility: PASSED")
        print(f"  Loaded {len(loaded_characters)} characters successfully")
        
        # Show loaded character details
        for char in loaded_characters:
            print(f"  - {char.name} ({char.tier}): Cost {char.cost}, Income {char.income}/s")
            
    except Exception as e:
        print(f"✗ CSVDataLoader compatibility: FAILED - {e}")
    
    # Test appending functionality
    print("\n--- Append Test ---")
    additional_character = [CharacterData(
        name="Appended Character",
        tier="Mythic",
        cost=5000,
        income=250,
        variant="Standard",
        image_path="images/Appended_Character.png"
    )]
    
    try:
        csv_generator.append_to_existing_csv(additional_character, csv_path)
        print("✓ Character appended successfully")
        
        # Get updated statistics
        updated_stats = csv_generator.get_csv_statistics(csv_path)
        print(f"  Updated total characters: {updated_stats['total_characters']}")
        
    except Exception as e:
        print(f"✗ Append test: FAILED - {e}")
    
    # Generate a second CSV with timestamp
    print("\n--- Multiple CSV Generation ---")
    import time
    time.sleep(1)  # Ensure different timestamp
    
    csv_path2 = csv_generator.generate_csv(sample_characters[:2])
    print(f"✓ Second CSV generated: {os.path.basename(csv_path2)}")
    print(f"  Different filename: {'YES' if csv_path != csv_path2 else 'NO'}")
    
    print(f"\n=== Demo Complete ===")
    print(f"Generated files in: {temp_dir}")
    print("Files will be cleaned up when the temporary directory is removed.")
    
    # Clean up
    import shutil
    try:
        shutil.rmtree(temp_dir)
        print("✓ Temporary files cleaned up")
    except Exception as e:
        print(f"⚠ Could not clean up temporary files: {e}")


if __name__ == "__main__":
    main()