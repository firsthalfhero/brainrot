#!/usr/bin/env python3
"""
Demonstration script for the CharacterDataExtractor.

This script shows how to use the CharacterDataExtractor to extract character data
from the Steal a Brainrot wiki. It includes examples of successful extraction,
error handling, and URL discovery.
"""

import logging
from card_generator.character_data_extractor import CharacterDataExtractor
from card_generator.config import DatabaseBuilderConfig

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def demo_url_variations():
    """Demonstrate URL variation generation."""
    print("=" * 60)
    print("DEMO: URL Variation Generation")
    print("=" * 60)
    
    extractor = CharacterDataExtractor()
    
    test_names = [
        "Fluriflura",
        "Brr Brr Patapim", 
        "Test-Character!",
        "Character With Spaces"
    ]
    
    for name in test_names:
        print(f"\nURL variations for '{name}':")
        variations = extractor._generate_url_variations(name)
        for i, url in enumerate(variations, 1):
            print(f"  {i}. {url}")
    
    extractor.close()

def demo_numeric_parsing():
    """Demonstrate numeric value parsing."""
    print("\n" + "=" * 60)
    print("DEMO: Numeric Value Parsing")
    print("=" * 60)
    
    extractor = CharacterDataExtractor()
    
    test_values = [
        "100",
        "1,500",
        "2.5k",
        "Cost: 500 coins",
        "Income: $1,200 per second",
        "Price: 3.5k",
        "No numbers here",
        "Mixed 123 text 456",
        "10k income"
    ]
    
    for value in test_values:
        parsed = extractor._parse_numeric_value(value)
        print(f"'{value}' -> {parsed}")
    
    extractor.close()

def demo_mock_extraction():
    """Demonstrate character data extraction with mock data."""
    print("\n" + "=" * 60)
    print("DEMO: Mock Character Data Extraction")
    print("=" * 60)
    
    from bs4 import BeautifulSoup
    
    extractor = CharacterDataExtractor()
    
    # Mock HTML with complete infobox
    html = """
    <html>
        <body>
            <table class="infobox">
                <tr>
                    <td colspan="2">
                        <figure class="pi-item pi-image">
                            <img src="/images/demo_character.png" alt="Demo Character">
                        </figure>
                    </td>
                </tr>
                <tr>
                    <td>Cost</td>
                    <td>2,500</td>
                </tr>
                <tr>
                    <td>Income per second</td>
                    <td>125</td>
                </tr>
            </table>
        </body>
    </html>
    """
    
    soup = BeautifulSoup(html, 'html.parser')
    data = extractor._extract_infobox_data(soup)
    
    print("Extracted infobox data:")
    print(f"  Cost: {data['cost']}")
    print(f"  Income: {data['income']}")
    print(f"  Image URL: {data['image_url']}")
    print(f"  Errors: {data['errors']}")
    
    extractor.close()

def demo_configuration():
    """Demonstrate database builder configuration."""
    print("\n" + "=" * 60)
    print("DEMO: Database Builder Configuration")
    print("=" * 60)
    
    # Create configuration
    config = DatabaseBuilderConfig(
        rate_limit_delay=1.0,  # Faster for demo
        max_retries=2,
        timeout=15
    )
    
    print("Database Builder Configuration:")
    print(f"  Base URL: {config.base_url}")
    print(f"  Brainrots Page: {config.full_brainrots_url}")
    print(f"  Output Directory: {config.output_dir}")
    print(f"  Images Directory: {config.images_dir}")
    print(f"  Rate Limit Delay: {config.rate_limit_delay}s")
    print(f"  Max Retries: {config.max_retries}")
    print(f"  Timeout: {config.timeout}s")
    print(f"  Request Headers: {config.request_headers}")
    
    # Demonstrate retry delay calculation
    print("\nRetry delay progression:")
    for attempt in range(4):
        delay = config.get_retry_delay(attempt)
        print(f"  Attempt {attempt}: {delay:.1f}s")

def main():
    """Run all demonstrations."""
    print("CharacterDataExtractor Demonstration")
    print("This script demonstrates the functionality without making real HTTP requests.")
    
    try:
        demo_url_variations()
        demo_numeric_parsing()
        demo_mock_extraction()
        demo_configuration()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\nThe CharacterDataExtractor is ready for use!")
        print("To test with real wiki pages, run the integration tests:")
        print("  python -m unittest tests.test_character_data_extractor_integration")
        print("\nRemember to uncomment the @unittest.skip decorators first.")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()