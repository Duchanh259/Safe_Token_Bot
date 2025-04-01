#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logger configuration module.
Sets up logging for the application.
"""

import os
import logging
import logging.handlers
from datetime import datetime


def setup_logging(log_level: str = 'INFO', log_dir: str = 'logs') -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if not exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Set up logger
    logger = logging.getLogger('bot')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers to avoid duplicate logs
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add formatter to console handler
    console_handler.setFormatter(log_format)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if log_dir is specified
    if log_dir:
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'bot_{timestamp}.log')
        
        # Create rotating file handler to limit file size
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name=None):
    """
    Get a configured logger.
    
    Args:
        name: Logger name, defaults to 'bot'
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name or "bot") 