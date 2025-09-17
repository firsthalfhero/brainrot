"""
Output file management system for organizing and saving generated trading cards.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from PIL import Image

from .config import OutputConfig
from .data_models import CharacterData
from .error_handling import ErrorHandler, ErrorCategory, ErrorSeverity


logger = logging.getLogger(__name__)


class OutputManager:
    """
    Handles the organization and saving of generated trading card files,
    including individual cards and print sheets in multiple formats.
    """
    
    def __init__(self, config: Optional[OutputConfig] = None):
        """
        Initialize the OutputManager with configuration.
        
        Args:
            config: Output configuration settings. Uses default if None.
        """
        self.config = config or OutputConfig()
        self.error_handler = ErrorHandler(__name__)
        self._ensure_directories()
        
    def save_individual_card(self, card_image: Image.Image, character: CharacterData, 
                           format: str = 'PNG') -> str:
        """
        Save an individual trading card to the appropriate directory.
        
        Args:
            card_image: PIL Image of the trading card
            character: Character data for filename generation
            format: Output format ('PNG', 'PDF', etc.)
            
        Returns:
            Path to the saved file
            
        Raises:
            ValueError: If format is not supported
            IOError: If file cannot be saved
        """
        if format.upper() not in self.config.formats:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.config.formats}")
        
        # Generate filename
        safe_name = self._sanitize_filename(character.name)
        filename = self.config.card_filename_template.format(
            name=safe_name,
            tier=character.tier
        )
        
        # Ensure correct extension
        if format.upper() == 'PNG':
            filename = filename.replace('.png', '') + '.png'
        elif format.upper() == 'PDF':
            filename = filename.replace('.png', '') + '.pdf'
        
        # Full path
        filepath = Path(self.config.individual_cards_dir) / filename
        
        try:
            # Check available disk space before saving
            self._check_disk_space(filepath.parent)
            
            # Ensure parent directory exists and is writable
            self._ensure_directory_writable(filepath.parent)
            
            if format.upper() == 'PNG':
                card_image.save(filepath, 'PNG', optimize=True)
            elif format.upper() == 'PDF':
                # Convert to RGB if necessary for PDF
                if card_image.mode != 'RGB':
                    card_image = card_image.convert('RGB')
                card_image.save(filepath, 'PDF', quality=self.config.image_quality)
            
            # Verify file was actually created and has reasonable size
            if not filepath.exists():
                raise IOError("File was not created successfully")
            
            file_size = filepath.stat().st_size
            if file_size == 0:
                filepath.unlink()  # Remove empty file
                raise IOError("Created file is empty")
            
            logger.info(f"Saved individual card: {filepath} ({file_size} bytes)")
            return str(filepath)
            
        except PermissionError as e:
            logger.error(f"Permission denied saving card for {character.name}: {e}")
            raise IOError(f"Permission denied: {e}")
        except OSError as e:
            if e.errno == 28:  # No space left on device
                logger.error(f"Disk full while saving card for {character.name}")
                raise IOError("Disk full - cannot save file")
            else:
                logger.error(f"OS error saving card for {character.name}: {e}")
                raise IOError(f"File system error: {e}")
        except Exception as e:
            logger.error(f"Failed to save card for {character.name}: {e}")
            raise IOError(f"Could not save card file: {e}")
    
    def save_print_sheet(self, sheet_image: Image.Image, batch_number: int, 
                        format: str = 'PNG') -> str:
        """
        Save a print sheet to the appropriate directory.
        
        Args:
            sheet_image: PIL Image of the print sheet
            batch_number: Batch number for filename generation
            format: Output format ('PNG', 'PDF', etc.)
            
        Returns:
            Path to the saved file
            
        Raises:
            ValueError: If format is not supported
            IOError: If file cannot be saved
        """
        if format.upper() not in self.config.formats:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.config.formats}")
        
        # Generate filename
        filename = self.config.sheet_filename_template.format(batch_number=batch_number)
        
        # Ensure correct extension
        if format.upper() == 'PNG':
            filename = filename.replace('.png', '') + '.png'
        elif format.upper() == 'PDF':
            filename = filename.replace('.png', '') + '.pdf'
        
        # Full path
        filepath = Path(self.config.print_sheets_dir) / filename
        
        try:
            # Check available disk space before saving
            self._check_disk_space(filepath.parent)
            
            # Ensure parent directory exists and is writable
            self._ensure_directory_writable(filepath.parent)
            
            if format.upper() == 'PNG':
                sheet_image.save(filepath, 'PNG', optimize=True)
            elif format.upper() == 'PDF':
                # Convert to RGB if necessary for PDF
                if sheet_image.mode != 'RGB':
                    sheet_image = sheet_image.convert('RGB')
                sheet_image.save(filepath, 'PDF', quality=self.config.image_quality)
            
            # Verify file was actually created and has reasonable size
            if not filepath.exists():
                raise IOError("File was not created successfully")
            
            file_size = filepath.stat().st_size
            if file_size == 0:
                filepath.unlink()  # Remove empty file
                raise IOError("Created file is empty")
            
            logger.info(f"Saved print sheet: {filepath} ({file_size} bytes)")
            return str(filepath)
            
        except PermissionError as e:
            logger.error(f"Permission denied saving print sheet {batch_number}: {e}")
            raise IOError(f"Permission denied: {e}")
        except OSError as e:
            if e.errno == 28:  # No space left on device
                logger.error(f"Disk full while saving print sheet {batch_number}")
                raise IOError("Disk full - cannot save file")
            else:
                logger.error(f"OS error saving print sheet {batch_number}: {e}")
                raise IOError(f"File system error: {e}")
        except Exception as e:
            logger.error(f"Failed to save print sheet {batch_number}: {e}")
            raise IOError(f"Could not save print sheet file: {e}")
    
    def batch_process_cards(self, cards_data: List[tuple], progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Process and save multiple cards with progress tracking and error reporting.
        
        Args:
            cards_data: List of (card_image, character_data) tuples
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with processing results and statistics
        """
        results = {
            'total_cards': len(cards_data),
            'successful_cards': 0,
            'failed_cards': 0,
            'saved_files': [],
            'errors': []
        }
        
        logger.info(f"Starting batch processing of {len(cards_data)} cards")
        
        for i, (card_image, character) in enumerate(cards_data):
            try:
                # Save in all configured formats
                for format in self.config.formats:
                    filepath = self.save_individual_card(card_image, character, format)
                    results['saved_files'].append(filepath)
                
                results['successful_cards'] += 1
                
                # Progress callback
                if progress_callback:
                    progress = (i + 1) / len(cards_data)
                    progress_callback(progress, character.name, None)
                    
            except Exception as e:
                error_msg = f"Failed to process {character.name}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['failed_cards'] += 1
                
                # Progress callback with error
                if progress_callback:
                    progress = (i + 1) / len(cards_data)
                    progress_callback(progress, character.name, str(e))
        
        logger.info(f"Batch processing complete. Success: {results['successful_cards']}, "
                   f"Failed: {results['failed_cards']}")
        
        return results
    
    def batch_process_print_sheets(self, sheets: List[Image.Image], 
                                 progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Process and save multiple print sheets with progress tracking.
        
        Args:
            sheets: List of print sheet images
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with processing results and statistics
        """
        results = {
            'total_sheets': len(sheets),
            'successful_sheets': 0,
            'failed_sheets': 0,
            'saved_files': [],
            'errors': []
        }
        
        logger.info(f"Starting batch processing of {len(sheets)} print sheets")
        
        for i, sheet_image in enumerate(sheets):
            try:
                batch_number = i + 1
                
                # Save in all configured formats
                for format in self.config.formats:
                    filepath = self.save_print_sheet(sheet_image, batch_number, format)
                    results['saved_files'].append(filepath)
                
                results['successful_sheets'] += 1
                
                # Progress callback
                if progress_callback:
                    progress = (i + 1) / len(sheets)
                    progress_callback(progress, f"Sheet {batch_number}", None)
                    
            except Exception as e:
                error_msg = f"Failed to process print sheet {i + 1}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['failed_sheets'] += 1
                
                # Progress callback with error
                if progress_callback:
                    progress = (i + 1) / len(sheets)
                    progress_callback(progress, f"Sheet {i + 1}", str(e))
        
        logger.info(f"Print sheet processing complete. Success: {results['successful_sheets']}, "
                   f"Failed: {results['failed_sheets']}")
        
        return results
    
    def clean_output_directories(self) -> None:
        """
        Clean all output directories by removing existing files.
        
        Raises:
            IOError: If directories cannot be cleaned
        """
        try:
            # Clean individual cards directory
            cards_dir = Path(self.config.individual_cards_dir)
            if cards_dir.exists():
                for file in cards_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                logger.info(f"Cleaned individual cards directory: {cards_dir}")
            
            # Clean print sheets directory
            sheets_dir = Path(self.config.print_sheets_dir)
            if sheets_dir.exists():
                for file in sheets_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                logger.info(f"Cleaned print sheets directory: {sheets_dir}")
                
        except Exception as e:
            logger.error(f"Failed to clean output directories: {e}")
            raise IOError(f"Could not clean output directories: {e}")
    
    def get_output_summary(self) -> Dict[str, Any]:
        """
        Get summary information about current output files.
        
        Returns:
            Dictionary with file counts and directory information
        """
        summary = {
            'individual_cards_dir': self.config.individual_cards_dir,
            'print_sheets_dir': self.config.print_sheets_dir,
            'individual_cards_count': 0,
            'print_sheets_count': 0,
            'total_files': 0,
            'supported_formats': list(self.config.formats)
        }
        
        try:
            # Count individual cards
            cards_dir = Path(self.config.individual_cards_dir)
            if cards_dir.exists():
                summary['individual_cards_count'] = len([f for f in cards_dir.iterdir() if f.is_file()])
            
            # Count print sheets
            sheets_dir = Path(self.config.print_sheets_dir)
            if sheets_dir.exists():
                summary['print_sheets_count'] = len([f for f in sheets_dir.iterdir() if f.is_file()])
            
            summary['total_files'] = summary['individual_cards_count'] + summary['print_sheets_count']
            
        except Exception as e:
            logger.warning(f"Could not get complete output summary: {e}")
        
        return summary
    
    def _ensure_directories(self) -> None:
        """
        Ensure that all required output directories exist.
        
        Raises:
            IOError: If directories cannot be created
        """
        try:
            # Create individual cards directory
            cards_dir = Path(self.config.individual_cards_dir)
            cards_dir.mkdir(parents=True, exist_ok=True)
            
            # Create print sheets directory
            sheets_dir = Path(self.config.print_sheets_dir)
            sheets_dir.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Ensured output directories exist: {cards_dir}, {sheets_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create output directories: {e}")
            raise IOError(f"Could not create output directories: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing or replacing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem use
        """
        # Replace invalid characters and spaces with underscores
        invalid_chars = '<>:"/\\|?* '
        sanitized = filename
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove multiple consecutive underscores
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = 'unnamed'
        
        # Limit length to avoid filesystem issues
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    def _check_disk_space(self, directory: Path, min_space_mb: int = 100) -> None:
        """
        Check if there's sufficient disk space available.
        
        Args:
            directory: Directory to check space for
            min_space_mb: Minimum required space in MB
            
        Raises:
            IOError: If insufficient disk space
        """
        try:
            import shutil
            total, used, free = shutil.disk_usage(directory)
            free_mb = free / (1024 * 1024)
            
            if free_mb < min_space_mb:
                error_msg = f"Insufficient disk space: {free_mb:.1f}MB available, {min_space_mb}MB required"
                logger.error(error_msg)
                raise IOError(error_msg)
                
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            # Don't fail the operation if we can't check disk space
    
    def _ensure_directory_writable(self, directory: Path) -> None:
        """
        Ensure directory exists and is writable.
        
        Args:
            directory: Directory to check
            
        Raises:
            IOError: If directory cannot be created or is not writable
        """
        try:
            # Create directory if it doesn't exist
            directory.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions by creating a temporary file
            test_file = directory / '.write_test'
            try:
                test_file.write_text('test')
                test_file.unlink()
            except PermissionError:
                raise IOError(f"Directory is not writable: {directory}")
            except Exception as e:
                raise IOError(f"Cannot write to directory {directory}: {e}")
                
        except PermissionError:
            raise IOError(f"Permission denied creating directory: {directory}")
        except Exception as e:
            raise IOError(f"Cannot ensure directory is writable {directory}: {e}")
    
    def get_error_recovery_suggestions(self, error: Exception) -> List[str]:
        """
        Get suggestions for recovering from common errors.
        
        Args:
            error: The exception that occurred
            
        Returns:
            List of suggested recovery actions
        """
        suggestions = []
        error_str = str(error).lower()
        
        if 'permission denied' in error_str:
            suggestions.extend([
                "Check file and directory permissions",
                "Run the application with appropriate privileges",
                "Ensure output directories are not read-only",
                "Close any applications that might be using the output files"
            ])
        
        if 'disk full' in error_str or 'no space left' in error_str:
            suggestions.extend([
                "Free up disk space on the target drive",
                "Choose a different output directory with more space",
                "Clean up old output files using clean_output_directories()",
                "Consider using a different output format (PNG vs PDF)"
            ])
        
        if 'file not found' in error_str:
            suggestions.extend([
                "Verify the input file paths are correct",
                "Check that all required files exist",
                "Ensure the working directory is correct"
            ])
        
        if 'corrupted' in error_str or 'invalid' in error_str:
            suggestions.extend([
                "Check the input data for corruption",
                "Try regenerating or re-downloading the source files",
                "Validate the CSV file format and encoding"
            ])
        
        if not suggestions:
            suggestions.append("Check the error logs for more detailed information")
        
        return suggestions