# Trading Card Generator Setup Guide

This guide will walk you through setting up the Trading Card Generator from scratch.

## System Requirements

### Operating System
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 18.04+, CentOS 7+, or equivalent)

### Python Version
- Python 3.8 or higher
- pip (Python package installer)

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended for large batches
- **Storage**: 2GB free space (more if downloading many character images)
- **CPU**: Any modern processor (multi-core recommended for faster processing)

## Step-by-Step Installation

### 1. Verify Python Installation

First, check if Python is installed and what version you have:

```bash
python --version
# or
python3 --version
```

If Python is not installed or you have a version older than 3.8:

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer and check "Add Python to PATH"
3. Verify installation: `python --version`

#### macOS
```bash
# Using Homebrew (recommended)
brew install python

# Or download from python.org
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip
```

#### Linux (CentOS/RHEL)
```bash
sudo yum install python3 python3-pip
# or for newer versions
sudo dnf install python3 python3-pip
```

### 2. Download the Project

#### Option A: Download ZIP
1. Download the project as a ZIP file
2. Extract to your desired location
3. Open terminal/command prompt in the project directory

#### Option B: Clone Repository (if using Git)
```bash
git clone [repository-url]
cd trading-card-generator
```

### 3. Install Dependencies

Install the required Python packages:

```bash
# Required packages
pip install pillow requests beautifulsoup4

# Optional (for performance testing)
pip install psutil
```

#### If you encounter permission errors:
```bash
# Use --user flag
pip install --user pillow requests beautifulsoup4

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pillow requests beautifulsoup4
```

### 4. Verify Installation

Test that all dependencies are installed correctly:

```bash
python -c "import PIL; print('✓ Pillow installed')"
python -c "import requests; print('✓ Requests installed')"
python -c "import bs4; print('✓ BeautifulSoup4 installed')"
```

### 5. Prepare Character Data

Ensure you have the character database file:
- File name: `steal_a_brainrot_complete_database.csv`
- Location: Project root directory
- Format: CSV with character names, tiers, costs, and income data

If you don't have this file, you'll need to create it with the following columns:
```csv
Character Name,Tier,Cost,Income per Second,Cost/Income Ratio,Variant Type
```

### 6. Test Basic Functionality

Run a basic test to ensure everything is working:

```bash
python -c "from card_generator.config import CardConfig; print('✓ Card generator modules loaded')"
```

### 7. Download Character Images (Optional)

To get the best results, download character images:

```bash
python download_images.py
```

This will:
- Create an `images/` directory
- Download character images from the Fandom wiki
- Take several minutes depending on the number of characters

### 8. Generate Your First Cards

Test the complete system:

```bash
python examples/basic_usage.py
```

This will:
- Load character data from the CSV
- Generate cards for all characters
- Create both individual cards and print sheets
- Save output to the `output/` directory

## Directory Structure After Setup

After successful setup, your project should look like this:

```
trading-card-generator/
├── card_generator/              # ✓ Main package
├── examples/                    # ✓ Usage examples
├── tests/                       # ✓ Test suite
├── images/                      # ✓ Character images (after download)
├── output/                      # ✓ Generated cards (after first run)
│   ├── individual_cards/
│   └── print_sheets/
├── venv/                        # ✓ Virtual environment (if used)
├── main.py                      # ✓ Main application
├── download_images.py           # ✓ Image downloader
├── steal_a_brainrot_complete_database.csv  # ✓ Character data
├── README.md                    # ✓ Documentation
└── SETUP.md                     # ✓ This file
```

## Troubleshooting Setup Issues

### Python Not Found
```
'python' is not recognized as an internal or external command
```

**Solutions:**
1. **Windows**: Reinstall Python and check "Add Python to PATH"
2. **macOS/Linux**: Try `python3` instead of `python`
3. Add Python to your system PATH manually

### Permission Denied Errors
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**
1. Use `pip install --user` instead of `pip install`
2. Use a virtual environment
3. Run as administrator (Windows) or with `sudo` (macOS/Linux) - not recommended

### Module Not Found Errors
```
ModuleNotFoundError: No module named 'PIL'
```

**Solutions:**
1. Ensure you're using the correct Python environment
2. Reinstall the package: `pip install pillow`
3. Check if you're using a virtual environment

### Virtual Environment Issues
```
'venv' is not recognized
```

**Solutions:**
1. **Windows**: Use `python -m venv venv`
2. **macOS/Linux**: Use `python3 -m venv venv`
3. Ensure Python was installed with venv support

### CSV File Not Found
```
Error: CSV file 'steal_a_brainrot_complete_database.csv' not found!
```

**Solutions:**
1. Ensure the CSV file is in the project root directory
2. Check the file name spelling exactly
3. Verify the file is not empty or corrupted

### Image Download Failures
```
Failed to download image: 503 Server Error
```

**Solutions:**
1. Check your internet connection
2. Try again later (server may be temporarily unavailable)
3. The system will work with placeholder images if downloads fail

## Advanced Setup Options

### Using Virtual Environments (Recommended)

Virtual environments keep your project dependencies isolated:

```bash
# Create virtual environment
python -m venv trading_cards_env

# Activate it
# Windows:
trading_cards_env\Scripts\activate
# macOS/Linux:
source trading_cards_env/bin/activate

# Install dependencies
pip install pillow requests beautifulsoup4 psutil

# When done working:
deactivate
```

### Development Setup

If you plan to modify the code:

```bash
# Install development dependencies
pip install pillow requests beautifulsoup4 psutil

# Run tests to verify everything works
python -m unittest discover -s tests -p "test_*.py"

# Run performance tests
python -m unittest tests.test_performance
```

### Custom Configuration

Create a custom configuration file for your specific needs:

```python
# config_custom.py
from card_generator.config import CardConfig, PrintConfig, OutputConfig

# High-quality configuration
HIGH_QUALITY = CardConfig(
    width=2480,
    height=3508,
    dpi=420,
    margin=80
)

# Your custom output directory
CUSTOM_OUTPUT = OutputConfig(
    individual_cards_dir='my_cards/individual',
    print_sheets_dir='my_cards/sheets'
)
```

## Verification Checklist

Before using the system, verify:

- [ ] Python 3.8+ is installed
- [ ] All required packages are installed
- [ ] Character CSV file is present
- [ ] Basic test runs without errors
- [ ] Output directories are created
- [ ] Images download successfully (optional)
- [ ] First card generation completes

## Getting Help

If you encounter issues during setup:

1. **Check the error message carefully** - it usually indicates the specific problem
2. **Run the test suite** to identify which component is failing
3. **Check file permissions** and disk space
4. **Verify all dependencies** are installed correctly
5. **Try the examples** to test individual components

## Next Steps

After successful setup:

1. **Explore the examples** in the `examples/` directory
2. **Run the test suite** to understand the system capabilities
3. **Try different configurations** for your specific needs
4. **Generate your first batch of cards**
5. **Test print a sample sheet** to verify quality

Congratulations! Your Trading Card Generator is now ready to use.