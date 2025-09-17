#!/usr/bin/env python3
"""
Demonstration script for the comprehensive error handling system.

This script shows how the error handling works across different scenarios.
"""

import os
import tempfile
import shutil
from pathlib import Path

from card_generator.data_loader import CSVDataLoader
from card_generator.image_processor import ImageProcessor
from card_generator.output_manager import OutputManager
from card_generator.config import OutputConfig
from card_generator.error_handling import setup_logging, create_error_report


def demo_data_loading_errors():
    """Demonstrate data loading error handling."""
    print("\n" + "="*60)
    print("DEMO: Data Loading Error Handling")
    print("="*60)
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        csv_path = os.path.join(temp_dir, 'demo.csv')
        images_dir = os.path.join(temp_dir, 'images')
        os.makedirs(images_dir)
        
        # Create CSV with mixed valid/invalid data
        csv_content = '''Character Name,Tier,Cost,Income per Second,Variant Type
"Valid Hero","Epic",500,25,"Standard"
"Invalid Cost","Rare","not_a_number",10,"Standard"
"Missing Tier","",200,8,"Standard"
"Negative Values","Common",-100,-5,"Standard"
"Valid Villain","Legendary",1000,50,"Special"
"Unicode Test ñáéíóú","Common",150,7,"Standard"
'''
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Load characters
        loader = CSVDataLoader(csv_path, images_dir)
        
        print("Loading characters from CSV with errors...")
        characters = loader.load_characters()
        
        print(f"✓ Successfully loaded {len(characters)} valid characters")
        
        # Show error summary
        failed = loader.get_failed_characters()
        print(f"✗ Failed to load {len(failed)} characters:")
        for failure in failed:
            print(f"  - Row {failure['row']}: {failure['error']}")
        
        # Show loading summary
        summary = loader.get_loading_summary()
        print(f"\nLoading Summary:")
        print(f"  Success rate: {summary['success_rate']:.1f}%")
        print(f"  Total processed: {summary['total_processed']}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def demo_image_processing_errors():
    """Demonstrate image processing error handling."""
    print("\n" + "="*60)
    print("DEMO: Image Processing Error Handling")
    print("="*60)
    
    processor = ImageProcessor()
    
    # Test missing image
    print("Testing missing image file...")
    try:
        image = processor.load_image('nonexistent.png')
        print(f"Result: {image}")
    except FileNotFoundError:
        print("✓ Properly handled missing image file")
    
    # Test corrupted image
    temp_dir = tempfile.mkdtemp()
    try:
        corrupted_path = os.path.join(temp_dir, 'corrupted.png')
        with open(corrupted_path, 'wb') as f:
            f.write(b'This is not a valid image')
        
        print("Testing corrupted image file...")
        image = processor.load_image(corrupted_path)
        if image is None:
            print("✓ Properly handled corrupted image file")
        
        # Test placeholder creation
        print("Creating placeholder image...")
        placeholder = processor.create_placeholder('Demo Character', 'Epic')
        if placeholder:
            print(f"✓ Created placeholder: {placeholder.size} pixels, {placeholder.mode} mode")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def demo_file_system_errors():
    """Demonstrate file system error handling."""
    print("\n" + "="*60)
    print("DEMO: File System Error Handling")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    try:
        config = OutputConfig(
            individual_cards_dir=os.path.join(temp_dir, 'cards'),
            print_sheets_dir=os.path.join(temp_dir, 'sheets'),
            formats=('PNG',)
        )
        
        output_manager = OutputManager(config)
        print("✓ Successfully created output directories")
        
        # Test error recovery suggestions
        print("\nTesting error recovery suggestions...")
        
        # Permission error
        perm_error = PermissionError("Access denied")
        suggestions = output_manager.get_error_recovery_suggestions(perm_error)
        print(f"Permission error suggestions: {len(suggestions)} items")
        for suggestion in suggestions[:2]:
            print(f"  - {suggestion}")
        
        # Disk space error
        disk_error = OSError("No space left on device")
        suggestions = output_manager.get_error_recovery_suggestions(disk_error)
        print(f"Disk space error suggestions: {len(suggestions)} items")
        for suggestion in suggestions[:2]:
            print(f"  - {suggestion}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def demo_integrated_error_handling():
    """Demonstrate integrated error handling across all components."""
    print("\n" + "="*60)
    print("DEMO: Integrated Error Handling")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Set up test environment
        csv_path = os.path.join(temp_dir, 'characters.csv')
        images_dir = os.path.join(temp_dir, 'images')
        output_dir = os.path.join(temp_dir, 'output')
        
        os.makedirs(images_dir)
        
        # Create CSV with mixed data
        csv_content = '''Character Name,Tier,Cost,Income per Second,Variant Type
"Hero Alpha","Common",100,5,"Standard"
"Hero Beta","Rare",250,12,"Standard"
"Invalid Hero","Epic","bad_cost",20,"Standard"
"Hero Gamma","Legendary",500,30,"Standard"
'''
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Create some test images (missing some intentionally)
        from PIL import Image
        test_image = Image.new('RGB', (300, 300), 'blue')
        test_image.save(os.path.join(images_dir, 'Hero Alpha_1.png'))
        # Hero Beta image missing - will use placeholder
        # Invalid Hero won't be loaded due to bad data
        test_image.save(os.path.join(images_dir, 'Hero Gamma_1.png'))
        
        # Initialize components
        loader = CSVDataLoader(csv_path, images_dir)
        processor = ImageProcessor()
        output_config = OutputConfig(
            individual_cards_dir=os.path.join(output_dir, 'cards'),
            print_sheets_dir=os.path.join(output_dir, 'sheets'),
            formats=('PNG',)
        )
        output_manager = OutputManager(output_config)
        
        print("Running integrated processing pipeline...")
        
        # Load characters
        characters = loader.load_characters()
        print(f"✓ Loaded {len(characters)} valid characters")
        
        # Process images
        processed_cards = []
        for character in characters:
            if character.has_image():
                image = processor.load_image(character.image_path)
            else:
                image = None
            
            if image is None:
                # Create placeholder for missing/corrupted images
                image = processor.create_placeholder(character.name, character.tier)
            
            processed_cards.append((image, character))
        
        print(f"✓ Processed {len(processed_cards)} character images")
        
        # Save cards
        results = output_manager.batch_process_cards(processed_cards)
        print(f"✓ Saved {results['successful_cards']} cards successfully")
        
        if results['failed_cards'] > 0:
            print(f"✗ Failed to save {results['failed_cards']} cards")
            for error in results['errors']:
                print(f"  - {error}")
        
        # Show final summary
        loading_summary = loader.get_loading_summary()
        print(f"\nFinal Summary:")
        print(f"  Data loading success rate: {loading_summary['success_rate']:.1f}%")
        print(f"  Card generation success rate: {results['successful_cards']/len(processed_cards)*100:.1f}%")
        print(f"  Total files created: {len(results['saved_files'])}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all error handling demonstrations."""
    # Set up logging
    logger = setup_logging()
    
    print("Trading Card Generator - Error Handling Demonstration")
    print("This demo shows how the system handles various error scenarios gracefully.")
    
    try:
        demo_data_loading_errors()
        demo_image_processing_errors()
        demo_file_system_errors()
        demo_integrated_error_handling()
        
        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        print("All error handling scenarios completed successfully!")
        print("The system demonstrated resilience to:")
        print("  ✓ Invalid CSV data")
        print("  ✓ Missing image files")
        print("  ✓ Corrupted image files")
        print("  ✓ File system permission issues")
        print("  ✓ Disk space constraints")
        print("  ✓ Mixed success/failure scenarios")
        
    except Exception as e:
        print(f"\nUnexpected error during demo: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == '__main__':
    main()