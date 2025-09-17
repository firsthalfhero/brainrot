import csv
import requests
import os
from urllib.parse import urljoin, urlparse
import time
from bs4 import BeautifulSoup
import re
from PIL import Image
from io import BytesIO
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_filename(filename):
    """Clean filename to be filesystem-safe."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def get_original_image_url(img_src):
    """Convert scaled/thumbnail image URLs to original full-size URLs."""
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

def character_has_existing_images(character_name, images_dir):
    """Check if character already has downloaded images."""
    clean_name = clean_filename(character_name)
    existing_files = [f for f in os.listdir(images_dir) if f.startswith(clean_name) and any(ext in f.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]
    return len(existing_files) > 0

def is_character_portrait(img_src, character_name, img_element=None):
    """
    Determine if an image is likely the main character portrait.
    
    Args:
        img_src: Image source URL
        character_name: Name of the character
        img_element: BeautifulSoup img element (for additional context)
        
    Returns:
        int: Score indicating likelihood (higher = better match)
    """
    # Clean character name for comparison
    clean_char_name = character_name.lower().replace(' ', '').replace('-', '').replace('_', '')
    
    # Extract filename from URL (handle wikia URL structure)
    # URLs look like: .../images/7/77/Fluriflura.png/revision/latest/scale-to-width-down/268?cb=...
    url_parts = img_src.split('/')
    filename = ""
    
    # Find the actual filename (before /revision/ if present)
    for i, part in enumerate(url_parts):
        if part == 'revision' and i > 0:
            filename = url_parts[i-1]
            break
    
    # If no revision found, use the last part before query params
    if not filename:
        filename = img_src.split('/')[-1].split('?')[0]
    
    filename = filename.lower()
    clean_filename = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '').replace('.gif', '').replace('.webp', '')
    
    # Priority scoring system
    score = 0
    
    # Penalty for obvious non-character images first
    exclude_patterns = [
        'site-logo', 'wiki-logo', 'favicon', 'cursor', 'button', 'arrow',
        'edit', 'delete', 'admin', 'staff', 'moderator', 'template',
        'navigation', 'menu', 'wordmark'
    ]
    for pattern in exclude_patterns:
        if pattern in img_src.lower():
            return 0  # Immediate disqualification
    
    # Special case: exclude "tralaleritos" but only if it's not part of the character name
    if 'tralaleritos' in clean_filename and 'tralaleritos' not in clean_char_name:
        return 0
    
    # Check image context from HTML element
    if img_element:
        # High priority for images in infobox or main content area
        parent_classes = []
        current = img_element.parent
        depth = 0
        while current and depth < 5:  # Check up to 5 levels up
            if current.get('class'):
                parent_classes.extend(current.get('class'))
            if current.get('id'):
                parent_classes.append(current.get('id'))
            current = current.parent
            depth += 1
        
        parent_classes_str = ' '.join(parent_classes).lower()
        
        # Bonus for being in infobox or main content
        if any(indicator in parent_classes_str for indicator in ['infobox', 'portable-infobox', 'character-infobox']):
            score += 100
        
        # Bonus for being in main content area
        if any(indicator in parent_classes_str for indicator in ['mw-content', 'page-content', 'article']):
            score += 50
        
        # Check alt text and title attributes
        alt_text = (img_element.get('alt') or '').lower()
        title_text = (img_element.get('title') or '').lower()
        
        if clean_char_name in alt_text.replace(' ', '').replace('-', '').replace('_', ''):
            score += 80
        if clean_char_name in title_text.replace(' ', '').replace('-', '').replace('_', ''):
            score += 80
    
    # Highest priority: exact character name match
    if clean_char_name == clean_filename.replace('-', '').replace('_', ''):
        score += 300
    
    # Very high priority: filename starts with character name
    if clean_filename.replace('-', '').replace('_', '').startswith(clean_char_name):
        score += 200
    
    # High priority: character name is contained in filename
    if clean_char_name in clean_filename.replace('-', '').replace('_', ''):
        score += 150
    
    # Check for partial matches with character name parts
    char_words = [word.lower() for word in character_name.split() if len(word) > 2]  # Skip short words
    filename_clean = clean_filename.replace('-', ' ').replace('_', ' ')
    
    if char_words:
        matching_words = sum(1 for word in char_words if word in filename_clean)
        word_match_ratio = matching_words / len(char_words)
        score += int(word_match_ratio * 100)
        
        # Special bonus if all words match
        if matching_words == len(char_words):
            score += 50
    
    # Bonus for being the exact character name without modifiers
    if clean_filename.replace('-', '').replace('_', '') == clean_char_name:
        score += 75
    
    # Small penalty for variant indicators (we prefer the base image)
    variant_indicators = ['gold', 'silver', 'variant', 'alt', 'alternative', 'v2', 'new', 'old', 'beta']
    for indicator in variant_indicators:
        if indicator in clean_filename:
            score -= 15
    
    # Penalty for obvious non-portrait indicators
    non_portrait_indicators = ['group', 'team', 'multiple', 'all', 'together', 'cast', 'lineup']
    for indicator in non_portrait_indicators:
        if indicator in clean_filename:
            score -= 30
    
    # High priority: appears to be from wikia/fandom static content
    if 'static.wikia.nocookie.net' in img_src or 'vignette.wikia.nocookie.net' in img_src:
        score += 40
    
    # Bonus for PNG format (often used for character portraits with transparency)
    if '.png' in img_src.lower():
        score += 20
    
    # Bonus for being in the main images directory structure
    if '/images/' in img_src and not '/thumb/' in img_src:
        score += 30
    
    return max(0, score)  # Ensure non-negative score

def find_character_portrait_images(page_soup, character_name):
    """
    Find the most likely character portrait images from a wiki page.
    Prioritizes infobox hero images which are the main character portraits.
    
    Args:
        page_soup: BeautifulSoup object of the character's wiki page
        character_name: Name of the character
        
    Returns:
        list: List of (image_url, score) tuples, sorted by score descending
    """
    candidate_images = []
    seen_urls = set()  # Avoid duplicates
    
    # PRIORITY 1: Look for the MAIN character image in infobox
    # First, look specifically for figures with data-source="image1" (primary infobox image)
    primary_infobox = page_soup.find_all('figure', attrs={'data-source': 'image1'})
    
    # Then look for pi-item pi-image figures (main infobox images)
    pi_item_figures = page_soup.find_all('figure', class_=lambda x: x and 'pi-item' in ' '.join(x) and 'pi-image' in ' '.join(x))
    
    # Then look for pi-hero figures (hero images)
    pi_hero_figures = page_soup.find_all('figure', class_=lambda x: x and 'pi-hero' in ' '.join(x))
    
    # Combine in priority order: data-source="image1" first, then pi-item pi-image, then pi-hero
    infobox_figures = primary_infobox + pi_item_figures + pi_hero_figures
    
    # Remove duplicates while preserving order
    seen_figures = set()
    unique_figures = []
    for fig in infobox_figures:
        fig_id = id(fig)
        if fig_id not in seen_figures:
            seen_figures.add(fig_id)
            unique_figures.append(fig)
    infobox_figures = unique_figures
    
    logger.info(f"  Found {len(infobox_figures)} infobox figures")
    
    for figure in infobox_figures:
        # Look for images within the figure
        imgs = figure.find_all('img')
        for img in imgs:
            img_src = img.get('src') or img.get('data-src')
            if not img_src:
                continue
            
            # Convert relative URLs to absolute
            if img_src.startswith('//'):
                img_src = 'https:' + img_src
            elif img_src.startswith('/'):
                img_src = urljoin('https://stealabrainrot.fandom.com', img_src)
            
            # Skip duplicates
            base_url = img_src.split('/revision/')[0] if '/revision/' in img_src else img_src.split('?')[0]
            if base_url in seen_urls:
                continue
            seen_urls.add(base_url)
            
            # Only consider wikia/fandom images with proper extensions
            if (('static.wikia.nocookie.net' in img_src or 'vignette.wikia.nocookie.net' in img_src) and 
                any(ext in img_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])):
                
                # Give massive bonus for infobox images, with extra priority for specific types
                score = is_character_portrait(img_src, character_name, img)
                
                # Check what type of infobox figure this is
                figure_classes = ' '.join(figure.get('class', []))
                data_source = figure.get('data-source')
                
                if data_source == 'image1':
                    score += 2000  # Highest priority for data-source="image1"
                    logger.info(f"    PRIMARY INFOBOX (data-source=image1): {img_src} (score: {score})")
                elif 'pi-item' in figure_classes and 'pi-image' in figure_classes:
                    score += 1500  # Very high priority for pi-item pi-image
                    logger.info(f"    PI-ITEM PI-IMAGE: {img_src} (score: {score})")
                elif 'pi-hero' in figure_classes:
                    score += 1200  # High priority for pi-hero
                    logger.info(f"    PI-HERO: {img_src} (score: {score})")
                else:
                    score += 1000  # Standard infobox bonus
                
                candidate_images.append((img_src, score))
                logger.info(f"    Infobox image found: {img_src} (score: {score})")
        
        # Also check data-attrs for direct image URLs (like in your Gangster Footera example)
        data_attrs = figure.get('data-attrs')
        if data_attrs:
            try:
                import json
                attrs = json.loads(data_attrs.replace('&quot;', '"'))
                if 'url' in attrs:
                    img_src = attrs['url']
                    
                    base_url = img_src.split('/revision/')[0] if '/revision/' in img_src else img_src.split('?')[0]
                    if base_url not in seen_urls:
                        seen_urls.add(base_url)
                        
                        if (('static.wikia.nocookie.net' in img_src or 'vignette.wikia.nocookie.net' in img_src) and 
                            any(ext in img_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])):
                            
                            score = is_character_portrait(img_src, character_name, None)
                            
                            # Check what type of infobox figure this data-attrs is from
                            figure_classes = ' '.join(figure.get('class', []))
                            data_source = figure.get('data-source')
                            
                            if data_source == 'image1':
                                score += 2200  # Highest priority for data-source="image1" with data-attrs
                                logger.info(f"    DATA-ATTRS PRIMARY INFOBOX (data-source=image1): {img_src}")
                            elif 'pi-item' in figure_classes and 'pi-image' in figure_classes:
                                score += 1700  # Very high priority for pi-item pi-image with data-attrs
                                logger.info(f"    DATA-ATTRS PI-ITEM PI-IMAGE: {img_src}")
                            elif 'pi-hero' in figure_classes:
                                score += 1400  # High priority for pi-hero with data-attrs
                                logger.info(f"    DATA-ATTRS PI-HERO: {img_src}")
                            else:
                                score += 1200  # Standard data-attrs infobox bonus
                            
                            candidate_images.append((img_src, score))
                            logger.info(f"    Infobox data-attrs image: {img_src} (score: {score})")
            except:
                pass  # Ignore JSON parsing errors
    
    # If we found infobox images, prioritize them heavily
    if candidate_images:
        logger.info(f"  Found {len(candidate_images)} infobox images - prioritizing these")
        candidate_images.sort(key=lambda x: x[1], reverse=True)
        return candidate_images
    
    # PRIORITY 2: Fallback to general image search if no infobox images found
    logger.info(f"  No infobox images found, falling back to general search")
    
    images = page_soup.find_all('img')
    logger.info(f"  Found {len(images)} total images on page")
    
    for img in images:
        img_src = img.get('src') or img.get('data-src')
        if not img_src:
            continue
        
        # Convert relative URLs to absolute
        if img_src.startswith('//'):
            img_src = 'https:' + img_src
        elif img_src.startswith('/'):
            img_src = urljoin('https://stealabrainrot.fandom.com', img_src)
        
        # Skip duplicates
        base_url = img_src.split('/revision/')[0] if '/revision/' in img_src else img_src.split('?')[0]
        if base_url in seen_urls:
            continue
        seen_urls.add(base_url)
        
        # Only consider wikia/fandom images
        if 'static.wikia.nocookie.net' in img_src or 'vignette.wikia.nocookie.net' in img_src:
            # Skip obvious non-character images
            skip_patterns = [
                'site-logo', 'favicon', 'cursor', 'wiki-logo', 'wordmark',
                'navigation', 'menu', 'commons.wikimedia.org', 'upload.wikimedia.org'
            ]
            if any(skip in img_src.lower() for skip in skip_patterns):
                continue
            
            # Skip images that don't have proper file extensions
            if not any(ext in img_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                continue
            
            score = is_character_portrait(img_src, character_name, img)
            if score > 0:
                candidate_images.append((img_src, score))
                logger.debug(f"    Fallback candidate: {img_src} (score: {score})")
    
    # Sort by score (highest first)
    candidate_images.sort(key=lambda x: x[1], reverse=True)
    
    logger.info(f"  Found {len(candidate_images)} candidate images after filtering")
    if candidate_images:
        logger.info(f"  Top candidate: {candidate_images[0][0]} (score: {candidate_images[0][1]})")
    
    return candidate_images

def download_character_images():
    """Download character portrait images from the Steal a Brainrot Wiki."""
    base_url = "https://stealabrainrot.fandom.com"
    images_dir = "images"
    
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    # Use the correct CSV filename
    csv_filename = 'steal_a_brainrot_complete_database.csv'
    if not os.path.exists(csv_filename):
        logger.error(f"CSV file not found: {csv_filename}")
        return
    
    with open(csv_filename, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            character_name = row['Character Name'].strip('"')
            
            if character_has_existing_images(character_name, images_dir):
                logger.info(f"Skipping {character_name} - images already exist")
                continue
                
            logger.info(f"Searching for images of: {character_name}")
            
            try:
                # Try direct wiki page first (try different case variations)
                page_found = False
                page_response = None
                
                # Try different case variations of the character name
                name_variations = [
                    character_name,
                    character_name.lower(),
                    character_name.title(),
                    character_name.capitalize()
                ]
                
                for name_variant in name_variations:
                    character_page_url = f"{base_url}/wiki/{name_variant.replace(' ', '_')}"
                    logger.info(f"  Trying page: {character_page_url}")
                    
                    page_response = requests.get(character_page_url)
                    if page_response.status_code == 200:
                        logger.info(f"  Found page with variant: {name_variant}")
                        page_found = True
                        break
                
                # If direct page doesn't exist with any variation, try search
                if not page_found:
                    logger.info(f"  Direct page not found, trying search...")
                    
                    search_url = f"{base_url}/wiki/Special:Search"
                    search_params = {
                        'query': character_name,
                        'scope': 'internal',
                        'navigationSearch': 'true'
                    }
                    
                    search_response = requests.get(search_url, params=search_params)
                    search_response.raise_for_status()
                    
                    search_soup = BeautifulSoup(search_response.content, 'html.parser')
                    
                    # Look for the character page in search results
                    character_page_link = None
                    search_results = search_soup.find_all('a', href=True)
                    
                    for link in search_results:
                        link_text = link.get_text().lower()
                        if character_name.lower() in link_text:
                            href = link['href']
                            if href.startswith('/wiki/') and 'Special:' not in href:
                                character_page_link = urljoin(base_url, href)
                                logger.info(f"  Found search result: {character_page_link}")
                                break
                    
                    if not character_page_link:
                        logger.warning(f"  No wiki page found for {character_name}")
                        continue
                    
                    page_response = requests.get(character_page_link)
                
                page_response.raise_for_status()
                page_soup = BeautifulSoup(page_response.content, 'html.parser')
                
                # Find candidate character portrait images
                candidate_images = find_character_portrait_images(page_soup, character_name)
                
                if not candidate_images:
                    logger.warning(f"  No suitable images found for {character_name}")
                    continue
                
                logger.info(f"  Found {len(candidate_images)} candidate images")
                
                downloaded_count = 0
                max_downloads = 1  # ONLY download the single best match (main character image)
                
                # Only download the top candidate - no backups or alternatives
                logger.info(f"  Downloading only the top candidate (main character image)")
                
                for img_src, score in candidate_images[:max_downloads]:
                    try:
                        original_img_src = get_original_image_url(img_src)
                        logger.info(f"  Trying image (score: {score}): {original_img_src}")
                        
                        img_response = requests.get(original_img_src, timeout=30)
                        img_response.raise_for_status()
                        
                        # Validate image
                        try:
                            img = Image.open(BytesIO(img_response.content))
                            width, height = img.size
                            
                            # Skip very small images (likely thumbnails or icons)
                            if width < 150 or height < 150:
                                logger.info(f"  Skipping small image: {width}x{height}")
                                continue
                            
                            # For subsequent downloads, require better quality
                            if downloaded_count > 0:
                                if width < 300 or height < 300:
                                    logger.info(f"  Skipping lower quality backup: {width}x{height}")
                                    continue
                                # Also require higher score for backups
                                if score < 100:
                                    logger.info(f"  Skipping low-scoring backup: score {score}")
                                    continue
                            
                            # Check aspect ratio - avoid very wide or very tall images
                            aspect_ratio = width / height
                            if aspect_ratio > 3.0 or aspect_ratio < 0.33:
                                logger.info(f"  Skipping image with unusual aspect ratio: {aspect_ratio:.2f}")
                                continue
                            
                            logger.info(f"  Valid image found: {width}x{height}, aspect ratio: {aspect_ratio:.2f}")
                            
                        except Exception as e:
                            logger.warning(f"  Could not validate image: {e}")
                            continue
                        
                        # Generate filename
                        clean_name = clean_filename(character_name)
                        
                        # Determine file extension from content type or URL
                        content_type = img_response.headers.get('content-type', '').lower()
                        if 'png' in content_type or '.png' in original_img_src.lower():
                            ext = '.png'
                        elif 'jpeg' in content_type or 'jpg' in content_type or '.jpg' in original_img_src.lower() or '.jpeg' in original_img_src.lower():
                            ext = '.jpg'
                        elif 'gif' in content_type or '.gif' in original_img_src.lower():
                            ext = '.gif'
                        elif 'webp' in content_type or '.webp' in original_img_src.lower():
                            ext = '.webp'
                        else:
                            # Try to detect from image format
                            try:
                                img_format = img.format.lower() if img.format else 'png'
                                if img_format == 'jpeg':
                                    ext = '.jpg'
                                else:
                                    ext = f'.{img_format}'
                            except:
                                ext = '.png'  # Default to PNG
                        
                        # Create filename with priority indicator
                        if downloaded_count == 0:
                            filename = f"{clean_name}{ext}"  # Primary image gets clean name
                        else:
                            filename = f"{clean_name}_alt{ext}"  # Alternative image
                        
                        filepath = os.path.join(images_dir, filename)
                        
                        # Save the image
                        with open(filepath, 'wb') as f:
                            f.write(img_response.content)
                        
                        logger.info(f"  Downloaded: {filename} ({width}x{height}, score: {score})")
                        downloaded_count += 1
                        
                        # Always stop after downloading the first (best) image
                        logger.info(f"  Downloaded primary image, stopping")
                        break
                        
                    except Exception as e:
                        logger.warning(f"  Failed to download image {img_src}: {e}")
                        continue
                
                if downloaded_count == 0:
                    logger.warning(f"  No images successfully downloaded for {character_name}")
                else:
                    logger.info(f"  Successfully downloaded {downloaded_count} images for {character_name}")
                
                # Rate limiting
                time.sleep(2)  # Be respectful to the server
                
            except Exception as e:
                logger.error(f"Error processing {character_name}: {e}")
                continue

if __name__ == "__main__":
    print("Starting image download from Steal a Brainrot Wiki...")
    download_character_images()
    print("Download complete!")