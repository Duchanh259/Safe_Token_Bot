#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main configuration for the application.
Reads variables from .env file and exports configuration variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Set, Union

# Find the project's root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_USER_IDS = set(int(uid.strip()) for uid in os.getenv('ADMIN_USER_IDS', '').split(',') if uid.strip())

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'token_security_bot')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

# Referral System Configuration
REFERRAL_F1_PERCENTAGE = float(os.getenv('REFERRAL_F1_PERCENTAGE', '3.0'))
REFERRAL_F2_PERCENTAGE = float(os.getenv('REFERRAL_F2_PERCENTAGE', '2.0'))

# Language Configuration
DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en')
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'vi': 'Tiếng Việt',
}

# Database Configuration
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'name': os.getenv('DB_NAME', 'token_security_bot'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
}

# Path to SQLite file
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'data', 'bot.db')

# Database URL configuration
if DB_TYPE == 'sqlite':
    DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"
else:
    DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['name']}"

# Blockchain API Keys
BLOCKCHAIN_API_KEYS = {
    'eth': os.getenv('ETHERSCAN_API_KEY', ''),
    'bsc': os.getenv('BSCSCAN_API_KEY', ''),
    'polygon': os.getenv('POLYGONSCAN_API_KEY', ''),
    'arbitrum': os.getenv('ARBISCAN_API_KEY', ''),
    'tron': os.getenv('TRON_API_KEY', ''),
    'sui': os.getenv('SUI_API_URL', ''),
}

# Web3 Providers
WEB3_PROVIDERS = {
    'eth': os.getenv('ETH_PROVIDER', ''),
    'bsc': os.getenv('BSC_PROVIDER', ''),
    'polygon': os.getenv('POLYGON_PROVIDER', ''),
    'arbitrum': os.getenv('ARB_PROVIDER', ''),
    'tron': os.getenv('TRON_PROVIDER', ''),
    'sui': os.getenv('SUI_PROVIDER', ''),
}

# Payment Configuration
PAYMENT_CONFIG = {
    'usdt_eth_contract': os.getenv('USDT_ETH_CONTRACT', ''),
    'usdt_bsc_contract': os.getenv('USDT_BSC_CONTRACT', ''),
    'wallet_address': os.getenv('PAYMENT_WALLET_ADDRESS', ''),
    'wallet_private_key': os.getenv('PAYMENT_WALLET_PRIVATE_KEY', ''),
}

# Email Configuration
EMAIL_CONFIG = {
    'enabled': os.getenv('EMAIL_ENABLED', 'False').lower() in ('true', '1', 't'),
    'service': os.getenv('EMAIL_SERVICE', ''),
    'port': int(os.getenv('EMAIL_PORT', 587)),
    'username': os.getenv('EMAIL_USERNAME', ''),
    'password': os.getenv('EMAIL_PASSWORD', ''),
    'from_email': os.getenv('EMAIL_FROM', ''),
}

# Service pricing (USDT)
PRICING = {
    'token_check': float(os.getenv('TOKEN_CHECK_PRICE', 5.0)),
    'detailed_analysis': float(os.getenv('DETAILED_ANALYSIS_PRICE', 15.0)),
    'monitor_per_day': float(os.getenv('MONITOR_PRICE_PER_DAY', 1.0)),
}

# Supported blockchains
SUPPORTED_BLOCKCHAINS = {
    'eth': {
        'name': 'Ethereum',
        'symbol': 'ETH',
        'icon': '🔹',
    },
    'bsc': {
        'name': 'Binance Smart Chain',
        'symbol': 'BSC',
        'icon': '🟡',
    },
    'polygon': {
        'name': 'Polygon',
        'symbol': 'MATIC',
        'icon': '🟣',
    },
    'arbitrum': {
        'name': 'Arbitrum',
        'symbol': 'ARB',
        'icon': '🔵',
    },
    'tron': {
        'name': 'Tron',
        'symbol': 'TRX',
        'icon': '🔴',
    },
    'sui': {
        'name': 'Sui',
        'symbol': 'SUI',
        'icon': '🔘',
    },
} 