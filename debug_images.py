import requests
from bs4 import BeautifulSoup

response = requests.get('https://stealabrainrot.fandom.com/wiki/Fluriflura')
soup = BeautifulSoup(response.content, 'html.parser')
images = soup.find_all('img')

print(f'Total images: {len(images)}')
for i, img in enumerate(images[:10]):
    src = img.get('src') or img.get('data-src')
    print(f'  {i+1}. {src}')
    if 'static.wikia.nocookie.net' in (src or ''):
        print(f'      ^ This is a wikia image')