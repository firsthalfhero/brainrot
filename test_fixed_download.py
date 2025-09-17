#!/usr/bin/env python3
"""
Test the fixed download logic with the problematic characters mentioned.
"""

import os
import requests
from PIL import Image
from io import BytesIO
from download_images import find_character_portrait_images, get_original_image_url, clean_filename
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_character_download(character_name, wiki_url, expected_image_contains=None):
    """Test downloading a specific character with the fixed logic."""
    test_images_dir = "test_fixed_images"
    
    if not os.path.exists(test_images_dir):
        os.makedirs(test_images_dir)
    
    logger.info(f"Testing download for: {character_name}")
    logger.info(f"URL: {wiki_url}")
    
    try:
        response = requests.get(wiki_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find candidates using the fixed logic
        candidates = find_character_portrait_images(soup, character_name)
        
        if not candidates:
            logger.warning(f"No candidates found for {character_name}")
            return False
        
        logger.info(f"Found {len(candidates)} candidates:")
        for i, (img_src, score) in enumerate(candidates[:3]):
            logger.info(f"  {i+1}. Score {score}: {img_src}")
            if expected_image_contains and expected_image_contains in img_src:
                logger.info(f"     ✓ MATCHES EXPECTED IMAGE!")
        
        # Download only the top candidate
        img_src, score = candidates[0]
        original_img_src = get_original_image_url(img_src)
        
        logger.info(f"Downloading top candidate: {original_img_src}")
        
        # Check if it matches expected
        if expected_image_contains:
            if expected_image_contains in original_img_src:
                logger.info(f"✓ Top candidate matches expected image pattern!")
            else:
                logger.warning(f"✗ Top candidate does not match expected pattern: {expected_image_contains}")
        
        img_response = requests.get(original_img_src, timeout=30)
        img_response.raise_for_status()
        
        # Validate image
        img = Image.open(BytesIO(img_response.content))
        width, height = img.size
        
        logger.info(f"Image: {width}x{height}, format: {img.format}")
        
        # Save the image
        clean_name = clean_filename(character_name)
        ext = '.png' if '.png' in original_img_src.lower() else '.jpg'
        filename = f"{clean_name}_fixed{ext}"
        filepath = os.path.join(test_images_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        logger.info(f"✓ Downloaded: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading {character_name}: {e}")
        return False

# Test the problematic characters from your original prompt
test_cases = [
    ("Graipuss Medussi", "https://stealabrainrot.fandom.com/wiki/Graipuss_Medussi", "Graipuss.png"),
    ("Gangster Footera", "https://stealabrainrot.fandom.com/wiki/Gangster_Footera", "King_von.png")
]

print("Testing FIXED image download logic...")
print("This should now download ONLY the main character image from the infobox.")
print()

for character_name, url, expected_pattern in test_cases:
    print(f"{'='*60}")
    print(f"Testing: {character_name}")
    print(f"Expected image should contain: {expected_pattern}")
    print()
    
    success = test_character_download(character_name, url, expected_pattern)
    
    if success:
        print(f"✓ {character_name}: SUCCESS")
    else:
        print(f"✗ {character_name}: FAILED")
    print()

print(f"{'='*60}")
print("Test complete! Check the test_fixed_images directory.")
print("There should be exactly ONE image per character, and it should be the correct main character image.")