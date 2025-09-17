from download_images import find_character_portrait_images
import requests
from bs4 import BeautifulSoup

# Test the problematic characters
test_cases = [
    ("Graipuss Medussi", "https://stealabrainrot.fandom.com/wiki/Graipuss_Medussi"),
    ("Gangster Footera", "https://stealabrainrot.fandom.com/wiki/Gangster_Footera")
]

for character_name, url in test_cases:
    print(f"\n{'='*60}")
    print(f"Testing: {character_name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find infobox figures first
        infobox_figures = soup.find_all('figure', class_=lambda x: x and any(
            cls in ' '.join(x).lower() for cls in ['pi-hero', 'pi-image', 'infobox', 'portable-infobox']
        ))
        
        print(f"Infobox figures found: {len(infobox_figures)}")
        for i, figure in enumerate(infobox_figures):
            print(f"  Figure {i+1}: {figure.get('class')}")
            data_attrs = figure.get('data-attrs')
            if data_attrs:
                print(f"    Has data-attrs: {len(data_attrs)} chars")
                # Try to extract URL from data-attrs
                if '"url"' in data_attrs:
                    start = data_attrs.find('"url":"') + 7
                    end = data_attrs.find('"', start)
                    if start > 6 and end > start:
                        url_in_attrs = data_attrs[start:end].replace('\\/', '/')
                        print(f"    URL in data-attrs: {url_in_attrs}")
        
        # Test the improved function
        candidates = find_character_portrait_images(soup, character_name)
        
        print(f"\nCandidates found: {len(candidates)}")
        for i, (img_url, score) in enumerate(candidates[:3]):
            filename = img_url.split('/')[-1].split('?')[0]
            if '/revision/' in img_url:
                parts = img_url.split('/')
                for j, part in enumerate(parts):
                    if part == 'revision' and j > 0:
                        filename = parts[j-1]
                        break
            print(f"  {i+1}. Score {score}: {filename}")
            print(f"     URL: {img_url}")
        
    except Exception as e:
        print(f"Error testing {character_name}: {e}")