from download_images import find_character_portrait_images
import requests
from bs4 import BeautifulSoup

response = requests.get('https://stealabrainrot.fandom.com/wiki/Fluriflura')
soup = BeautifulSoup(response.content, 'html.parser')
candidates = find_character_portrait_images(soup, 'Fluriflura')

print(f'Found {len(candidates)} candidates:')
for i, (url, score) in enumerate(candidates[:5]):
    filename = url.split('/')[-1].split('?')[0]
    if '/revision/' in url:
        # Extract filename before /revision/
        parts = url.split('/')
        for j, part in enumerate(parts):
            if part == 'revision' and j > 0:
                filename = parts[j-1]
                break
    print(f'{i+1}. Score {score}: {filename}')
    print(f'   URL: {url}')