#!/usr/bin/env python3
"""
Test the fixed download logic with specific characters.
"""

import csv
import os
from download_images import download_character_images

def test_specific_characters():
    """Test downloading specific characters with the fixed logic."""
    
    # Read the CSV to get all characters
    csv_file = 'steal_a_brainrot_complete_database.csv'
    characters = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        characters = [row['Character Name'].strip('"') for row in reader]
    
    # Characters to test
    test_chars = ['Graipuss Medussi', 'Gangster Footera']
    print(f'Will test: {test_chars}')
    
    # Clean up existing images for these characters
    for char in test_chars:
        # Try different filename patterns
        possible_files = [
            f'images/{char}.png',
            f'images/{char}.jpg',
            f'images/{char.replace(" ", "_")}.png',
            f'images/{char.replace(" ", "_")}.jpg',
        ]
        
        for filepath in possible_files:
            if os.path.exists(filepath):
                print(f'Removing existing file: {filepath}')
                os.remove(filepath)
    
    print('Testing a few characters with the fixed logic...')
    
    # Now run the download function
    download_character_images()

if __name__ == "__main__":
    test_specific_characters()