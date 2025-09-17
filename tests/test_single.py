import requests
import os
from urllib.parse import urljoin, urlparse
import time
from bs4 import BeautifulSoup
import re
from PIL import Image
from io import BytesIO

def clean_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def get_original_image_url(img_src):
    if 'scale-to-width-down' in img_src:
        img_src = re.sub(r'/scale-to-width-down/\d+', '', img_src)
    if 'scale-to-height-down' in img_src:
        img_src = re.sub(r'/scale-to-height-down/\d+', '', img_src)
    if '/revision/latest/' in img_src and '?' in img_src:
        parts = img_src.split('/revision/latest/')
        if len(parts) == 2:
            base = parts[0]
            callback = parts[1].split('?cb=')[-1] if '?cb=' in parts[1] else None
            if callback:
                img_src = f"{base}/revision/latest?cb={callback}"
            else:
                img_src = f"{base}/revision/latest"
    return img_src

def test_single_character(character_name):
    base_url = "https://stealabrainrot.fandom.com"
    images_dir = "images"
    
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    print(f"Searching for images of: {character_name}")
    
    try:
        search_url = f"{base_url}/wiki/Special:Search"
        search_params = {
            'query': character_name,
            'scope': 'internal',
            'navigationSearch': 'true'
        }
        
        print(f"Searching: {search_url}?query={character_name}")
        response = requests.get(search_url, params=search_params)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        character_page_link = None
        search_results = soup.find_all('a', href=True)
        
        for link in search_results:
            if character_name.lower() in link.get_text().lower():
                href = link['href']
                if href.startswith('/wiki/') and 'Special:' not in href:
                    character_page_link = urljoin(base_url, href)
                    print(f"Found character page link: {character_page_link}")
                    break
        
        if not character_page_link:
            character_page_url = f"{base_url}/wiki/{character_name.replace(' ', '_')}"
            character_page_link = character_page_url
            print(f"Using direct URL: {character_page_link}")
        
        print(f"Checking page: {character_page_link}")
        
        page_response = requests.get(character_page_link)
        if page_response.status_code == 404:
            print(f"Character page not found for {character_name}")
            return
        
        page_response.raise_for_status()
        page_soup = BeautifulSoup(page_response.content, 'html.parser')
        
        images = page_soup.find_all('img')
        print(f"Found {len(images)} total images on page")
        downloaded_count = 0
        
        for i, img in enumerate(images):
            img_src = img.get('src') or img.get('data-src')
            if not img_src:
                continue
            
            print(f"  Image {i+1}: {img_src}")
            
            if img_src.startswith('//'):
                img_src = 'https:' + img_src
            elif img_src.startswith('/'):
                img_src = urljoin(base_url, img_src)
            
            if 'static.wikia.nocookie.net' in img_src or 'vignette.wikia.nocookie.net' in img_src:
                if 'Site-logo' in img_src or 'site-logo' in img_src:
                    print(f"    Skipping site logo: {img_src}")
                    continue
                if any(ext in img_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    print(f"    Checking Wikia image: {img_src}")
                    original_img_src = get_original_image_url(img_src)
                    print(f"    Original URL: {original_img_src}")
                    try:
                        img_response = requests.get(original_img_src)
                        img_response.raise_for_status()
                        
                        try:
                            img_obj = Image.open(BytesIO(img_response.content))
                            width, height = img_obj.size
                            
                            print(f"    Image size: {width}x{height}")
                            
                            if width < 500 or height < 500:
                                print(f"    Skipping small image: {width}x{height}")
                                continue
                            
                            print(f"    Found large image: {width}x{height}")
                            
                        except Exception as e:
                            print(f"    Could not determine image size: {e}")
                            continue
                        
                        filename = f"{clean_filename(character_name)}_{downloaded_count + 1}"
                        
                        if '.jpg' in img_src.lower() or '.jpeg' in img_src.lower():
                            filename += '.jpg'
                        elif '.png' in img_src.lower():
                            filename += '.png'
                        elif '.gif' in img_src.lower():
                            filename += '.gif'
                        elif '.webp' in img_src.lower():
                            filename += '.webp'
                        else:
                            filename += '.jpg'
                        
                        filepath = os.path.join(images_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(img_response.content)
                        
                        print(f"    Downloaded: {filename} ({width}x{height})")
                        downloaded_count += 1
                        
                    except Exception as e:
                        print(f"    Failed to download image: {e}")
                else:
                    print(f"    Skipping non-image file: {img_src}")
            else:
                print(f"    Skipping non-Wikia image: {img_src}")
        
        if downloaded_count == 0:
            print(f"No large images found for {character_name}")
        else:
            print(f"Downloaded {downloaded_count} large images for {character_name}")
        
    except Exception as e:
        print(f"Error processing {character_name}: {e}")

def test_multiple_characters(character_names):
    """
    Test the image download functionality with an array of character names

    Args:
        character_names: List of character names to test
    """
    print(f"Testing image download for {len(character_names)} characters...")
    print("=" * 60)

    successful_downloads = 0
    failed_downloads = 0

    for i, character_name in enumerate(character_names, 1):
        print(f"\n[{i}/{len(character_names)}] Testing: {character_name}")
        print("-" * 40)

        try:
            test_single_character(character_name)
            successful_downloads += 1
        except Exception as e:
            print(f"FAILED: {character_name} - {e}")
            failed_downloads += 1

        # Add delay between requests to be respectful to the server
        if i < len(character_names):
            print("Waiting 2 seconds before next character...")
            time.sleep(2)

    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"Total characters tested: {len(character_names)}")
    print(f"Successful: {successful_downloads}")
    print(f"Failed: {failed_downloads}")
    print("=" * 60)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Use command line arguments as character names
        test_characters = sys.argv[1:]
        print(f"Testing characters from command line: {test_characters}")
        test_multiple_characters(test_characters)
    else:
        # Default test characters if no arguments provided
        test_characters = [
            "Trippi Troppi",
            "Noobini Pizzanini",
            "Spaghetti Boi",
            "Lirilì Larilà",
            "Tim Cheese"
        ]
        print("No arguments provided. Using default test characters.")
        test_multiple_characters(test_characters)