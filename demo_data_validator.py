#!/usr/bin/env python3
"""
Demo script for the DataValidator functionality.

This script demonstrates the data validation and quality assurance features
implemented for the database builder.
"""

import logging
from datetime import datetime
from card_generator.data_validator import DataValidator
from card_generator.data_models import CharacterData

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def create_test_character(name, tier, cost, income, variant, **kwargs):
    """Create a test character bypassing validation for demo purposes."""
    char = CharacterData.__new__(CharacterData)
    char.name = name
    char.tier = tier
    char.cost = cost
    char.income = income
    char.variant = variant
    char.image_path = kwargs.get('image_path')
    char.wiki_url = kwargs.get('wiki_url')
    char.image_url = kwargs.get('image_url')
    char.extraction_timestamp = kwargs.get('extraction_timestamp')
    char.extraction_success = kwargs.get('extraction_success', True)
    char.extraction_errors = kwargs.get('extraction_errors', [])
    return char

def main():
    """Main demo function."""
    print("=== Data Validator Demo ===\n")
    
    # Create validator instances
    validator = DataValidator(strict_mode=False, timeout=5)
    strict_validator = DataValidator(strict_mode=True, timeout=5)
    
    try:
        # Create sample character data with various issues
        test_characters = [
            # Valid character
            CharacterData("Fluriflura", "Common", 100, 5, "Standard"),
            
            # Character with name normalization needed
            CharacterData("  Test   Character  ", "rare", 200, 10, "standard"),
            
            # Character with numeric issues (bypass validation for demo)
            create_test_character("Expensive Character", "Legendary", -50, 2000000, "Special"),
            
            # Character with invalid tier
            create_test_character("Unknown Tier Character", "SuperRare", 300, 15, "Standard"),
            
            # Duplicate character
            CharacterData("Fluriflura", "Common", 100, 5, "Standard"),
            
            # Similar character (potential duplicate)
            CharacterData("Fluriflora", "Common", 100, 5, "Standard"),
            
            # Character with problematic name
            create_test_character("Character@#$%", "Epic", 500, 25, "Standard"),
            
            # Character with suspicious values
            CharacterData("Minimal Character", "Common", 0, 0, "Standard"),
        ]
        
        print(f"Created {len(test_characters)} test characters with various issues\n")
        
        # Test comprehensive validation
        print("=== Comprehensive Validation (Non-Strict Mode) ===")
        result = validator.validate_character_list(test_characters)
        
        print(f"Validation Result:")
        print(f"  Valid: {result.is_valid}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Warnings: {len(result.warnings)}")
        print(f"  Characters processed: {len(result.normalized_data) if result.normalized_data else 0}")
        
        if result.errors:
            print(f"\nErrors found:")
            for i, error in enumerate(result.errors[:3], 1):  # Show first 3 errors
                print(f"  {i}. {error}")
            if len(result.errors) > 3:
                print(f"  ... and {len(result.errors) - 3} more errors")
        
        if result.warnings:
            print(f"\nWarnings found:")
            for i, warning in enumerate(result.warnings[:5], 1):  # Show first 5 warnings
                print(f"  {i}. {warning}")
            if len(result.warnings) > 5:
                print(f"  ... and {len(result.warnings) - 5} more warnings")
        
        # Show duplicate information
        duplicates = result.metadata.get('duplicate_info', [])
        if duplicates:
            print(f"\nDuplicates found: {len(duplicates)} groups")
            for i, dup in enumerate(duplicates, 1):
                char_names = [test_characters[idx].name for idx in [dup.original_index] + dup.duplicate_indices]
                print(f"  Group {i} ({dup.duplicate_type}): {', '.join(char_names)}")
        
        # Show some normalization examples
        if result.normalized_data:
            print(f"\nNormalization Examples:")
            for i, (original, normalized) in enumerate(zip(test_characters[:3], result.normalized_data[:3])):
                changes = []
                if original.name != normalized.name:
                    changes.append(f"name: '{original.name}' -> '{normalized.name}'")
                if original.tier != normalized.tier:
                    changes.append(f"tier: '{original.tier}' -> '{normalized.tier}'")
                if original.cost != normalized.cost:
                    changes.append(f"cost: {original.cost} -> {normalized.cost}")
                if original.income != normalized.income:
                    changes.append(f"income: {original.income} -> {normalized.income}")
                if original.variant != normalized.variant:
                    changes.append(f"variant: '{original.variant}' -> '{normalized.variant}'")
                
                if changes:
                    print(f"  Character {i+1}: {', '.join(changes)}")
        
        # Test strict mode comparison
        print(f"\n=== Strict Mode Comparison ===")
        strict_result = strict_validator.validate_character_list(test_characters)
        
        print(f"Non-strict mode: {len(result.errors)} errors, {len(result.warnings)} warnings")
        print(f"Strict mode: {len(strict_result.errors)} errors, {len(strict_result.warnings)} warnings")
        
        # Test individual validation features
        print(f"\n=== Individual Validation Features ===")
        
        # Name validation
        print("Name Validation:")
        name_tests = ["Valid Name", "  Spaced Name  ", "Name@#$%", "a" * 60, ""]
        for name in name_tests:
            name_result = validator.validate_and_normalize_name(name)
            status = "✓" if name_result.is_valid else "✗"
            normalized = f" -> '{name_result.normalized_data}'" if name_result.normalized_data else ""
            print(f"  {status} '{name}'{normalized}")
        
        # Tier validation
        print("\nTier Validation:")
        tier_tests = ["Common", "common", "RARE", "brainrot god", "InvalidTier"]
        for tier in tier_tests:
            tier_result = validator.validate_tier(tier)
            status = "✓" if tier_result.is_valid else "✗"
            normalized = f" -> '{tier_result.normalized_data}'" if tier_result.normalized_data else ""
            print(f"  {status} '{tier}'{normalized}")
        
        # Numeric validation
        print("\nNumeric Validation:")
        numeric_tests = [(100, "cost"), (-50, "cost"), (2000000, "income"), (0, "income")]
        for value, field in numeric_tests:
            numeric_result = validator.validate_numeric_field(value, field)
            status = "✓" if numeric_result.is_valid else "✗"
            normalized = f" -> {numeric_result.normalized_data}" if numeric_result.normalized_data is not None else ""
            print(f"  {status} {field}={value}{normalized}")
        
        # Get validation statistics
        print(f"\n=== Validation Statistics ===")
        stats = validator.get_validation_statistics()
        validation_stats = stats['validation_stats']
        
        print(f"Total validated: {validation_stats['total_validated']}")
        print(f"Names normalized: {validation_stats['names_normalized']}")
        print(f"Numeric corrections: {validation_stats['numeric_corrections']}")
        print(f"URL validations: {validation_stats['url_validations']}")
        print(f"Duplicates found: {validation_stats['duplicates_found']}")
        
        cache_stats = stats['cache_stats']
        print(f"URL cache size: {cache_stats['url_cache_size']}")
        
        print(f"\n=== Demo Complete ===")
        print("The DataValidator successfully demonstrated:")
        print("✓ Character name normalization and validation")
        print("✓ Numeric data validation and correction")
        print("✓ Tier and variant validation")
        print("✓ Duplicate detection")
        print("✓ Comprehensive error and warning reporting")
        print("✓ Data normalization and quality assurance")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        validator.close()
        strict_validator.close()

if __name__ == "__main__":
    main()