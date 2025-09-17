import requests
from bs4 import BeautifulSoup

# Check Gangster Footera page structure
url = "https://stealabrainrot.fandom.com/wiki/Gangster_Footera"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

print("Looking for all figure elements:")
figures = soup.find_all('figure')
for i, figure in enumerate(figures):
    print(f"Figure {i+1}:")
    print(f"  Classes: {figure.get('class')}")
    print(f"  Data-attrs: {figure.get('data-attrs') is not None}")
    if figure.get('data-attrs'):
        data_attrs = figure.get('data-attrs')
        if 'King_von.png' in data_attrs:
            print(f"  *** CONTAINS King_von.png ***")
            print(f"  Data-attrs snippet: {data_attrs[:200]}...")
    print()

print("\nLooking for pi-hero elements:")
pi_elements = soup.find_all(class_=lambda x: x and 'pi-hero' in ' '.join(x))
for i, elem in enumerate(pi_elements):
    print(f"Pi-hero {i+1}: {elem.name} with classes {elem.get('class')}")

print("\nLooking for any element with 'hero' in class:")
hero_elements = soup.find_all(class_=lambda x: x and 'hero' in ' '.join(x).lower())
for i, elem in enumerate(hero_elements):
    print(f"Hero {i+1}: {elem.name} with classes {elem.get('class')}")
    if elem.name == 'figure':
        print(f"  *** This is a figure! ***")