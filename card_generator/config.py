"""
Configuration settings for the Trading Card Generator.
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CardConfig:
    """Configuration for card design and layout."""
    
    # Base dimensions (A5 at 300 DPI, adjusted for print layout)
    base_width: int = 1745  # A5 width at 300 DPI (148mm) - adjusted for print layout
    base_height: int = 2468  # A5 height at 300 DPI (210mm) - adjusted for print layout
    dpi: int = 300
    
    # Layout proportions
    image_ratio: float = 0.6  # 60% of card height for image
    margin: int = 50  # pixels
    inner_margin: int = 20  # pixels - margin within card elements
    
    # Colors
    background_color: str = '#FFFFFF'
    text_color: str = '#000000'
    border_color: str = '#CCCCCC'
    border_width: int = 2  # pixels
    
    # Typography (doubled sizes at 300 DPI for enhanced A5 format readability)
    title_font_size: int = 96  # Doubled from 48pt for improved character name readability
    tier_font_size: int = 72   # Doubled from 36pt for enhanced tier information visibility
    stats_font_size: int = 48  # Doubled from 24pt for better income/cost text readability
    
    def __post_init__(self):
        """Validate configuration values after initialization."""
        if self.dpi < 72:
            raise ValueError("DPI must be at least 72")
        if self.dpi > 600:
            raise ValueError("DPI cannot exceed 600 (performance limitation)")
        
        if not (0.3 <= self.image_ratio <= 0.8):
            raise ValueError("Image ratio must be between 0.3 and 0.8")
        
        if self.margin < 10:
            raise ValueError("Margin must be at least 10 pixels")
        if self.margin > 200:
            raise ValueError("Margin cannot exceed 200 pixels")
        
        if self.inner_margin < 5:
            raise ValueError("Inner margin must be at least 5 pixels")
        if self.inner_margin > 100:
            raise ValueError("Inner margin cannot exceed 100 pixels")
        
        if self.title_font_size < 20:
            raise ValueError("Title font size must be at least 20")
        if self.title_font_size > 200:
            raise ValueError("Title font size cannot exceed 200")
        
        if self.stats_font_size < 16:  # Allow smaller base sizes, A5 compliance checked separately
            raise ValueError("Stats font size must be at least 16")
        if self.stats_font_size > 120:
            raise ValueError("Stats font size cannot exceed 120")
        
        # Tier font size validation (ensure it exists)
        if self.tier_font_size < 24:  # Allow smaller base sizes, A5 compliance checked separately
            raise ValueError("Tier font size must be at least 24")
        if self.tier_font_size > 150:
            raise ValueError("Tier font size cannot exceed 150")
    
    @property
    def width(self) -> int:
        """Calculate actual width based on DPI scaling."""
        scale_factor = self.dpi / 300.0
        return int(self.base_width * scale_factor)
    
    @property
    def height(self) -> int:
        """Calculate actual height based on DPI scaling."""
        scale_factor = self.dpi / 300.0
        return int(self.base_height * scale_factor)
    
    @property
    def image_height(self) -> int:
        """Calculate image area height."""
        return int(self.height * self.image_ratio)
    
    @property
    def text_height(self) -> int:
        """Calculate text area height."""
        return self.height - self.image_height
    
    @property
    def scaled_margin(self) -> int:
        """Calculate margin scaled to current DPI."""
        scale_factor = self.dpi / 300.0
        return int(self.margin * scale_factor)
    
    @property
    def scaled_inner_margin(self) -> int:
        """Calculate inner margin scaled to current DPI."""
        scale_factor = self.dpi / 300.0
        return int(self.inner_margin * scale_factor)
    
    @property
    def scaled_title_font_size(self) -> int:
        """Calculate title font size scaled to current DPI."""
        scale_factor = self.dpi / 300.0
        return int(self.title_font_size * scale_factor)
    
    @property
    def scaled_stats_font_size(self) -> int:
        """Calculate stats font size scaled to current DPI."""
        scale_factor = self.dpi / 300.0
        return int(self.stats_font_size * scale_factor)
    
    @property
    def scaled_tier_font_size(self) -> int:
        """Calculate tier font size scaled to current DPI."""
        scale_factor = self.dpi / 300.0
        return int(self.tier_font_size * scale_factor)
    
    def validate_a5_compliance(self) -> bool:
        """
        Validate that configuration meets A5 format compliance requirements.
        
        Returns:
            True if configuration is compliant
            
        Raises:
            ValueError: If configuration doesn't meet A5 requirements
        """
        # Check minimum font sizes at 300 DPI (doubled for enhanced readability)
        if self.dpi == 300:
            if self.title_font_size < 96:
                raise ValueError("Character name font must be at least 96pt at 300 DPI for enhanced A5 readability")
            if self.tier_font_size < 72:
                raise ValueError("Tier font must be at least 72pt at 300 DPI for enhanced A5 readability")
            if self.stats_font_size < 48:
                raise ValueError("Stats font must be at least 48pt at 300 DPI for enhanced A5 readability")
        else:
            # Scale requirements for other DPI settings
            scale_factor = self.dpi / 300.0
            min_title = int(96 * scale_factor)
            min_tier = int(72 * scale_factor)
            min_stats = int(48 * scale_factor)
            
            if self.title_font_size < min_title:
                raise ValueError(f"Character name font must be at least {min_title}pt at {self.dpi} DPI for enhanced A5 readability")
            if self.tier_font_size < min_tier:
                raise ValueError(f"Tier font must be at least {min_tier}pt at {self.dpi} DPI for enhanced A5 readability")
            if self.stats_font_size < min_stats:
                raise ValueError(f"Stats font must be at least {min_stats}pt at {self.dpi} DPI for enhanced A5 readability")
        
        # Check image height requirement (exactly 60%)
        if abs(self.image_ratio - 0.6) > 0.001:
            raise ValueError("Image must occupy exactly 60% of A5 card height for compliance")
        
        return True


@dataclass 
class PrintConfig:
    """Configuration for print layout and formatting."""
    
    # Base A4 dimensions at 300 DPI (landscape)
    base_sheet_width: int = 3508  # A4 height becomes width in landscape (297mm)
    base_sheet_height: int = 2480  # A4 width becomes height in landscape (210mm)
    dpi: int = 300
    
    # Layout
    cards_per_sheet: int = 2
    sheet_margin: int = 6  # pixels - minimal margin for cutting
    card_spacing: int = 6  # pixels between cards - minimal spacing for cutting
    
    # Cut guides
    cut_guide_width: int = 2
    cut_guide_color: str = '#000000'
    cut_guide_length: int = 20  # pixels
    show_cut_guides: bool = True
    
    def __post_init__(self):
        """Validate configuration values after initialization."""
        if self.dpi < 72:
            raise ValueError("DPI must be at least 72")
        if self.dpi > 600:
            raise ValueError("DPI cannot exceed 600 (performance limitation)")
        
        if self.cards_per_sheet < 1:
            raise ValueError("Cards per sheet must be at least 1")
        if self.cards_per_sheet > 6:
            raise ValueError("Cards per sheet cannot exceed 6 (layout limitation)")
        
        if self.sheet_margin < 0:
            raise ValueError("Sheet margin cannot be negative")
        if self.sheet_margin > 100:
            raise ValueError("Sheet margin cannot exceed 100 pixels")
        
        if self.card_spacing < 0:
            raise ValueError("Card spacing cannot be negative")
        if self.card_spacing > 50:
            raise ValueError("Card spacing cannot exceed 50 pixels")
        
        if self.cut_guide_width < 1:
            raise ValueError("Cut guide width must be at least 1 pixel")
        if self.cut_guide_width > 10:
            raise ValueError("Cut guide width cannot exceed 10 pixels")
        
        if self.cut_guide_length < 5:
            raise ValueError("Cut guide length must be at least 5 pixels")
        if self.cut_guide_length > 100:
            raise ValueError("Cut guide length cannot exceed 100 pixels")
    
    @property
    def sheet_width(self) -> int:
        """Calculate actual sheet width based on DPI scaling."""
        scale_factor = self.dpi / 300.0
        return int(self.base_sheet_width * scale_factor)
    
    @property
    def sheet_height(self) -> int:
        """Calculate actual sheet height based on DPI scaling."""
        scale_factor = self.dpi / 300.0
        return int(self.base_sheet_height * scale_factor)
    
    @property
    def scaled_sheet_margin(self) -> int:
        """Calculate sheet margin scaled to current DPI."""
        scale_factor = self.dpi / 300.0
        return int(self.sheet_margin * scale_factor)
    
    @property
    def scaled_card_spacing(self) -> int:
        """Calculate card spacing scaled to current DPI."""
        scale_factor = self.dpi / 300.0
        return int(self.card_spacing * scale_factor)
    
    @property
    def scaled_cut_guide_width(self) -> int:
        """Calculate cut guide width scaled to current DPI."""
        scale_factor = self.dpi / 300.0
        return max(1, int(self.cut_guide_width * scale_factor))
    
    @property
    def scaled_cut_guide_length(self) -> int:
        """Calculate cut guide length scaled to current DPI."""
        scale_factor = self.dpi / 300.0
        return int(self.cut_guide_length * scale_factor)


@dataclass
class OutputConfig:
    """Configuration for output files and directories."""
    
    # Directory paths
    individual_cards_dir: str = 'output/individual_cards'
    print_sheets_dir: str = 'output/print_sheets'
    
    # File formats
    formats: Tuple[str, ...] = ('PNG',)
    image_quality: int = 95  # for JPEG if needed
    pdf_quality: int = 95  # for PDF compression
    
    # File naming
    card_filename_template: str = '{name}_{tier}_card'
    sheet_filename_template: str = 'print_sheet_{batch_number:03d}'
    
    # Output options
    create_subdirectories: bool = True  # Create subdirectories by tier
    overwrite_existing: bool = True  # Overwrite existing files
    
    def __post_init__(self):
        """Validate configuration values after initialization."""
        # Validate formats
        valid_formats = {'PNG', 'PDF', 'JPEG', 'JPG'}
        for fmt in self.formats:
            if fmt.upper() not in valid_formats:
                raise ValueError(f"Unsupported format: {fmt}. Valid formats: {', '.join(valid_formats)}")
        
        # Validate quality settings
        if not (1 <= self.image_quality <= 100):
            raise ValueError("Image quality must be between 1 and 100")
        
        if not (1 <= self.pdf_quality <= 100):
            raise ValueError("PDF quality must be between 1 and 100")
        
        # Validate filename templates
        if not self.card_filename_template:
            raise ValueError("Card filename template cannot be empty")
        
        if not self.sheet_filename_template:
            raise ValueError("Sheet filename template cannot be empty")
        
        # Check for required template variables
        required_card_vars = ['{name}', '{tier}']
        for var in required_card_vars:
            if var not in self.card_filename_template:
                raise ValueError(f"Card filename template must contain {var}")
        
        if '{batch_number' not in self.sheet_filename_template:
            raise ValueError("Sheet filename template must contain {batch_number}")
    
    @property
    def normalized_formats(self) -> Tuple[str, ...]:
        """Get formats normalized to uppercase."""
        return tuple(fmt.upper() for fmt in self.formats)
    
    def get_card_filename(self, name: str, tier: str, format_ext: str) -> str:
        """Generate a card filename with the given parameters."""
        # Clean the name for filesystem safety
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        filename = self.card_filename_template.format(
            name=safe_name,
            tier=tier
        )
        return f"{filename}.{format_ext.lower()}"
    
    def get_sheet_filename(self, batch_number: int, format_ext: str) -> str:
        """Generate a sheet filename with the given parameters."""
        filename = self.sheet_filename_template.format(
            batch_number=batch_number
        )
        return f"{filename}.{format_ext.lower()}"


# Tier color mapping for visual consistency (based on game wiki)
TIER_COLORS: Dict[str, str] = {
    'Common': '#808080',        # Gray
    'Rare': '#4169E1',          # Blue  
    'Epic': '#8A2BE2',          # Purple
    'Legendary': '#FF8C00',     # Orange
    'Mythic': '#DC143C',        # Red
    'Brainrot God': '#FFD700',  # Gold
    'Secret': '#00FFFF',        # Cyan
    'OG': '#FF1493',            # Deep Pink
    'Admin': '#FF0000',         # Bright Red
    'Taco': '#FFFF00',          # Yellow
    # Legacy mapping for backwards compatibility
    'Divine': '#FFD700',        # Gold (maps to Brainrot God)
    'Celestial': '#00FFFF',     # Cyan (maps to Secret)
}

# Default file paths
DEFAULT_CSV_PATH = 'steal_a_brainrot_complete_database.csv'
DEFAULT_IMAGES_DIR = 'images/'


@dataclass
class DatabaseBuilderConfig:
    """Configuration for database builder functionality."""
    
    # Wiki scraping settings
    base_url: str = "https://stealabrainrot.fandom.com"
    brainrots_page_path: str = "/wiki/Brainrots"
    
    # Output directories
    output_dir: str = "databases"
    images_dir: str = "images"
    
    # Network settings
    rate_limit_delay: float = 2.0  # seconds between requests
    max_retries: int = 3
    timeout: int = 30  # seconds
    retry_backoff_factor: float = 2.0  # exponential backoff multiplier
    
    # User agent for respectful scraping
    user_agent: str = "TradingCardGenerator/1.0 (Educational/Research Tool)"
    
    # CSV generation settings
    csv_filename_template: str = "brainrot_database_{timestamp}.csv"
    include_timestamp: bool = True
    
    # Tier mappings based on wiki structure
    tier_headings: Dict[str, str] = None
    
    # Processing options
    skip_existing_images: bool = True  # Skip downloading if image already exists
    validate_images: bool = True  # Validate downloaded images
    continue_on_error: bool = True  # Continue processing other characters on individual failures
    
    def __post_init__(self):
        """Validate configuration values after initialization."""
        # Set default tier headings if not provided
        if self.tier_headings is None:
            self.tier_headings = {
                'Common': 'Common',
                'Rare': 'Rare',
                'Epic': 'Epic',
                'Legendary': 'Legendary',
                'Mythic': 'Mythic',
                'Brainrot God': 'Brainrot God',
                'Secret': 'Secret',
                'OG': 'OG'
            }
        
        # Validate network settings
        if self.rate_limit_delay < 0.5:
            raise ValueError("Rate limit delay must be at least 0.5 seconds for respectful scraping")
        if self.rate_limit_delay > 60:
            raise ValueError("Rate limit delay cannot exceed 60 seconds")
        
        if self.max_retries < 1:
            raise ValueError("Max retries must be at least 1")
        if self.max_retries > 10:
            raise ValueError("Max retries cannot exceed 10")
        
        if self.timeout < 5:
            raise ValueError("Timeout must be at least 5 seconds")
        if self.timeout > 300:
            raise ValueError("Timeout cannot exceed 300 seconds")
        
        if self.retry_backoff_factor < 1.0:
            raise ValueError("Retry backoff factor must be at least 1.0")
        if self.retry_backoff_factor > 10.0:
            raise ValueError("Retry backoff factor cannot exceed 10.0")
        
        # Validate paths
        if not self.output_dir:
            raise ValueError("Output directory cannot be empty")
        if not self.images_dir:
            raise ValueError("Images directory cannot be empty")
        
        # Validate URL components
        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
        if not self.brainrots_page_path.startswith('/'):
            raise ValueError("Brainrots page path must start with /")
        
        # Validate filename template
        if not self.csv_filename_template:
            raise ValueError("CSV filename template cannot be empty")
        if self.include_timestamp and '{timestamp}' not in self.csv_filename_template:
            raise ValueError("CSV filename template must contain {timestamp} when include_timestamp is True")
    
    @property
    def full_brainrots_url(self) -> str:
        """Get the complete URL for the brainrots page."""
        return f"{self.base_url.rstrip('/')}{self.brainrots_page_path}"
    
    @property
    def request_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def get_csv_filename(self, timestamp: Optional[str] = None) -> str:
        """
        Generate CSV filename with optional timestamp.
        
        Args:
            timestamp: Optional timestamp string, will generate current if None
            
        Returns:
            Generated filename
        """
        if self.include_timestamp:
            if timestamp is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return self.csv_filename_template.format(timestamp=timestamp)
        else:
            return self.csv_filename_template.replace('_{timestamp}', '').replace('{timestamp}_', '').replace('{timestamp}', '')
    
    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff.
        
        Args:
            attempt: Current retry attempt (0-based)
            
        Returns:
            Delay in seconds
        """
        base_delay = self.rate_limit_delay
        backoff_delay = base_delay * (self.retry_backoff_factor ** attempt)
        return min(backoff_delay, 60.0)  # Cap at 60 seconds


def validate_database_directories(config: 'DatabaseBuilderConfig') -> bool:
    """
    Validate and create necessary directories for database builder.
    
    Args:
        config: DatabaseBuilderConfig instance
        
    Returns:
        True if directories are valid and accessible
        
    Raises:
        ValueError: If directories cannot be created or accessed
        PermissionError: If insufficient permissions
    """
    import os
    from pathlib import Path
    
    # Validate and create output directory
    output_path = Path(config.output_dir)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(f"Cannot create output directory '{config.output_dir}': {e}")
    except OSError as e:
        raise ValueError(f"Invalid output directory path '{config.output_dir}': {e}")
    
    # Test write permissions
    test_file = output_path / '.write_test'
    try:
        test_file.write_text('test')
        test_file.unlink()
    except PermissionError as e:
        raise PermissionError(f"No write permission for output directory '{config.output_dir}': {e}")
    except OSError as e:
        raise ValueError(f"Cannot write to output directory '{config.output_dir}': {e}")
    
    # Validate and create images directory
    images_path = Path(config.images_dir)
    try:
        images_path.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(f"Cannot create images directory '{config.images_dir}': {e}")
    except OSError as e:
        raise ValueError(f"Invalid images directory path '{config.images_dir}': {e}")
    
    # Test write permissions for images directory
    test_file = images_path / '.write_test'
    try:
        test_file.write_text('test')
        test_file.unlink()
    except PermissionError as e:
        raise PermissionError(f"No write permission for images directory '{config.images_dir}': {e}")
    except OSError as e:
        raise ValueError(f"Cannot write to images directory '{config.images_dir}': {e}")
    
    return True


class ConfigurationManager:
    """Manager for creating and validating configuration objects."""
    
    @staticmethod
    def create_card_config(
        dpi: Optional[int] = None,
        image_ratio: Optional[float] = None,
        margin: Optional[int] = None,
        inner_margin: Optional[int] = None,
        title_font_size: Optional[int] = None,
        stats_font_size: Optional[int] = None,
        **kwargs
    ) -> CardConfig:
        """
        Create a CardConfig with optional overrides.
        
        Args:
            dpi: DPI setting for card generation
            image_ratio: Ratio of card height for image (0.3-0.8)
            margin: Outer margin in pixels
            inner_margin: Inner margin in pixels
            title_font_size: Font size for character names
            stats_font_size: Font size for stats
            **kwargs: Additional configuration options
            
        Returns:
            Configured CardConfig instance
            
        Raises:
            ValueError: If any configuration value is invalid
        """
        config_dict = {}
        
        if dpi is not None:
            config_dict['dpi'] = dpi
        if image_ratio is not None:
            config_dict['image_ratio'] = image_ratio
        if margin is not None:
            config_dict['margin'] = margin
        if inner_margin is not None:
            config_dict['inner_margin'] = inner_margin
        if title_font_size is not None:
            config_dict['title_font_size'] = title_font_size
        if stats_font_size is not None:
            config_dict['stats_font_size'] = stats_font_size
        
        # Add any additional kwargs
        config_dict.update(kwargs)
        
        return CardConfig(**config_dict)
    
    @staticmethod
    def create_print_config(
        dpi: Optional[int] = None,
        cards_per_sheet: Optional[int] = None,
        sheet_margin: Optional[int] = None,
        card_spacing: Optional[int] = None,
        show_cut_guides: Optional[bool] = None,
        **kwargs
    ) -> PrintConfig:
        """
        Create a PrintConfig with optional overrides.
        
        Args:
            dpi: DPI setting for print sheets
            cards_per_sheet: Number of cards per sheet (1-6)
            sheet_margin: Margin around sheet edges
            card_spacing: Spacing between cards
            show_cut_guides: Whether to show cutting guides
            **kwargs: Additional configuration options
            
        Returns:
            Configured PrintConfig instance
            
        Raises:
            ValueError: If any configuration value is invalid
        """
        config_dict = {}
        
        if dpi is not None:
            config_dict['dpi'] = dpi
        if cards_per_sheet is not None:
            config_dict['cards_per_sheet'] = cards_per_sheet
        if sheet_margin is not None:
            config_dict['sheet_margin'] = sheet_margin
        if card_spacing is not None:
            config_dict['card_spacing'] = card_spacing
        if show_cut_guides is not None:
            config_dict['show_cut_guides'] = show_cut_guides
        
        # Add any additional kwargs
        config_dict.update(kwargs)
        
        return PrintConfig(**config_dict)
    
    @staticmethod
    def create_output_config(
        formats: Optional[Tuple[str, ...]] = None,
        individual_cards_dir: Optional[str] = None,
        print_sheets_dir: Optional[str] = None,
        image_quality: Optional[int] = None,
        pdf_quality: Optional[int] = None,
        create_subdirectories: Optional[bool] = None,
        overwrite_existing: Optional[bool] = None,
        **kwargs
    ) -> OutputConfig:
        """
        Create an OutputConfig with optional overrides.
        
        Args:
            formats: Output formats tuple (PNG, PDF, JPEG)
            individual_cards_dir: Directory for individual cards
            print_sheets_dir: Directory for print sheets
            image_quality: Quality for image formats (1-100)
            pdf_quality: Quality for PDF format (1-100)
            create_subdirectories: Whether to create tier subdirectories
            overwrite_existing: Whether to overwrite existing files
            **kwargs: Additional configuration options
            
        Returns:
            Configured OutputConfig instance
            
        Raises:
            ValueError: If any configuration value is invalid
        """
        config_dict = {}
        
        if formats is not None:
            config_dict['formats'] = formats
        if individual_cards_dir is not None:
            config_dict['individual_cards_dir'] = individual_cards_dir
        if print_sheets_dir is not None:
            config_dict['print_sheets_dir'] = print_sheets_dir
        if image_quality is not None:
            config_dict['image_quality'] = image_quality
        if pdf_quality is not None:
            config_dict['pdf_quality'] = pdf_quality
        if create_subdirectories is not None:
            config_dict['create_subdirectories'] = create_subdirectories
        if overwrite_existing is not None:
            config_dict['overwrite_existing'] = overwrite_existing
        
        # Add any additional kwargs
        config_dict.update(kwargs)
        
        return OutputConfig(**config_dict)
    
    @staticmethod
    def validate_dpi_compatibility(card_config: CardConfig, print_config: PrintConfig) -> bool:
        """
        Validate that card and print configurations have compatible DPI settings.
        
        Args:
            card_config: Card configuration
            print_config: Print configuration
            
        Returns:
            True if configurations are compatible
            
        Raises:
            ValueError: If DPI settings are incompatible
        """
        if card_config.dpi != print_config.dpi:
            raise ValueError(
                f"Card DPI ({card_config.dpi}) must match print DPI ({print_config.dpi})"
            )
        return True
    
    @staticmethod
    def create_database_builder_config(
        base_url: Optional[str] = None,
        output_dir: Optional[str] = None,
        images_dir: Optional[str] = None,
        rate_limit_delay: Optional[float] = None,
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None,
        skip_existing_images: Optional[bool] = None,
        validate_images: Optional[bool] = None,
        continue_on_error: Optional[bool] = None,
        **kwargs
    ) -> 'DatabaseBuilderConfig':
        """
        Create a DatabaseBuilderConfig with optional overrides.
        
        Args:
            base_url: Base URL for wiki scraping
            output_dir: Directory for database output files
            images_dir: Directory for downloaded images
            rate_limit_delay: Delay between requests in seconds
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            skip_existing_images: Whether to skip downloading existing images
            validate_images: Whether to validate downloaded images
            continue_on_error: Whether to continue on individual character errors
            **kwargs: Additional configuration options
            
        Returns:
            Configured DatabaseBuilderConfig instance
            
        Raises:
            ValueError: If any configuration value is invalid
        """
        config_dict = {}
        
        if base_url is not None:
            config_dict['base_url'] = base_url
        if output_dir is not None:
            config_dict['output_dir'] = output_dir
        if images_dir is not None:
            config_dict['images_dir'] = images_dir
        if rate_limit_delay is not None:
            config_dict['rate_limit_delay'] = rate_limit_delay
        if max_retries is not None:
            config_dict['max_retries'] = max_retries
        if timeout is not None:
            config_dict['timeout'] = timeout
        if skip_existing_images is not None:
            config_dict['skip_existing_images'] = skip_existing_images
        if validate_images is not None:
            config_dict['validate_images'] = validate_images
        if continue_on_error is not None:
            config_dict['continue_on_error'] = continue_on_error
        
        # Add any additional kwargs
        config_dict.update(kwargs)
        
        config = DatabaseBuilderConfig(**config_dict)
        
        # Validate directories
        validate_database_directories(config)
        
        return config