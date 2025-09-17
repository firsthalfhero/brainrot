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

def test_download_character(character_name, wiki_url):
    """Test downloading a specific character with the fixed logic."""
    images_dir = "images"
    
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    logger.info(f"Testing download for: {character_name}")
    
    try:
        response = requests.get(wiki_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find candidates
        candidates = find_character_portrait_images(soup, character_name)
        
        if not candidates:
            logger.warning(f"No candidates found for {character_name}")
            return False
        
        # Download the top candidate
        img_src, score = candidates[0]
        original_img_src = get_original_image_url(img_src)
        
        logger.info(f"Downloading: {original_img_src}")
        
        img_response = requests.get(original_img_src, timeout=30)
        img_response.raise_for_status()
        
        # Validate image
        img = Image.open(BytesIO(img_response.content))
        width, height = img.size
        
        logger.info(f"Image: {width}x{height}, format: {img.format}")
        
        # Save the image
        clean_name = clean_filename(character_name)
        ext = '.png' if '.png' in original_img_src.lower() else '.jpg'
        filename = f"{clean_name}{ext}"
        filepath = os.path.join(images_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        logger.info(f"✓ Downloaded: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading {character_name}: {e}")
        return False

# Test the problematic characters
test_cases = [
    ("Graipuss Medussi", "https://stealabrainrot.fandom.com/wiki/Graipuss_Medussi"),
    ("Gangster Footera", "https://stealabrainrot.fandom.com/wiki/Gangster_Footera")
]

print("Testing fixed image download logic...")
for character_name, url in test_cases:
    print(f"\n{'='*50}")
    success = test_download_character(character_name, url)
    if success:
        print(f"✓ {character_name}: SUCCESS")
    else:
        print(f"✗ {character_name}: FAILED")

print(f"\n{'='*50}")
print("Test complete!")