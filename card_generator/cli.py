"""
Command-line interface for the Trading Card Generator.
"""

import argparse
import sys
import logging
import time
from typing import List, Dict, Any, Optional
from .data_loader import CSVDataLoader
from .character_selector import CharacterSelector
from .config import CardConfig, PrintConfig, OutputConfig, ConfigurationManager, DatabaseBuilderConfig
from .image_processor import ImageProcessor
from .card_designer import CardDesigner
from .print_layout import PrintLayoutManager
from .output_manager import OutputManager
from .database_builder import DatabaseBuilder


class CardGeneratorCLI:
    """
    Command-line interface for the Trading Card Generator.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.data_loader = CSVDataLoader()
        self.character_selector = CharacterSelector(self.data_loader)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create and configure the argument parser.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description='Generate trading cards for Brainrot characters',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Generate cards for all characters
  python main.py --all
  
  # Generate cards for specific characters
  python main.py --names "Tim Cheese" "FluriFlura"
  
  # Generate cards for specific tiers
  python main.py --tiers Common Rare
  
  # Generate cards with name pattern
  python main.py --name-pattern "*Cheese*"
  
  # Generate cards in cost range
  python main.py --min-cost 100 --max-cost 1000
  
  # Generate cards only for characters with images
  python main.py --with-images-only
  
  # List available options
  python main.py --list-tiers
  python main.py --list-characters
            """
        )
        
        # Selection options
        selection_group = parser.add_argument_group('Character Selection')
        selection_group.add_argument(
            '--all', 
            action='store_true',
            help='Generate cards for all characters'
        )
        selection_group.add_argument(
            '--names', 
            nargs='+',
            metavar='NAME',
            help='Generate cards for specific character names'
        )
        selection_group.add_argument(
            '--name-pattern',
            metavar='PATTERN',
            help='Generate cards for characters matching pattern (supports wildcards like *)'
        )
        selection_group.add_argument(
            '--tiers',
            nargs='+',
            metavar='TIER',
            help='Generate cards for specific tiers (e.g., Common, Rare, Epic)'
        )
        selection_group.add_argument(
            '--variants',
            nargs='+',
            metavar='VARIANT',
            help='Generate cards for specific variants (e.g., Standard, Special)'
        )
        selection_group.add_argument(
            '--min-cost',
            type=int,
            metavar='COST',
            help='Minimum character cost'
        )
        selection_group.add_argument(
            '--max-cost',
            type=int,
            metavar='COST',
            help='Maximum character cost'
        )
        selection_group.add_argument(
            '--min-income',
            type=int,
            metavar='INCOME',
            help='Minimum character income per second'
        )
        selection_group.add_argument(
            '--max-income',
            type=int,
            metavar='INCOME',
            help='Maximum character income per second'
        )
        selection_group.add_argument(
            '--with-images-only',
            action='store_true',
            help='Generate cards only for characters with available images'
        )
        selection_group.add_argument(
            '--without-images-only',
            action='store_true',
            help='Generate cards only for characters without available images'
        )
        selection_group.add_argument(
            '--case-sensitive',
            action='store_true',
            help='Use case-sensitive matching for names, tiers, and variants'
        )
        
        # Information options
        info_group = parser.add_argument_group('Information')
        info_group.add_argument(
            '--list-characters',
            action='store_true',
            help='List all available character names'
        )
        info_group.add_argument(
            '--list-tiers',
            action='store_true',
            help='List all available tiers'
        )
        info_group.add_argument(
            '--list-variants',
            action='store_true',
            help='List all available variants'
        )
        info_group.add_argument(
            '--stats',
            action='store_true',
            help='Show character database statistics'
        )
        info_group.add_argument(
            '--preview',
            action='store_true',
            help='Preview selected characters without generating cards'
        )
        
        # Output options
        output_group = parser.add_argument_group('Output Options')
        output_group.add_argument(
            '--output-dir',
            metavar='DIR',
            default='output',
            help='Output directory for generated cards (default: output)'
        )
        output_group.add_argument(
            '--format',
            choices=['png', 'pdf', 'both'],
            default='png',
            help='Output format (default: png)'
        )
        output_group.add_argument(
            '--individual-only',
            action='store_true',
            help='Generate only individual card files, not print sheets'
        )
        output_group.add_argument(
            '--print-sheets-only',
            action='store_true',
            help='Generate only print sheets, not individual cards'
        )
        
        # Configuration options
        config_group = parser.add_argument_group('Configuration')
        config_group.add_argument(
            '--csv-file',
            metavar='FILE',
            default='steal_a_brainrot_complete_database.csv',
            help='Path to CSV file with character data'
        )
        config_group.add_argument(
            '--images-dir',
            metavar='DIR',
            default='images',
            help='Directory containing character images'
        )
        config_group.add_argument(
            '--dpi',
            type=int,
            default=300,
            help='DPI for generated images (default: 300, range: 72-600)'
        )
        config_group.add_argument(
            '--image-ratio',
            type=float,
            metavar='RATIO',
            help='Ratio of card height for image (default: 0.6, range: 0.3-0.8)'
        )
        config_group.add_argument(
            '--margin',
            type=int,
            metavar='PIXELS',
            help='Outer margin in pixels (default: 50, range: 10-200)'
        )
        config_group.add_argument(
            '--inner-margin',
            type=int,
            metavar='PIXELS',
            help='Inner margin in pixels (default: 20, range: 5-100)'
        )
        config_group.add_argument(
            '--sheet-margin',
            type=int,
            metavar='PIXELS',
            help='Print sheet margin in pixels (default: 6, range: 0-100)'
        )
        config_group.add_argument(
            '--card-spacing',
            type=int,
            metavar='PIXELS',
            help='Spacing between cards on print sheet (default: 6, range: 0-50)'
        )
        config_group.add_argument(
            '--cards-per-sheet',
            type=int,
            metavar='COUNT',
            help='Number of cards per print sheet (default: 2, range: 1-6)'
        )
        config_group.add_argument(
            '--no-cut-guides',
            action='store_true',
            help='Disable cutting guides on print sheets'
        )
        config_group.add_argument(
            '--image-quality',
            type=int,
            metavar='QUALITY',
            help='Image quality for JPEG/PNG (default: 95, range: 1-100)'
        )
        config_group.add_argument(
            '--pdf-quality',
            type=int,
            metavar='QUALITY',
            help='PDF compression quality (default: 95, range: 1-100)'
        )
        config_group.add_argument(
            '--no-subdirectories',
            action='store_true',
            help='Do not create tier subdirectories in output'
        )
        config_group.add_argument(
            '--no-overwrite',
            action='store_true',
            help='Do not overwrite existing files'
        )
        config_group.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress progress output'
        )
        config_group.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information'
        )
        
        # Database builder options
        db_group = parser.add_argument_group('Database Builder')
        db_group.add_argument(
            '--build-database',
            action='store_true',
            help='Build character database by scraping wiki data'
        )
        db_group.add_argument(
            '--wiki-url',
            metavar='URL',
            default='https://stealabrainrot.fandom.com',
            help='Base URL for the wiki (default: https://stealabrainrot.fandom.com)'
        )
        db_group.add_argument(
            '--databases-dir',
            metavar='DIR',
            default='databases',
            help='Directory for generated database files (default: databases)'
        )
        db_group.add_argument(
            '--rate-limit',
            type=float,
            metavar='SECONDS',
            default=2.0,
            help='Delay between wiki requests in seconds (default: 2.0)'
        )
        db_group.add_argument(
            '--max-retries',
            type=int,
            metavar='COUNT',
            default=3,
            help='Maximum retries for failed requests (default: 3)'
        )
        db_group.add_argument(
            '--timeout',
            type=int,
            metavar='SECONDS',
            default=30,
            help='Request timeout in seconds (default: 30)'
        )
        db_group.add_argument(
            '--skip-images',
            action='store_true',
            help='Skip image downloading during database building'
        )
        db_group.add_argument(
            '--validate-csv',
            action='store_true',
            help='Validate generated CSV format'
        )
        
        return parser
    
    def parse_selection_criteria(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Parse command-line arguments into selection criteria.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Dictionary with selection criteria
        """
        criteria = {}
        
        if args.names:
            criteria['names'] = args.names
        
        if args.name_pattern:
            criteria['name_pattern'] = args.name_pattern
        
        if args.tiers:
            criteria['tiers'] = args.tiers
        
        if args.variants:
            criteria['variants'] = args.variants
        
        if args.min_cost is not None:
            criteria['min_cost'] = args.min_cost
        
        if args.max_cost is not None:
            criteria['max_cost'] = args.max_cost
        
        if args.min_income is not None:
            criteria['min_income'] = args.min_income
        
        if args.max_income is not None:
            criteria['max_income'] = args.max_income
        
        if args.with_images_only:
            criteria['with_images_only'] = True
        
        if args.without_images_only:
            criteria['without_images_only'] = True
        
        if args.case_sensitive:
            criteria['case_sensitive'] = True
        
        return criteria
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """
        Validate command-line arguments.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            True if arguments are valid, False otherwise
        """
        # Check for conflicting image options
        if args.with_images_only and args.without_images_only:
            print("Error: Cannot specify both --with-images-only and --without-images-only")
            return False
        
        # Check for conflicting output options
        if args.individual_only and args.print_sheets_only:
            print("Error: Cannot specify both --individual-only and --print-sheets-only")
            return False
        
        # Check cost range
        if args.min_cost is not None and args.max_cost is not None:
            if args.min_cost > args.max_cost:
                print("Error: min-cost cannot be greater than max-cost")
                return False
        
        # Check income range
        if args.min_income is not None and args.max_income is not None:
            if args.min_income > args.max_income:
                print("Error: min-income cannot be greater than max-income")
                return False
        
        # Check that at least one selection method is specified for generation
        selection_methods = [
            args.all, args.names, args.name_pattern, args.tiers, args.variants,
            args.min_cost is not None, args.max_cost is not None,
            args.min_income is not None, args.max_income is not None,
            args.with_images_only, args.without_images_only
        ]
        
        info_methods = [
            args.list_characters, args.list_tiers, args.list_variants, 
            args.stats, args.preview
        ]
        
        database_methods = [
            args.build_database
        ]
        
        if not any(selection_methods) and not any(info_methods) and not any(database_methods):
            print("Error: Must specify at least one selection method, information option, or database builder option")
            return False
        
        return True
    
    def handle_info_commands(self, args: argparse.Namespace) -> bool:
        """
        Handle information commands (list, stats, etc.).
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            True if an info command was handled, False otherwise
        """
        handled = False
        
        if args.list_characters:
            print("Available characters:")
            names = self.data_loader.get_character_names()
            for name in names:
                print(f"  {name}")
            print(f"\nTotal: {len(names)} characters")
            handled = True
        
        if args.list_tiers:
            print("Available tiers:")
            tiers = self.data_loader.get_available_tiers()
            for tier in tiers:
                print(f"  {tier}")
            print(f"\nTotal: {len(tiers)} tiers")
            handled = True
        
        if args.list_variants:
            print("Available variants:")
            variants = self.data_loader.get_available_variants()
            for variant in variants:
                print(f"  {variant}")
            print(f"\nTotal: {len(variants)} variants")
            handled = True
        
        if args.stats:
            stats = self.data_loader.get_image_coverage_stats()
            print("Character database statistics:")
            print(f"  Total characters: {stats['total_characters']}")
            print(f"  Characters with images: {stats['characters_with_images']}")
            print(f"  Characters without images: {stats['characters_without_images']}")
            print(f"  Image coverage: {stats['image_coverage_percentage']:.1f}%")
            handled = True
        
        return handled
    
    def preview_selection(self, args: argparse.Namespace) -> List:
        """
        Preview the character selection without generating cards.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            List of selected characters
        """
        # Update data loader paths if specified
        if args.csv_file != 'steal_a_brainrot_complete_database.csv' or args.images_dir != 'images':
            self.data_loader = CSVDataLoader(args.csv_file, args.images_dir)
            self.character_selector = CharacterSelector(self.data_loader)
        
        # Get selection criteria
        if args.all:
            characters = self.character_selector.get_all_characters()
        else:
            criteria = self.parse_selection_criteria(args)
            characters = self.character_selector.select_characters(criteria)
        
        # Show preview
        if not characters:
            print("No characters match the selection criteria.")
            return []
        
        print(f"Selected {len(characters)} characters:")
        for char in characters:
            image_status = "✓" if char.has_image() else "✗"
            print(f"  {image_status} {char.name} ({char.tier}) - Cost: {char.cost}, Income: {char.income}/s")
        
        # Show summary
        summary = self.character_selector.get_selection_summary(characters)
        print(f"\nSelection summary:")
        print(f"  Total: {summary['total_selected']}")
        print(f"  With images: {summary['with_images']}")
        print(f"  Without images: {summary['without_images']}")
        print(f"  Tiers: {', '.join(f'{tier}({count})' for tier, count in summary['tiers'].items())}")
        
        return characters
    
    def build_database(self, args: argparse.Namespace) -> int:
        """
        Build character database by scraping wiki data.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Setup logging
            log_level = logging.DEBUG if args.verbose else logging.INFO if not args.quiet else logging.WARNING
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            logger = logging.getLogger(__name__)
            
            if not args.quiet:
                print("Starting database build process...")
                print("=" * 50)
            
            # Create database builder configuration
            db_config = DatabaseBuilderConfig(
                base_url=args.wiki_url,
                output_dir=args.databases_dir,
                images_dir=args.images_dir,
                rate_limit_delay=args.rate_limit,
                max_retries=args.max_retries,
                timeout=args.timeout,
                skip_existing_images=not args.skip_images,  # Invert logic: skip_images means don't skip existing
                validate_images=args.validate_csv  # Reuse validate_csv flag for image validation
            )
            
            # Initialize database builder
            database_builder = DatabaseBuilder(db_config)
            
            # Progress reporting setup
            start_time = time.time()
            last_progress_time = start_time
            
            def log_progress():
                nonlocal last_progress_time
                current_time = time.time()
                
                # Only log progress every 30 seconds to avoid spam
                if current_time - last_progress_time >= 30.0 or args.verbose:
                    progress_info = database_builder.get_progress_info()
                    
                    if not args.quiet:
                        if progress_info['current_tier']:
                            print(f"Processing tier: {progress_info['current_tier']}")
                        
                        if progress_info['current_character']:
                            print(f"Current character: {progress_info['current_character']}")
                        
                        progress_pct = progress_info['progress_percentage']
                        processed = progress_info['characters_processed']
                        total = progress_info['total_characters']
                        
                        print(f"Progress: {progress_pct:.1f}% ({processed}/{total} characters)")
                        
                        if progress_info['estimated_remaining_time']:
                            eta_minutes = progress_info['estimated_remaining_time'] / 60
                            print(f"Estimated time remaining: {eta_minutes:.1f} minutes")
                        
                        print(f"Successful extractions: {progress_info['successful_extractions']}")
                        print(f"Failed extractions: {progress_info['failed_extractions']}")
                        print(f"Images downloaded: {progress_info['images_downloaded']}")
                        print(f"Image failures: {progress_info['images_failed']}")
                        print("-" * 30)
                    
                    last_progress_time = current_time
            
            # Execute database building
            if not args.quiet:
                print(f"Configuration:")
                print(f"  Wiki URL: {db_config.base_url}")
                print(f"  Output directory: {db_config.output_dir}")
                print(f"  Images directory: {db_config.images_dir}")
                print(f"  Rate limit: {db_config.rate_limit_delay}s between requests")
                print(f"  Max retries: {db_config.max_retries}")
                print(f"  Skip existing images: {db_config.skip_existing_images}")
                print()
            
            # Start the build process
            try:
                result = database_builder.build_database()
                
                # Report final results
                elapsed_time = time.time() - start_time
                
                if not args.quiet:
                    print("\n" + "=" * 50)
                    print("DATABASE BUILD COMPLETED")
                    print("=" * 50)
                    print(f"Processing time: {elapsed_time:.1f} seconds")
                    print(f"Total characters: {result.total_characters}")
                    print(f"Successful extractions: {result.successful_extractions}")
                    print(f"Failed extractions: {result.failed_extractions}")
                    print(f"Success rate: {result.get_success_rate():.1f}%")
                    print()
                    print(f"Images downloaded: {result.images_downloaded}")
                    print(f"Image failures: {result.images_failed}")
                    print(f"Image success rate: {result.get_image_success_rate():.1f}%")
                    print()
                    print(f"Generated database: {result.csv_file_path}")
                    print()
                    
                    # Show tier-by-tier statistics
                    if result.tier_statistics:
                        print("Tier Statistics:")
                        print("-" * 50)
                        for tier, stats in result.tier_statistics.items():
                            success_rate = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0
                            image_total = stats['images_downloaded'] + stats['images_failed']
                            image_rate = (stats['images_downloaded'] / image_total) * 100 if image_total > 0 else 0
                            
                            print(f"{tier:15} | {stats['successful']:3}/{stats['total']:3} chars ({success_rate:5.1f}%) | {stats['images_downloaded']:3} images ({image_rate:5.1f}%)")
                        print()
                    
                    # Show warnings and errors summary
                    if result.warnings:
                        print(f"Warnings: {len(result.warnings)}")
                        if args.verbose:
                            for warning in result.warnings[:10]:  # Show first 10 warnings
                                print(f"  ⚠ {warning}")
                            if len(result.warnings) > 10:
                                print(f"  ... and {len(result.warnings) - 10} more warnings")
                        print()
                    
                    if result.errors:
                        print(f"Errors: {len(result.errors)}")
                        if args.verbose:
                            for error in result.errors[:10]:  # Show first 10 errors
                                print(f"  ✗ {error}")
                            if len(result.errors) > 10:
                                print(f"  ... and {len(result.errors) - 10} more errors")
                        print()
                    
                    print("Database build completed successfully!")
                    print(f"You can now use the generated database: {result.csv_file_path}")
                
                # Return appropriate exit code
                if result.failed_extractions > 0 or result.errors:
                    logger.warning(f"Build completed with {result.failed_extractions} failed extractions and {len(result.errors)} errors")
                    return 1 if result.failed_extractions > result.successful_extractions else 0
                else:
                    return 0
                
            except KeyboardInterrupt:
                print("\nDatabase build interrupted by user")
                logger.info("Database build cancelled by user")
                return 130
                
        except Exception as e:
            if args.verbose:
                logging.exception("Database build failed")
            else:
                print(f"Error: Database build failed: {e}")
            return 1
    
    def generate_cards(self, args: argparse.Namespace) -> int:
        """
        Generate trading cards based on the provided arguments.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Setup logging
            log_level = logging.DEBUG if args.verbose else logging.INFO if not args.quiet else logging.WARNING
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Update data loader paths if specified
            if args.csv_file != 'steal_a_brainrot_complete_database.csv' or args.images_dir != 'images':
                self.data_loader = CSVDataLoader(args.csv_file, args.images_dir)
                self.character_selector = CharacterSelector(self.data_loader)
            
            # Get selected characters
            if args.all:
                characters = self.character_selector.get_all_characters()
            else:
                criteria = self.parse_selection_criteria(args)
                characters = self.character_selector.select_characters(criteria)
            
            if not characters:
                print("No characters match the selection criteria.")
                return 1
            
            if not args.quiet:
                print(f"Generating cards for {len(characters)} characters...")
            
            # Initialize components with configuration
            from .config import ConfigurationManager
            
            # Create card configuration with CLI overrides
            card_config = ConfigurationManager.create_card_config(
                dpi=args.dpi,
                image_ratio=getattr(args, 'image_ratio', None),
                margin=getattr(args, 'margin', None),
                inner_margin=getattr(args, 'inner_margin', None)
            )
            
            # Create print configuration with CLI overrides
            print_config = ConfigurationManager.create_print_config(
                dpi=args.dpi,  # Keep DPI consistent
                cards_per_sheet=getattr(args, 'cards_per_sheet', None),
                sheet_margin=getattr(args, 'sheet_margin', None),
                card_spacing=getattr(args, 'card_spacing', None),
                show_cut_guides=not getattr(args, 'no_cut_guides', False)
            )
            
            # Validate DPI compatibility
            ConfigurationManager.validate_dpi_compatibility(card_config, print_config)
            
            # Determine output formats
            if args.format == 'png':
                formats = ('PNG',)
            elif args.format == 'pdf':
                formats = ('PDF',)
            else:  # both
                formats = ('PNG', 'PDF')
            
            # Create output configuration with CLI overrides
            output_config = ConfigurationManager.create_output_config(
                individual_cards_dir=f'{args.output_dir}/individual_cards',
                print_sheets_dir=f'{args.output_dir}/print_sheets',
                formats=formats,
                image_quality=getattr(args, 'image_quality', None),
                pdf_quality=getattr(args, 'pdf_quality', None),
                create_subdirectories=not getattr(args, 'no_subdirectories', False),
                overwrite_existing=not getattr(args, 'no_overwrite', False)
            )
            
            image_processor = ImageProcessor()
            card_designer = CardDesigner(card_config)
            output_manager = OutputManager(output_config)
            
            # Only create print layout manager if we need print sheets
            print_layout_manager = None
            if not args.individual_only:
                print_layout_manager = PrintLayoutManager(print_config, card_config)
            
            # Progress tracking
            total_operations = len(characters)
            if not args.individual_only:
                # Add print sheets to operation count
                total_operations += (len(characters) + print_config.cards_per_sheet - 1) // print_config.cards_per_sheet
            
            current_operation = 0
            start_time = time.time()
            
            def progress_callback(progress: float, item_name: str, error: Optional[str] = None):
                nonlocal current_operation
                current_operation += 1
                
                if not args.quiet:
                    if error:
                        print(f"[{current_operation}/{total_operations}] ✗ {item_name}: {error}")
                    else:
                        print(f"[{current_operation}/{total_operations}] ✓ {item_name}")
            
            # Generate individual cards if requested
            individual_results = None
            if not args.print_sheets_only:
                if not args.quiet:
                    print("\nGenerating individual cards...")
                
                cards_data = []
                for character in characters:
                    try:
                        # Process character image
                        if character.has_image():
                            character_image = image_processor.load_image(character.image_path)
                            if character_image:
                                character_image = image_processor.resize_and_crop(character_image)
                            else:
                                character_image = image_processor.create_placeholder(character.name, character.tier)
                        else:
                            character_image = image_processor.create_placeholder(character.name, character.tier)
                        
                        # Generate card
                        card_image = card_designer.create_card(character, character_image)
                        cards_data.append((card_image, character))
                        
                    except Exception as e:
                        if args.verbose:
                            logging.exception(f"Failed to generate card for {character.name}")
                        else:
                            logging.error(f"Failed to generate card for {character.name}: {e}")
                        continue
                
                # Save individual cards
                individual_results = output_manager.batch_process_cards(cards_data, progress_callback)
            
            # Generate print sheets if requested
            sheet_results = None
            if not args.individual_only:
                if not args.quiet:
                    print("\nGenerating print sheets...")
                
                # Create print sheets from characters
                sheets = []
                for i in range(0, len(characters), print_config.cards_per_sheet):
                    batch_characters = characters[i:i + print_config.cards_per_sheet]
                    
                    # Generate cards for this batch
                    batch_cards = []
                    for character in batch_characters:
                        try:
                            # Process character image
                            if character.has_image():
                                character_image = image_processor.load_image(character.image_path)
                                if character_image:
                                    character_image = image_processor.resize_and_crop(character_image)
                                else:
                                    character_image = image_processor.create_placeholder(character.name, character.tier)
                            else:
                                character_image = image_processor.create_placeholder(character.name, character.tier)
                            
                            card_image = card_designer.create_card(character, character_image)
                            batch_cards.append(card_image)
                        except Exception as e:
                            logging.error(f"Failed to generate card for print sheet: {character.name}: {e}")
                            continue
                    
                    if batch_cards and print_layout_manager:
                        # Create print sheet
                        sheet = print_layout_manager.create_print_sheet(batch_cards)
                        sheets.append(sheet)
                
                # Save print sheets
                if sheets:
                    sheet_results = output_manager.batch_process_print_sheets(sheets, progress_callback)
            
            # Report results
            elapsed_time = time.time() - start_time
            
            if not args.quiet:
                print(f"\nCard generation completed in {elapsed_time:.1f} seconds")
                
                if individual_results:
                    print(f"Individual cards: {individual_results['successful_cards']} successful, "
                          f"{individual_results['failed_cards']} failed")
                
                if sheet_results:
                    print(f"Print sheets: {sheet_results['successful_sheets']} successful, "
                          f"{sheet_results['failed_sheets']} failed")
                
                # Show output summary
                summary = output_manager.get_output_summary()
                print(f"\nOutput saved to:")
                print(f"  Individual cards: {summary['individual_cards_dir']} ({summary['individual_cards_count']} files)")
                print(f"  Print sheets: {summary['print_sheets_dir']} ({summary['print_sheets_count']} files)")
            
            # Return appropriate exit code
            total_failures = 0
            if individual_results:
                total_failures += individual_results['failed_cards']
            if sheet_results:
                total_failures += sheet_results['failed_sheets']
            
            return 1 if total_failures > 0 else 0
            
        except KeyboardInterrupt:
            print("\nCard generation interrupted by user")
            return 130
        except Exception as e:
            if args.verbose:
                logging.exception("Card generation failed")
            else:
                print(f"Error: {e}")
            return 1
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI with the given arguments.
        
        Args:
            args: Command-line arguments (uses sys.argv if None)
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        parser = self.create_parser()
        
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit as e:
            return e.code
        
        # Validate arguments
        if not self.validate_args(parsed_args):
            return 1
        
        try:
            # Handle database builder
            if parsed_args.build_database:
                return self.build_database(parsed_args)
            
            # Handle info commands
            if self.handle_info_commands(parsed_args):
                return 0
            
            # Handle preview
            if parsed_args.preview:
                self.preview_selection(parsed_args)
                return 0
            
            # If we get here, we need to generate cards
            return self.generate_cards(parsed_args)
            
        except Exception as e:
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"Error: {e}")
            return 1


def main():
    """Main entry point for the CLI."""
    cli = CardGeneratorCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())