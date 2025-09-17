# Trading Card Generator Examples

This directory contains example scripts demonstrating different ways to use the Trading Card Generator.

## Examples Overview

### 1. Basic Usage (`basic_usage.py`)
Demonstrates the simplest way to generate cards for all characters in the database.

**Features:**
- Loads all characters from the CSV file
- Generates cards with default settings
- Creates both individual cards and print sheets
- Handles missing images gracefully

**Usage:**
```bash
python examples/basic_usage.py
```

### 2. Selective Generation (`selective_generation.py`)
Shows how to generate cards for specific subsets of characters.

**Features:**
- Filter by tier (Common, Rare, Epic, etc.)
- Filter by specific character names
- Filter by cost range
- Generate cards for multiple tiers

**Usage:**
```bash
python examples/selective_generation.py
```

### 3. Custom Configuration (`custom_configuration.py`)
Demonstrates using different configurations for various output needs.

**Features:**
- High-quality configuration (420 DPI)
- Draft configuration (150 DPI)
- Compact print layout (4 cards per sheet)
- Custom colors and styling

**Usage:**
```bash
python examples/custom_configuration.py
```

## Prerequisites

Before running the examples, ensure you have:

1. **Character Database**: The `steal_a_brainrot_complete_database.csv` file in the project root
2. **Python Dependencies**: All required packages installed (see main README)
3. **Images Directory**: Optional `images/` directory with character images (examples work with placeholders if missing)

## Output Structure

Each example creates its own output directory:

- `basic_usage.py` → `output/`
- `selective_generation.py` → `output_selective/`
- `custom_configuration.py` → `output_custom/`

Each output directory contains:
- `individual_cards/` - Individual card PNG files
- `print_sheets/` - Print-ready A4 sheets with multiple cards

## Running Examples

From the project root directory:

```bash
# Basic usage - generate all cards
python examples/basic_usage.py

# Selective generation - generate specific cards
python examples/selective_generation.py

# Custom configuration - different quality settings
python examples/custom_configuration.py
```

## Customizing Examples

You can modify the examples to suit your needs:

### Changing Output Directory
```python
output_dir = 'my_custom_output'
```

### Filtering Characters
```python
# Filter by tier
legendary_chars = [c for c in characters if c.tier == 'Legendary']

# Filter by name pattern
pizza_chars = [c for c in characters if 'pizza' in c.name.lower()]

# Filter by cost
expensive_chars = [c for c in characters if c.cost > 10000]
```

### Custom Card Configuration
```python
custom_config = CardConfig(
    width=2000,           # Custom width
    height=2800,          # Custom height
    dpi=350,              # Custom DPI
    background_color='#F0F0F0',  # Light gray background
    margin=50,            # Custom margin
    image_ratio=0.7       # 70% of card for image
)
```

### Custom Print Configuration
```python
custom_print = PrintConfig(
    cards_per_sheet=6,    # 6 cards per sheet
    margin=20,            # Smaller margins
    cut_guide_color='#FF0000'  # Red cut guides
)
```

## Error Handling

All examples include error handling for common issues:

- Missing CSV file
- Missing images directory
- Corrupted character data
- File permission errors
- Disk space issues

Check the console output for detailed error messages and progress information.

## Performance Notes

- **High-quality configuration**: Slower but better for professional printing
- **Draft configuration**: Faster processing, good for previews
- **Batch processing**: Process characters in smaller batches if memory is limited
- **Image caching**: Images are processed fresh each time (no caching in examples)

## Next Steps

After running the examples:

1. **Review Output**: Check the generated cards and print sheets
2. **Test Printing**: Print a sample sheet to verify quality and alignment
3. **Customize Settings**: Adjust configurations based on your printing needs
4. **Create Your Own**: Use the examples as templates for your specific requirements