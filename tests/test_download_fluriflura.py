import os
import requests
from PIL import Image
from io import BytesIO
from download_images import find_character_portrait_images, get_original_image_url, clean_filename
from bs4 import BeautifulSoup

# Create test directory
test_dir = "test_download"
if not os.path.exists(test_dir):
    os.makedirs(test_dir)

# Get the page
response = requests.get('https://stealabrainrot.fandom.com/wiki/Fluriflura')
soup = BeautifulSoup(response.content, 'html.parser')

# Find candidates
candidates = find_character_portrait_images(soup, 'Fluriflura')
print(f'Found {len(candidates)} candidates')

if candidates:
    # Download the top candidate
    img_src, score = candidates[0]
    original_img_src = get_original_image_url(img_src)
    
    print(f'Downloading: {original_img_src}')
    
    img_response = requests.get(original_img_src, timeout=30)
    img_response.raise_for_status()
    
    # Validate image
    img = Image.open(BytesIO(img_response.content))
    width, height = img.size
    
    print(f'Image: {width}x{height}, format: {img.format}')
    
    # Save the image
    clean_name = clean_filename('Fluriflura')
    ext = '.png' if '.png' in original_img_src.lower() else '.jpg'
    filename = f"{clean_name}{ext}"
    filepath = os.path.join(test_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(img_response.content)
    
    print(f'✓ Downloaded: {filename}')
    print(f'✓ File saved to: {filepath}')
else:
    print('✗ No candidates found')