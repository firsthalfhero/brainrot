#!/usr/bin/env python3
"""
Test downloading just the two specific characters.
"""

import csv
import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
from download_images import find_character_portrait_images, get_original_image_url, clean_filename, character_has_existing_images
from PIL import Image
from io import BytesIO
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_specific_characters(character_names):
    """Download images for specific characters only."""
    base_url = "https://stealabrainrot.fandom.com"
    images_dir = "images"
    
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    for character_name in character_names:
        if character_has_existing_images(character_name, images_dir):
            logger.info(f"Skipping {character_name} - images already exist")
            continue
            
        logger.info(f"Searching for images of: {character_name}")
        
        try:
            # Try direct wiki page first
            character_page_url = f"{base_url}/wiki/{character_name.replace(' ', '_')}"
            logger.info(f"  Trying page: {character_page_url}")
            
            page_response = requests.get(character_page_url)
            page_response.raise_for_status()
            
            page_soup = BeautifulSoup(page_response.content, 'html.parser')
            
            # Find candidate character portrait images
            candidate_images = find_character_portrait_images(page_soup, character_name)
            
            if not candidate_images:
                logger.warning(f"  No suitable images found for {character_name}")
                continue
            
            logger.info(f"  Found {len(candidate_images)} candidate images")
            
            # Download only the top candidate
            img_src, score = candidate_images[0]
            original_img_src = get_original_image_url(img_src)
            
            logger.info(f"  Downloading: {original_img_src} (score: {score})")
            
            img_response = requests.get(original_img_src, timeout=30)
            img_response.raise_for_status()
            
            # Validate image
            img = Image.open(BytesIO(img_response.content))
            width, height = img.size
            
            logger.info(f"  Image: {width}x{height}, format: {img.format}")
            
            # Generate filename
            clean_name = clean_filename(character_name)
            ext = '.png' if '.png' in original_img_src.lower() else '.jpg'
            filename = f"{clean_name}{ext}"
            filepath = os.path.join(images_dir, filename)
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            logger.info(f"  ✓ Downloaded: {filename}")
            
            # Rate limiting
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error processing {character_name}: {e}")
            continue

if __name__ == "__main__":
    test_characters = ['Graipuss Medussi', 'Gangster Footera']
    print(f"Testing fixed download logic with: {test_characters}")
    download_specific_characters(test_characters)
    print("Download test complete!")