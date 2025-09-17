import requests
from bs4 import BeautifulSoup

# Check Gangster Footera page structure
url = "https://stealabrainrot.fandom.com/wiki/Gangster_Footera"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

print("Looking for pi-item pi-image figures:")
figures = soup.find_all('figure', class_=['pi-item', 'pi-image'])
for i, figure in enumerate(figures):
    print(f"Figure {i+1}:")
    print(f"  Classes: {figure.get('class')}")
    print(f"  Data-source: {figure.get('data-source')}")
    
    # Look for images in this figure
    imgs = figure.find_all('img')
    print(f"  Images found: {len(imgs)}")
    for j, img in enumerate(imgs):
        src = img.get('src') or img.get('data-src')
        alt = img.get('alt')
        print(f"    Image {j+1}: {src}")
        print(f"    Alt: {alt}")
        if 'King_von' in (src or '') or 'King_von' in (alt or ''):
            print(f"    *** CONTAINS King_von! ***")
    
    # Check for links
    links = figure.find_all('a')
    print(f"  Links found: {len(links)}")
    for j, link in enumerate(links):
        href = link.get('href')
        print(f"    Link {j+1}: {href}")
        if 'King_von' in (href or ''):
            print(f"    *** LINK CONTAINS King_von! ***")
    
    print(f"  Full HTML: {str(figure)[:300]}...")
    print()

# Also check for any element containing King_von
print("\nSearching for any element containing 'King_von':")
all_elements = soup.find_all(string=lambda text: text and 'King_von' in text)
print(f"Found {len(all_elements)} text elements containing 'King_von'")

# Search in attributes
king_von_elements = soup.find_all(attrs={'href': lambda x: x and 'King_von' in x})
print(f"Found {len(king_von_elements)} elements with href containing 'King_von'")
for elem in king_von_elements:
    print(f"  {elem.name}: {elem.get('href')}")
    print(f"  Parent: {elem.parent.name if elem.parent else 'None'}")
    if elem.parent and elem.parent.name == 'figure':
        print(f"  *** Parent is figure with classes: {elem.parent.get('class')} ***")