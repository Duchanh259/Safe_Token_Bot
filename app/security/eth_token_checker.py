#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ethereum token security checker.
Checks security issues in Ethereum tokens.
"""

import asyncio
from typing import Dict, Any, List, Optional
from web3 import Web3
from app.utils.logger import get_logger
from app.blockchain.eth import ethereum_client

logger = get_logger(__name__)

class EthTokenChecker:
    """Ethereum token security checker."""
    
    def __init__(self):
        """Initialize Ethereum token checker."""
        logger.info("Ethereum token checker initialized")
    
    async def check_token(self, token_address: str) -> Dict[str, Any]:
        """
        Check Ethereum token security and information.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Dictionary with token check results
        """
        try:
            # Run both information retrieval and security checks concurrently
            token_info_task = asyncio.create_task(ethereum_client.get_token_information(token_address))
            security_check_task = asyncio.create_task(ethereum_client.check_token_security(token_address))
            
            # Await all tasks
            token_info = await token_info_task
            security_result = await security_check_task
            
            # Check for errors
            if "error" in token_info:
                return {
                    "status": "error",
                    "error": token_info["error"],
                    "valid": False
                }
            
            # Combine all results
            result = {
                "status": "success",
                "valid": True,
                "blockchain": "eth",
                "token": token_info,
                "security": security_result,
                "risk_level": self._determine_risk_level(security_result),
                "issues": self._format_issues(security_result)
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error in check_token: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "valid": False
            }
    
    def _determine_risk_level(self, security_result: Dict[str, Any]) -> str:
        """
        Determine risk level based on security score.
        
        Args:
            security_result: Security check result
            
        Returns:
            Risk level string (critical, high, medium, low, safe)
        """
        score = security_result.get("security_score", 0)
        
        if score < 20:
            return "critical"
        elif score < 40:
            return "high"
        elif score < 70:
            return "medium"
        elif score < 90:
            return "low"
        else:
            return "safe"
    
    def _format_issues(self, security_result: Dict[str, Any]) -> List[str]:
        """
        Format security issues list.
        
        Args:
            security_result: Security check result
            
        Returns:
            List of formatted issues
        """
        issues = []
        
        # Add issues from security result
        if "issues" in security_result:
            issues.extend(security_result["issues"])
        
        # Add standard issues based on flags
        if security_result.get("is_honeypot", False):
            issues.append("Contract appears to be a honeypot")
        if not security_result.get("is_verified", True):
            issues.append("Contract is not verified on Etherscan")
        
        return issues


# Create singleton instance
eth_token_checker = EthTokenChecker() 