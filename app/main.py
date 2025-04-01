#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Token Security Bot - Main Entry Point
Initializes and starts the Telegram bot.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root directory to the Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.core.bot import TelegramBot
from config.config import LOG_LEVEL, LOG_DIR
from app.utils.logger import setup_logging


def main():
    """
    Entry point of the application.
    Initializes logger, database and Telegram bot.
    """
    # Set up logging
    setup_logging(LOG_LEVEL, LOG_DIR)
    logger = logging.getLogger("bot")
    
    try:
        logger.info("Starting Token Security Bot...")
        
        # Create necessary directories
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Initialize Telegram bot
        bot = TelegramBot()
        
        # Run the bot
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 