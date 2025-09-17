# Trading Card Generator Commands

Quick reference for generating trading cards from Brainrot character data.

## Basic Generation Commands

### Generate All Cards
```bash
python main.py --all
```
Generates cards for all characters in the database.

### Generate Specific Characters
```bash
python main.py --names "Tim Cheese" "FluriFlura"
```
Generate cards for specific character names.

### Generate by Tier
```bash
python main.py --tiers Common Rare Epic
```
Generate cards for specific tiers only.

### Generate with Pattern Matching
```bash
python main.py --name-pattern "*Cheese*"
```
Generate cards for characters matching a pattern (supports wildcards).

## Selection Filters

### Cost Range
```bash
python main.py --min-cost 100 --max-cost 1000
```

### Income Range
```bash
python main.py --min-income 50 --max-income 500
```

### Characters with Images Only
```bash
python main.py --all --with-images-only
```

### Characters without Images Only
```bash
python main.py --all --without-images-only
```

### Specific Variants
```bash
python main.py --variants Standard Special
```

## Output Format Options

### PNG Format (Default)
```bash
python main.py --all --format png
```

### PDF Format
```bash
python main.py --all --format pdf
```

### Both Formats
```bash
python main.py --all --format both
```

## Output Type Options

### Individual Cards Only
```bash
python main.py --all --individual-only
```

### Print Sheets Only
```bash
python main.py --all --print-sheets-only
```

### Both Individual and Print Sheets (Default)
```bash
python main.py --all
```

## Configuration Options

### Custom Output Directory
```bash
python main.py --all --output-dir my_cards
```

### Custom DPI
```bash
python main.py --all --dpi 600
```

### Custom Cards Per Sheet
```bash
python main.py --all --cards-per-sheet 4
```

### No Cut Guides on Print Sheets
```bash
python main.py --all --no-cut-guides
```

### Custom Image and CSV Paths
```bash
python main.py --all --csv-file my_data.csv --images-dir my_images
```

## Information Commands

### List All Characters
```bash
python main.py --list-characters
```

### List All Tiers
```bash
python main.py --list-tiers
```

### List All Variants
```bash
python main.py --list-variants
```

### Show Database Statistics
```bash
python main.py --stats
```

### Preview Selection (No Generation)
```bash
python main.py --tiers Common Rare --preview
```

## Advanced Examples

### High-Quality PDF Cards for Specific Tiers
```bash
python main.py --tiers Legendary Mythic Divine --format pdf --dpi 600
```

### Individual Cards Only for Characters with Images
```bash
python main.py --all --with-images-only --individual-only
```

### Print Sheets with 6 Cards Per Sheet
```bash
python main.py --all --print-sheets-only --cards-per-sheet 6
```

### Generate Cards in Cost Range with Custom Output
```bash
python main.py --min-cost 500 --max-cost 2000 --output-dir expensive_cards
```

## Verbose and Quiet Modes

### Verbose Output (Debug Information)
```bash
python main.py --all --verbose
```

### Quiet Output (Minimal Messages)
```bash
python main.py --all --quiet
```

## Common Workflows

### Quick Test Run
```bash
python main.py --names "Tim Cheese" --preview
python main.py --names "Tim Cheese"
```

### Full Production Run
```bash
python main.py --all --format both --dpi 300
```

### Print-Ready Sheets Only
```bash
python main.py --all --print-sheets-only --format pdf --dpi 300
```

### Development Testing
```bash
python main.py --tiers Common --with-images-only --verbose
```

## Help and Version

### Show Help
```bash
python main.py --help
```

### Show Quick Help
```bash
python main.py
```

## File Structure After Generation

```
output/
├── individual_cards/
│   ├── Common/
│   ├── Rare/
│   ├── Epic/
│   └── ...
└── print_sheets/
    ├── print_sheet_001.png
    ├── print_sheet_002.png
    └── ...
```