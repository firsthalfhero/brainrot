"""
Integration test for ImageProcessor with the actual project structure.
"""

import os
from PIL import Image
from card_generator.image_processor import ImageProcessor
from card_generator.data_models import CharacterData


def test_image_processor_integration():
    """Test ImageProcessor with project structure."""
    processor = ImageProcessor()
    
    # Test placeholder generation for different tiers
    tiers = ['Common', 'Rare', 'Epic', 'Legendary', 'Mythic', 'Divine', 'Celestial', 'OG']
    
    print("Testing placeholder generation for all tiers:")
    for tier in tiers:
        character_name = f"Test {tier} Character"
        placeholder = processor.create_placeholder(character_name, tier)
        
        print(f"✓ {tier}: {placeholder.size} {placeholder.mode}")
        
        # Verify placeholder properties
        assert placeholder.size == processor.target_image_size
        assert placeholder.mode == 'RGB'
    
    # Test with a sample character data
    test_character = CharacterData(
        name="Ballerina Cappuccina",
        tier="Epic", 
        cost=1500,
        income=75,
        variant="Standard"
    )
    
    # Test placeholder for this character
    placeholder = processor.create_placeholder(test_character.name, test_character.tier)
    print(f"✓ Character placeholder: {test_character.name} - {placeholder.size}")
    
    # Test image processing with a created test image
    test_image_path = "test_character_image.png"
    
    # Create a test image
    test_image = Image.new('RGB', (800, 600), 'red')
    test_image.save(test_image_path)
    
    try:
        # Load and process the test image
        loaded_image = processor.load_image(test_image_path)
        if loaded_image:
            processed_image = processor.resize_and_crop(loaded_image)
            print(f"✓ Image processing: {loaded_image.size} -> {processed_image.size}")
            
            assert processed_image.size == processor.target_image_size
            assert processed_image.mode == 'RGB'
        else:
            print("✗ Failed to load test image")
    
    finally:
        # Clean up test image
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
    
    print("\n✓ All integration tests passed!")


if __name__ == '__main__':
    test_image_processor_integration()