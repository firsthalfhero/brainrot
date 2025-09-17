"""
Test script to download images for a single character to verify the improved logic.
"""

import requests
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import logging
from download_images import find_character_portrait_images, get_original_image_url, clean_filename
from PIL import Image
from io import BytesIO

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_character_download(character_name, expected_image_url=None):
    """Test downloading images for a specific character."""
    base_url = "https://stealabrainrot.fandom.com"
    images_dir = "test_images"
    
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    logger.info(f"Testing image download for: {character_name}")
    
    try:
        # Try direct wiki page
        character_page_url = f"{base_url}/wiki/{character_name.replace(' ', '_')}"
        logger.info(f"Trying page: {character_page_url}")
        
        page_response = requests.get(character_page_url)
        page_response.raise_for_status()
        
        page_soup = BeautifulSoup(page_response.content, 'html.parser')
        
        # Find candidate character portrait images
        candidate_images = find_character_portrait_images(page_soup, character_name)
        
        if not candidate_images:
            logger.warning(f"No suitable images found for {character_name}")
            return False
        
        logger.info(f"Found {len(candidate_images)} candidate images:")
        for i, (img_src, score) in enumerate(candidate_images[:5]):  # Show top 5
            logger.info(f"  {i+1}. Score {score}: {img_src}")
        
        # Check if expected image is in top candidates
        if expected_image_url:
            found_expected = False
            for img_src, score in candidate_images[:3]:
                if expected_image_url in img_src or img_src in expected_image_url:
                    found_expected = True
                    logger.info(f"✓ Expected image found with score {score}")
                    break
            
            if not found_expected:
                logger.warning(f"✗ Expected image not found in top candidates")
                logger.info(f"Expected: {expected_image_url}")
        
        # Download the top candidate
        img_src, score = candidate_images[0]
        original_img_src = get_original_image_url(img_src)
        
        logger.info(f"Downloading top candidate: {original_img_src}")
        
        img_response = requests.get(original_img_src, timeout=30)
        img_response.raise_for_status()
        
        # Validate image
        img = Image.open(BytesIO(img_response.content))
        width, height = img.size
        
        logger.info(f"Image dimensions: {width}x{height}")
        logger.info(f"Image format: {img.format}")
        
        # Save the image
        clean_name = clean_filename(character_name)
        ext = '.png' if '.png' in original_img_src.lower() else '.jpg'
        filename = f"{clean_name}_test{ext}"
        filepath = os.path.join(images_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        logger.info(f"✓ Successfully downloaded: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing {character_name}: {e}")
        return False

if __name__ == "__main__":
    # Test with Fluriflura specifically
    print("Testing improved image download logic...")
    
    # Test cases
    test_cases = [
        ("Fluriflura", "https://static.wikia.nocookie.net/stealabr/images/7/77/Fluriflura.png"),
        ("Skibidi Toilet", None),  # Another character to test
        ("Ohio", None),  # Another character to test
    ]
    
    for character_name, expected_url in test_cases:
        print(f"\n{'='*50}")
        success = test_character_download(character_name, expected_url)
        if success:
            print(f"✓ {character_name}: SUCCESS")
        else:
            print(f"✗ {character_name}: FAILED")
    
    print(f"\n{'='*50}")
    print("Test complete! Check the test_images directory for downloaded files.")