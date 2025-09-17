# Trading Card Generator

A comprehensive Python application that generates printable A5 trading cards from Brainrot character data. The system processes character information from CSV files, matches them with downloaded character images, and creates professional-quality trading cards suitable for printing.

## Features

- **Data Processing**: Loads character data from CSV files with validation and error handling
- **Image Management**: Processes character images with smart resizing, cropping, and placeholder generation
- **Card Generation**: Creates A5-sized trading cards with character images, stats, and tier-based styling
- **Print Layout**: Arranges cards on A4 sheets for efficient printing with cut guides
- **Multi-format Output**: Supports PNG and PDF output formats
- **Flexible Configuration**: Customizable card dimensions, print layouts, and styling options
- **Selective Generation**: Generate cards for specific characters, tiers, or cost ranges
- **Image Downloading**: Automated character image scraping from Fandom wiki

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install pillow requests beautifulsoup4 psutil
   ```

2. **Ensure you have the character database**: `steal_a_brainrot_complete_database.csv`

3. **Download character images** (optional):
   ```bash
   python download_images.py
   ```

4. **Generate cards**:
   ```bash
   python main.py
   ```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Required Dependencies
```bash
pip install pillow requests beautifulsoup4
```

### Optional Dependencies (for performance testing)
```bash
pip install psutil
```

### Verify Installation
```bash
python -c "import PIL; print('Pillow installed successfully')"
python -c "import requests; print('Requests installed successfully')"
```

## Usage

### Basic Usage

Generate cards for all characters:
```bash
python main.py
```

Or use the basic example script:
```bash
python examples/basic_usage.py
```

### Advanced Usage

#### Selective Generation
Generate cards for specific characters or tiers:
```bash
python examples/selective_generation.py
```

#### Custom Configuration
Use different quality settings and layouts:
```bash
python examples/custom_configuration.py
```

#### Command Line Interface
Use the CLI for more control:
```bash
python -m card_generator.cli --help
python -m card_generator.cli --tier Legendary --output legendary_cards
python -m card_generator.cli --characters "Matteo,Tim Cheese" --high-quality
```

### Image Management

#### Download All Character Images
```bash
python download_images.py
```

#### Download Specific Character
```bash
python test_single.py
```

## Configuration

The system uses dataclass-based configuration for easy customization:

### Card Configuration
```python
from card_generator.config import CardConfig

# High-quality configuration
high_quality = CardConfig(
    width=2480,   # A5 at 420 DPI
    height=3508,
    dpi=420,
    margin=80,
    image_ratio=0.65
)

# Draft configuration
draft = CardConfig(
    width=874,    # A5 at 150 DPI
    height=1240,
    dpi=150,
    margin=25
)
```

### Print Configuration
```python
from card_generator.config import PrintConfig

# Standard layout (2 cards per sheet)
standard = PrintConfig(
    cards_per_sheet=2,
    margin=50
)

# Compact layout (4 cards per sheet)
compact = PrintConfig(
    cards_per_sheet=4,
    margin=30
)
```

### Output Configuration
```python
from card_generator.config import OutputConfig

config = OutputConfig(
    individual_cards_dir='output/cards',
    print_sheets_dir='output/sheets',
    formats=['PNG', 'PDF']
)
```

## Project Structure

```
trading-card-generator/
├── card_generator/              # Main package
│   ├── __init__.py             # Package exports
│   ├── config.py               # Configuration classes
│   ├── data_models.py          # Data structures
│   ├── data_loader.py          # CSV loading logic
│   ├── image_processor.py      # Image processing
│   ├── card_designer.py        # Card layout generation
│   ├── print_layout.py         # Print sheet arrangement
│   ├── output_manager.py       # File output handling
│   ├── character_selector.py   # Character filtering
│   ├── cli.py                  # Command line interface
│   └── error_handling.py       # Error handling utilities
├── examples/                   # Usage examples
│   ├── basic_usage.py          # Simple card generation
│   ├── selective_generation.py # Filtered generation
│   ├── custom_configuration.py # Custom settings
│   └── README.md               # Examples documentation
├── tests/                      # Comprehensive test suite
│   ├── test_*.py               # Unit tests
│   ├── test_*_integration.py   # Integration tests
│   ├── test_comprehensive_integration.py  # Full workflow tests
│   └── test_performance.py     # Performance benchmarks
├── images/                     # Character images directory
├── output/                     # Generated cards and sheets
├── main.py                     # Application entry point
├── download_images.py          # Image scraping script
├── steal_a_brainrot_complete_database.csv  # Character data
└── README.md                   # This file
```

## Character Data

Character data comes from `steal_a_brainrot_complete_database.csv` with fields:
- **Character Name**: Display name for the card
- **Tier**: Rarity level (Common, Rare, Epic, Legendary, Mythic, Divine, Celestial, OG)
- **Cost**: Purchase cost in game currency
- **Income per Second**: Revenue generation rate
- **Variant Type**: Standard or Special variant

### Tier Colors
- **Common**: Gray (#808080)
- **Rare**: Blue (#4169E1)
- **Epic**: Purple (#8A2BE2)
- **Legendary**: Orange (#FF8C00)
- **Mythic**: Red (#DC143C)
- **Divine**: Gold (#FFD700)
- **Celestial**: Cyan (#00FFFF)
- **OG**: Rainbow gradient

## Output

### Generated Files
- **Individual cards**: `output/individual_cards/` - PNG files for each character
- **Print sheets**: `output/print_sheets/` - A4 sheets with multiple cards for printing

### File Naming
- Individual cards: `{Character_Name}_{Tier}_card.png`
- Print sheets: `print_sheet_{number:03d}.png`

### Print Specifications
- **Card Size**: A5 (148mm × 210mm) at 300 DPI (1748 × 2480 pixels)
- **Sheet Size**: A4 (210mm × 297mm) at 300 DPI (2480 × 3508 pixels)
- **Layout**: 2 cards per A4 sheet in landscape orientation
- **Cut Guides**: Included for precise cutting

## Testing

### Run All Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Run Specific Test Categories
```bash
# Unit tests
python -m unittest tests.test_data_loader
python -m unittest tests.test_image_processor
python -m unittest tests.test_card_designer

# Integration tests
python -m unittest tests.test_comprehensive_integration
python -m unittest tests.test_main_integration

# Performance tests (requires psutil)
python -m unittest tests.test_performance
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: Complete workflow testing with real data
- **Performance Tests**: Memory usage and processing speed benchmarks
- **Error Handling Tests**: Graceful failure scenarios

## Examples

See the `examples/` directory for detailed usage examples:

1. **Basic Usage** (`examples/basic_usage.py`): Generate all cards with default settings
2. **Selective Generation** (`examples/selective_generation.py`): Filter by tier, name, or cost
3. **Custom Configuration** (`examples/custom_configuration.py`): Different quality and layout options

Each example includes detailed comments and error handling.

## Image Downloading

The system includes automated image downloading from the Steal a Brainrot Fandom Wiki:

### Download All Character Images
```bash
python download_images.py
```

### Download Specific Characters
```bash
python test_single.py
```

### Image Quality Features
- Only downloads high-quality images (≥500x500 pixels)
- Skips site logos and thumbnails
- Supports PNG, JPG, GIF, and WebP formats
- Includes rate limiting to respect server resources

### File Naming Convention
Downloaded images are saved as: `{character_name}_{number}.{extension}`

Examples:
- `Trippi Troppi_1.png`
- `Noobini Pizzanini_2.jpg`

## Troubleshooting

### Common Issues

#### Missing CSV File
```
Error: CSV file 'steal_a_brainrot_complete_database.csv' not found!
```
**Solution**: Ensure the CSV file is in the project root directory.

#### Missing Images
Cards will be generated with placeholder images if character images are not found. To download images:
```bash
python download_images.py
```

#### Memory Issues
For large batches, use the draft configuration or process characters in smaller groups:
```python
draft_config = CardConfig(dpi=150)  # Lower DPI for less memory usage
```

#### Permission Errors
Ensure the output directory is writable:
```bash
mkdir -p output/individual_cards output/print_sheets
chmod 755 output output/individual_cards output/print_sheets
```

#### Network Errors (Image Downloading)
```
Failed to download image: 503 Server Error
```
**Solution**: The wiki server may be temporarily unavailable. Wait and try again.

### Performance Optimization

- Use draft configuration (150 DPI) for previews
- Process characters in batches for large datasets
- Close image files explicitly in custom scripts
- Monitor memory usage with performance tests

### Getting Help

1. Check the examples in the `examples/` directory
2. Run the test suite to verify installation
3. Review error messages for specific guidance
4. Check file permissions and disk space

## Development

### Adding New Features
1. Create feature branch
2. Add unit tests
3. Update integration tests
4. Add example usage
5. Update documentation

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings (Google style)
- Include error handling
- Write comprehensive tests

### Testing New Features
```bash
# Run specific tests
python -m unittest tests.test_your_feature

# Run integration tests
python -m unittest tests.test_comprehensive_integration

# Run performance tests
python -m unittest tests.test_performance
```

## Legal Notice

The image downloading functionality is for educational purposes. Please respect the Fandom wiki's terms of service and robots.txt file. Use reasonable delays between requests to avoid overloading their servers.

## Contributing

Feel free to submit issues or pull requests to improve the system's functionality or add new features. Please include tests for any new functionality.