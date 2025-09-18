"""
Centralized error handling utilities for the Trading Card Generator.

Provides common error handling patterns, logging setup, and recovery mechanisms.
"""

import logging
import os
import sys
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from functools import wraps
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for categorizing issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for better organization."""
    DATA_LOADING = "data_loading"
    IMAGE_PROCESSING = "image_processing"
    FILE_SYSTEM = "file_system"
    VALIDATION = "validation"
    DATA_VALIDATION = "data_validation"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    # Database builder specific categories
    WIKI_SCRAPING = "wiki_scraping"
    CHARACTER_EXTRACTION = "character_extraction"
    IMAGE_DOWNLOAD = "image_download"
    CSV_GENERATION = "csv_generation"
    RATE_LIMITING = "rate_limiting"
    DATABASE_BUILDING = "database_building"


class ErrorInfo:
    """Container for detailed error information."""
    
    def __init__(self, 
                 category: ErrorCategory,
                 severity: ErrorSeverity,
                 message: str,
                 details: Optional[str] = None,
                 suggestions: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.category = category
        self.severity = severity
        self.message = message
        self.details = details or ""
        self.suggestions = suggestions or []
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error info to dictionary."""
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'details': self.details,
            'suggestions': self.suggestions,
            'context': self.context
        }


class ErrorHandler:
    """Centralized error handling and logging system."""
    
    def __init__(self, logger_name: str = 'card_generator'):
        self.logger = logging.getLogger(logger_name)
        self.error_history: List[ErrorInfo] = []
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration if not already configured."""
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def handle_error(self, 
                    error: Exception,
                    category: ErrorCategory,
                    severity: ErrorSeverity,
                    context: Optional[Dict[str, Any]] = None,
                    suggestions: Optional[List[str]] = None) -> ErrorInfo:
        """
        Handle an error with proper logging and tracking.
        
        Args:
            error: The exception that occurred
            category: Category of the error
            severity: Severity level
            context: Additional context information
            suggestions: Recovery suggestions
            
        Returns:
            ErrorInfo object with details
        """
        error_info = ErrorInfo(
            category=category,
            severity=severity,
            message=str(error),
            details=f"{type(error).__name__}: {error}",
            suggestions=suggestions or self._get_default_suggestions(error, category),
            context=context or {}
        )
        
        # Log the error
        log_level = self._get_log_level(severity)
        self.logger.log(
            log_level,
            f"[{category.value.upper()}] {error_info.message}",
            extra={'error_info': error_info.to_dict()}
        )
        
        # Track error
        self.error_history.append(error_info)
        
        return error_info
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get logging level based on error severity."""
        severity_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return severity_map.get(severity, logging.ERROR)
    
    def _get_default_suggestions(self, error: Exception, category: ErrorCategory) -> List[str]:
        """Get default recovery suggestions based on error type and category."""
        suggestions = []
        error_str = str(error).lower()
        
        # Common suggestions based on error type
        if isinstance(error, FileNotFoundError):
            suggestions.extend([
                "Verify the file path is correct",
                "Check that the file exists",
                "Ensure the working directory is correct"
            ])
        elif isinstance(error, PermissionError):
            suggestions.extend([
                "Check file and directory permissions",
                "Run with appropriate privileges",
                "Ensure files are not read-only or in use"
            ])
        elif isinstance(error, OSError) and hasattr(error, 'errno') and error.errno == 28:
            suggestions.extend([
                "Free up disk space",
                "Choose a different output location",
                "Clean up temporary files"
            ])
        elif isinstance(error, ValueError):
            suggestions.extend([
                "Check input data format and validity",
                "Verify configuration parameters",
                "Review data for corruption"
            ])
        
        # Category-specific suggestions
        if category == ErrorCategory.DATA_LOADING:
            suggestions.extend([
                "Validate CSV file format and encoding",
                "Check for missing required columns",
                "Verify data types in CSV fields"
            ])
        elif category == ErrorCategory.IMAGE_PROCESSING:
            suggestions.extend([
                "Check image file format and integrity",
                "Verify image files are not corrupted",
                "Ensure sufficient memory for image processing"
            ])
        elif category == ErrorCategory.FILE_SYSTEM:
            suggestions.extend([
                "Check available disk space",
                "Verify directory write permissions",
                "Ensure output paths are valid"
            ])
        elif category == ErrorCategory.WIKI_SCRAPING:
            suggestions.extend([
                "Check internet connection",
                "Verify wiki URL is accessible",
                "Check if wiki structure has changed",
                "Try again later if server is temporarily unavailable"
            ])
        elif category == ErrorCategory.CHARACTER_EXTRACTION:
            suggestions.extend([
                "Verify character page exists on wiki",
                "Check if character name spelling is correct",
                "Try alternative character page URLs",
                "Check if wiki page structure has changed"
            ])
        elif category == ErrorCategory.IMAGE_DOWNLOAD:
            suggestions.extend([
                "Check internet connection",
                "Verify image URL is accessible",
                "Check available disk space for images",
                "Ensure images directory has write permissions"
            ])
        elif category == ErrorCategory.CSV_GENERATION:
            suggestions.extend([
                "Check available disk space",
                "Verify output directory write permissions",
                "Ensure CSV data is properly formatted",
                "Check for invalid characters in data"
            ])
        elif category == ErrorCategory.RATE_LIMITING:
            suggestions.extend([
                "Increase delay between requests",
                "Wait before retrying requests",
                "Check if IP is temporarily blocked",
                "Reduce concurrent request load"
            ])
        
        return suggestions
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered."""
        if not self.error_history:
            return {
                'total_errors': 0,
                'by_category': {},
                'by_severity': {},
                'recent_errors': []
            }
        
        # Count by category
        by_category = {}
        for error in self.error_history:
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count by severity
        by_severity = {}
        for error in self.error_history:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Get recent errors (last 10)
        recent_errors = [error.to_dict() for error in self.error_history[-10:]]
        
        return {
            'total_errors': len(self.error_history),
            'by_category': by_category,
            'by_severity': by_severity,
            'recent_errors': recent_errors
        }
    
    def clear_error_history(self):
        """Clear the error history."""
        self.error_history.clear()
    
    def has_critical_errors(self) -> bool:
        """Check if any critical errors have occurred."""
        return any(error.severity == ErrorSeverity.CRITICAL for error in self.error_history)


def with_error_handling(category: ErrorCategory, 
                       severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                       reraise: bool = True,
                       default_return: Any = None):
    """
    Decorator for automatic error handling.
    
    Args:
        category: Error category
        severity: Error severity level
        reraise: Whether to reraise the exception after handling
        default_return: Default return value if error occurs and not reraising
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error handler from first argument if it has one
                error_handler = None
                if args and hasattr(args[0], 'error_handler'):
                    error_handler = args[0].error_handler
                elif args and hasattr(args[0], 'logger'):
                    # Create temporary error handler
                    error_handler = ErrorHandler(args[0].logger.name)
                else:
                    error_handler = ErrorHandler()
                
                # Handle the error
                error_handler.handle_error(
                    e, category, severity,
                    context={'function': func.__name__, 'args': str(args), 'kwargs': str(kwargs)}
                )
                
                if reraise:
                    raise
                else:
                    return default_return
        
        return wrapper
    return decorator


def setup_logging(level: int = logging.INFO, 
                 format_string: Optional[str] = None,
                 log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging for the entire application.
    
    Args:
        level: Logging level
        format_string: Custom format string
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger('card_generator')
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set level
    logger.setLevel(level)
    
    # Default format
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")
    
    return logger


def validate_file_system_requirements(output_dir: str, 
                                     min_space_mb: int = 100) -> List[ErrorInfo]:
    """
    Validate file system requirements before processing.
    
    Args:
        output_dir: Output directory path
        min_space_mb: Minimum required space in MB
        
    Returns:
        List of validation errors
    """
    errors = []
    error_handler = ErrorHandler()
    
    try:
        output_path = Path(output_dir)
        
        # Check if directory exists or can be created
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            errors.append(error_handler.handle_error(
                e, ErrorCategory.FILE_SYSTEM, ErrorSeverity.CRITICAL,
                context={'directory': str(output_path)}
            ))
        
        # Check write permissions
        if output_path.exists():
            test_file = output_path / '.write_test'
            try:
                test_file.write_text('test')
                test_file.unlink()
            except PermissionError as e:
                errors.append(error_handler.handle_error(
                    e, ErrorCategory.FILE_SYSTEM, ErrorSeverity.HIGH,
                    context={'directory': str(output_path)}
                ))
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(output_path)
            free_mb = free / (1024 * 1024)
            
            if free_mb < min_space_mb:
                error = OSError(f"Insufficient disk space: {free_mb:.1f}MB available, {min_space_mb}MB required")
                errors.append(error_handler.handle_error(
                    error, ErrorCategory.FILE_SYSTEM, ErrorSeverity.HIGH,
                    context={'available_mb': free_mb, 'required_mb': min_space_mb}
                ))
        except Exception as e:
            errors.append(error_handler.handle_error(
                e, ErrorCategory.FILE_SYSTEM, ErrorSeverity.MEDIUM,
                context={'directory': str(output_path)}
            ))
    
    except Exception as e:
        errors.append(error_handler.handle_error(
            e, ErrorCategory.FILE_SYSTEM, ErrorSeverity.CRITICAL,
            context={'output_dir': output_dir}
        ))
    
    return errors


def create_error_report(error_handler: ErrorHandler, 
                       output_file: Optional[str] = None) -> str:
    """
    Create a detailed error report.
    
    Args:
        error_handler: ErrorHandler instance with error history
        output_file: Optional file to write report to
        
    Returns:
        Error report as string
    """
    summary = error_handler.get_error_summary()
    
    report_lines = [
        "=" * 60,
        "TRADING CARD GENERATOR - ERROR REPORT",
        "=" * 60,
        "",
        f"Total Errors: {summary['total_errors']}",
        ""
    ]
    
    if summary['by_severity']:
        report_lines.extend([
            "Errors by Severity:",
            "-" * 20
        ])
        for severity, count in summary['by_severity'].items():
            report_lines.append(f"  {severity.upper()}: {count}")
        report_lines.append("")
    
    if summary['by_category']:
        report_lines.extend([
            "Errors by Category:",
            "-" * 20
        ])
        for category, count in summary['by_category'].items():
            report_lines.append(f"  {category.upper()}: {count}")
        report_lines.append("")
    
    if summary['recent_errors']:
        report_lines.extend([
            "Recent Errors:",
            "-" * 15
        ])
        for i, error in enumerate(summary['recent_errors'], 1):
            report_lines.extend([
                f"{i}. [{error['category'].upper()}] {error['message']}",
                f"   Severity: {error['severity'].upper()}",
                f"   Details: {error['details']}"
            ])
            if error['suggestions']:
                report_lines.append("   Suggestions:")
                for suggestion in error['suggestions']:
                    report_lines.append(f"     - {suggestion}")
            report_lines.append("")
    
    report_lines.extend([
        "=" * 60,
        "END OF REPORT",
        "=" * 60
    ])
    
    report = "\n".join(report_lines)
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
        except Exception as e:
            logging.getLogger('card_generator').error(f"Could not write error report to {output_file}: {e}")
    
    return report