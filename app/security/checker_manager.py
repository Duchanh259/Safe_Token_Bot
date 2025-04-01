#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manages token security checkers.
"""

import asyncio
from typing import Dict, Any
from app.utils.logger import get_logger
from app.security.eth_token_checker import eth_token_checker

logger = get_logger(__name__)


class CheckerManager:
    """Manages token security checkers."""
    
    def __init__(self):
        """Initialize checker manager."""
        # Register checkers for different blockchains
        self.checkers = {
            'eth': eth_token_checker,
            # Add other blockchain checkers as they get implemented
            # 'bsc': bsc_token_checker,
            # 'polygon': polygon_token_checker,
        }
        logger.info("Checker manager initialized")
    
    async def check_token(self, token_address: str, blockchain: str) -> Dict[str, Any]:
        """
        Check token security.
        
        Args:
            token_address: Token contract address
            blockchain: Blockchain name (eth, bsc, etc.)
            
        Returns:
            Dictionary with check results
        """
        logger.info(f"Checking token {token_address} on {blockchain}")
        
        # Normalize blockchain name
        blockchain = blockchain.lower()
        
        # Get appropriate checker for the blockchain
        checker = self.checkers.get(blockchain)
        
        if not checker:
            logger.warning(f"No checker available for blockchain {blockchain}")
            return {
                "status": "error",
                "error": f"Unsupported blockchain: {blockchain}",
                "valid": False
            }
        
        try:
            # Perform the check
            result = await checker.check_token(token_address)
            return result
            
        except Exception as e:
            logger.error(f"Error checking token {token_address} on {blockchain}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "valid": False
            }


# Create singleton instance
checker_manager = CheckerManager() 