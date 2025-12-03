"""
Centralized Logging Configuration Module
=========================================
Enterprise-grade structured logging for the Insurance Claims Backend.

Features:
- Structured JSON logging for production environments
- Correlation ID tracking for request tracing across services
- Consistent log format with service context
- Automatic inclusion of module, function, and line information
- Thread-safe context management for correlation IDs

Usage:
    from app.core.logging_config import get_logger, set_correlation_id, get_correlation_id

    logger = get_logger(__name__)
    logger.info("Processing request", extra={"user_id": "123", "action": "login"})
"""

import logging
import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Thread-safe context variable for correlation ID
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID for request tracing.
    
    Returns:
        Current correlation ID or None if not set
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set or generate a correlation ID for the current request context.
    
    Args:
        correlation_id: Optional ID to use, generates UUID if not provided
        
    Returns:
        The correlation ID that was set
    """
    cid = correlation_id or str(uuid.uuid4())
    _correlation_id.set(cid)
    return cid


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    _correlation_id.set(None)


class StructuredJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Produces logs in a format that's easily parsed by log aggregation
    systems like CloudWatch, ELK Stack, or Splunk.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "service": "insurance-backend",
        }

        # Add correlation ID if available
        correlation_id = get_correlation_id()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }

        # Add extra fields (excluding standard LogRecord attributes)
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'taskName', 'message'
        }
        
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith('_')
        }
        
        if extra_fields:
            log_entry["context"] = extra_fields

        return json.dumps(log_entry, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter for development environments.
    
    Uses colors and structured format for easy reading during development.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted console log string
        """
        color = self.COLORS.get(record.levelname, self.RESET)
        correlation_id = get_correlation_id()
        cid_str = f"[{correlation_id[:8]}] " if correlation_id else ""
        
        # Format: [TIMESTAMP] [LEVEL] [CID] module.function:line - message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        base_msg = (
            f"{self.BOLD}[{timestamp}]{self.RESET} "
            f"{color}[{record.levelname:8}]{self.RESET} "
            f"{cid_str}"
            f"{self.BOLD}{record.module}.{record.funcName}:{record.lineno}{self.RESET} - "
            f"{record.getMessage()}"
        )
        
        # Add extra context if present
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'taskName', 'message'
        }
        
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith('_')
        }
        
        if extra_fields:
            base_msg += f" | {json.dumps(extra_fields, default=str)}"
        
        # Add exception info if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
            
        return base_msg


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_to_file: Optional[str] = None
) -> None:
    """
    Configure application-wide logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, use JSON format; if False, use console format
        log_to_file: Optional file path for logging to file
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if json_format:
        console_handler.setFormatter(StructuredJsonFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())
    
    root_logger.addHandler(console_handler)
    
    # Optional file handler
    if log_to_file:
        file_handler = logging.FileHandler(log_to_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(StructuredJsonFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Module-level logger for this config module
_logger = get_logger(__name__)


class LogContext:
    """
    Context manager for adding temporary context to logs.
    
    Usage:
        with LogContext(user_id="123", action="process_claim"):
            logger.info("Processing...")  # Will include user_id and action
    """
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self._old_factory = None
        
    def __enter__(self):
        old_factory = logging.getLogRecordFactory()
        context = self.context
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in context.items():
                setattr(record, key, value)
            return record
        
        self._old_factory = old_factory
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, *args):
        if self._old_factory:
            logging.setLogRecordFactory(self._old_factory)

