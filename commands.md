# Trading Card Generator Commands

Quick reference for generating trading cards from Brainrot character data.

## Database Builder Commands (Optional First Step)

Build a fresh character database by scraping the Steal a Brainrot Wiki.

### Build Complete Database
```bash
python main.py --build-database
```
Scrapes the wiki to build a complete character database with images.

### Build Database with Custom Settings
```bash
python main.py --build-database --wiki-url https://stealabrainrot.fandom.com --databases-dir my_databases --rate-limit 1.5
```

### Build Database Without Images
```bash
python main.py --build-database --skip-images
```
Build database with character data only, skip image downloads.

### Build Database with Validation
```bash
python main.py --build-database --validate-csv --verbose
```
Build database with CSV validation and detailed progress output.

### Build Database with Custom Network Settings
```bash
python main.py --build-database --max-retries 5 --timeout 60 --rate-limit 3.0
```

**Database Builder Options:**
- `--wiki-url URL` - Base URL for the wiki (default: https://stealabrainrot.fandom.com)
- `--databases-dir DIR` - Directory for generated database files (default: databases)
- `--rate-limit SECONDS` - Delay between wiki requests (default: 2.0)
- `--max-retries COUNT` - Maximum retries for failed requests (default: 3)
- `--timeout SECONDS` - Request timeout in seconds (default: 30)
- `--skip-images` - Skip image downloading during database building
- `--validate-csv` - Validate generated CSV format

## Image Download Commands (Alternative Method)

Before generating cards, you need to download character images from the wiki.

### Download All Character Images
```bash
python download_images.py
```
Downloads character portrait images for all characters in the CSV database from the Steal a Brainrot Wiki.

### Test Single Character Image Download
```bash
python tests/test_single.py "Character Name"
```
Test image download for a specific character (useful for debugging).

### Test Multiple Character Downloads
```bash
python tests/test_single.py "Tim Cheese" "FluriFlura" "Trippi Troppi"
```
Test image downloads for multiple specific characters.

**Note:** The image download process:
- Automatically finds character wiki pages
- Prioritizes main character portraits from infoboxes
- Downloads high-quality images (skips thumbnails)
- Saves images to the `images/` directory
- Includes rate limiting to be respectful to the wiki server

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

### Complete Database Build and Card Generation
```bash
# Step 1: Build fresh database from wiki
python main.py --build-database --verbose

# Step 2: Generate cards from new database
python main.py --all --format both --dpi 300
```

### Quick Database Update
```bash
# Build database without images (faster)
python main.py --build-database --skip-images --quiet

# Generate cards using existing images
python main.py --all --with-images-only
```

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

## File Structure After Database Build

```
databases/
├── brainrot_database_20241218_143022.csv
└── ...

images/
├── Tim_Cheese.jpg
├── FluriFlura.png
├── Trippi_Troppi.jpg
└── ...
```

## File Structure After Card Generation

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