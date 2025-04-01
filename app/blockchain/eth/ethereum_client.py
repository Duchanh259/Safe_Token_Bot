#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ethereum blockchain client.
Handles interaction with Ethereum blockchain and Etherscan API.
"""

import os
import json
import re
import aiohttp
import asyncio
from web3 import Web3
from etherscan import Etherscan
from typing import Dict, List, Any, Optional, Union
from app.utils.logger import get_logger
from config.config import BLOCKCHAIN_API_KEYS, WEB3_PROVIDERS

logger = get_logger(__name__)

class EthereumClient:
    """Client for Ethereum blockchain interactions."""
    
    def __init__(self):
        """Initialize Ethereum client."""
        # Get API keys and provider URLs from config
        self.etherscan_api_key = BLOCKCHAIN_API_KEYS.get('eth', '')
        self.eth_provider_url = WEB3_PROVIDERS.get('eth', '')
        
        # Initialize Web3 provider
        if self.eth_provider_url:
            self.web3 = Web3(Web3.HTTPProvider(self.eth_provider_url))
            logger.info(f"Web3 connection: {'Connected' if self.web3.is_connected() else 'Failed'}")
        else:
            self.web3 = None
            logger.warning("ETH_PROVIDER URL not configured")
        
        # Initialize Etherscan client
        if self.etherscan_api_key:
            self.etherscan = Etherscan(self.etherscan_api_key)
            logger.info("Etherscan API client initialized")
        else:
            self.etherscan = None
            logger.warning("ETHERSCAN_API_KEY not configured")
        
        # Addresses and ABI
        self._init_addresses_and_abi()
        
        # Precompile regex patterns
        self._compile_regex_patterns()
    
    def _init_addresses_and_abi(self):
        """Initialize addresses and ABI definitions."""
        # DEX Addresses
        self.dex_addresses = {
            'uniswap_v2_factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
            'uniswap_v3_factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
            'sushiswap_factory': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac'
        }
        
        # Locker Contract Addresses
        self.locker_addresses = {
            'unicrypt': '0x663A5C229c09b049E36dCc11a9B0d4a8Eb9db214',
            'team_finance': '0xE2fE530C047f2d85298b07D9333C05737f1435fB',
            'pink_lock': '0x71B5759d73262FBb223956913ecF4ecC51057641'
        }
        
        # ERC20 ABI for token interactions
        self.erc20_abi = [
            # Transfer event
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
            # Balance of function
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
            # Decimals function
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"},
            # Total supply function
            {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
            # Symbol function
            {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
            # Name function
            {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
        ]
        
        # Factory ABI (minimal for pair checking)
        self.factory_abi = [
            {"inputs": [{"internalType": "address", "name": "tokenA", "type": "address"},
                       {"internalType": "address", "name": "tokenB", "type": "address"}],
             "name": "getPair",
             "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
             "stateMutability": "view",
             "type": "function"}
        ]
        
        # Locker ABI (minimal for lock checking)
        self.locker_abi = [
            {"inputs": [{"internalType": "address", "name": "token", "type": "address"}],
             "name": "getLockedTokens",
             "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
             "stateMutability": "view",
             "type": "function"}
        ]
    
    def _compile_regex_patterns(self):
        """Precompile regex patterns for better performance."""
        # Owner detection patterns
        self.owner_methods = [
            'owner', 'getOwner', 'admin', 'getAdmin', 'governance', 
            'authority', 'manager', 'controller', 'masterMinter',
            'administrator', 'adminAddress', 'contractOwner', 'creator',
            'deployer', 'dev', 'treasury', 'team', 'operator',
            'master', 'executor', 'moderator', 'superAdmin', 'supervisor'
        ]
        
        # Security check patterns
        self.blacklist_mapping_patterns = re.compile(
            '|'.join([f"mapping.*{term}" for term in [
                'blacklist', 'blocklist', 'blacklisted', 'banned', 'excluded', 
                'excluida', 'restricted', 'blocked', 'frozen', 'denylist', 
                'ban', 'sanctions', 'isrestricted', 'isblacklisted', 
                'frozenAccount', 'lockAccount', 'frozenAddresses', 'lockedAddresses'
            ]]),
            re.IGNORECASE
        )
        
        self.selfdestruct_pattern = re.compile(
            'selfdestruct\(|suicide\(|self\.destruct|destroy\(address',
            re.IGNORECASE
        )
        
        self.pause_patterns = re.compile(
            '|'.join([
                'function pause', 'whennotpaused', 'whenpaused', '_paused', 
                'paused\(\)', 'ispause', 'function toggletrading', 'trading = false',
                'enabletrading', 'disabletrading', 'tradingenabled', 'tradingactive',
                'tradingstatus', 'function tradingStatus', '_tradingOpen',
                'tradingOpen', 'tradingEnabled', 'function enableTrading',
                'function disableTrading', '_tradingEnabled', 'function setTrading'
            ]),
            re.IGNORECASE
        )
        
        # Function extraction pattern
        self.function_pattern = re.compile(
            r"function\s+(\w+)\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
            re.DOTALL | re.IGNORECASE
        )
        
    async def get_token_information(self, token_address: str) -> Dict[str, Any]:
        """
        Get basic token information using Web3 and Etherscan.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Dictionary with token information
        """
        if not self.web3 or not self.web3.is_connected():
            return {"error": "Web3 connection not available"}
        
        if not Web3.is_address(token_address):
            return {"error": "Invalid Ethereum address format"}
        
        try:
            # Initialize token contract
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.erc20_abi
            )
            
            # Get basic token information
            token_info = {
                "address": token_address,
                "name": None,
                "symbol": None,
                "decimals": None,
                "total_supply": None,
                "is_contract": None,
                "verified": None,
                "creation_date": None,
                "owner": None,
                "owner_full": None,
                "owner_link": None,
                "owner_html": None
            }
            
            # Get token metadata (name, symbol, etc.)
            self._get_token_metadata(token_contract, token_info)
            
            # Find contract owner
            await self._find_contract_owner(token_address, token_info, token_contract)
            
            # Check if address is a contract
            token_info["is_contract"] = self.web3.eth.get_code(Web3.to_checksum_address(token_address)) != "0x"
            
            # Get contract verification status from Etherscan
            self._get_verification_status(token_address, token_info)
            
            return token_info
            
        except Exception as e:
            logger.error(f"Error in get_token_information: {str(e)}")
            return {"error": str(e)}
    
    def _get_token_metadata(self, token_contract, token_info):
        """Get token metadata like name, symbol, decimals, and total supply."""
        try:
            token_info["name"] = token_contract.functions.name().call()
            token_info["symbol"] = token_contract.functions.symbol().call()
            token_info["decimals"] = token_contract.functions.decimals().call()
            total_supply = token_contract.functions.totalSupply().call()
            token_info["total_supply"] = total_supply / (10 ** token_info["decimals"])
        except Exception as e:
            logger.error(f"Error getting token information: {str(e)}")
    
    async def _find_contract_owner(self, token_address, token_info, token_contract):
        """Find contract owner using multiple strategies."""
        try:
            owner_address = None
            
            # Strategy 1: Check common owner methods
            owner_address = self._check_owner_methods(token_contract)
            
            # Strategy 2: Check Etherscan source code
            if not owner_address and self.etherscan:
                owner_address = await self._check_source_code_for_owner(token_address)
            
            # Strategy 3: Check if contract is a proxy
            if not owner_address and self.etherscan_api_key:
                owner_address = await self._check_proxy_implementation(token_address)
            
            # Strategy 4: Check ownership events
            if not owner_address and self.etherscan_api_key:
                owner_address = await self._check_ownership_events(token_address)
            
            # Strategy 5: Check contract creator
            if not owner_address and self.etherscan_api_key:
                owner_address = await self._check_contract_creator(token_address)
            
            # Save owner info to token_info
            if owner_address and Web3.is_address(owner_address):
                token_info["owner_full"] = owner_address
                token_info["owner_link"] = f"https://etherscan.io/address/{owner_address}"
                token_info["owner"] = owner_address[:6] + "..." + owner_address[-4:]
            else:
                token_info["owner"] = "N/A"
                token_info["owner_full"] = None
                token_info["owner_link"] = None
                token_info["owner_html"] = "N/A"
        except Exception as e:
            logger.error(f"Error getting contract owner: {str(e)}")
            token_info["owner"] = "N/A"
            token_info["owner_full"] = None
            token_info["owner_link"] = None
            token_info["owner_html"] = "N/A"
    
    def _check_owner_methods(self, token_contract):
        """Check common contract methods to find owner."""
        for method in self.owner_methods:
            if hasattr(token_contract.functions, method):
                try:
                    owner_address = getattr(token_contract.functions, method)().call()
                    if owner_address and Web3.is_address(owner_address):
                        return owner_address
                except Exception as e:
                    logger.debug(f"Error calling {method}(): {str(e)}")
        return None
    
    async def _check_source_code_for_owner(self, token_address):
        """Check contract source code for owner information."""
        try:
            source_info = self.etherscan.get_contract_source_code(token_address)
            
            if not source_info or len(source_info) == 0:
                return None
                
            # Check ABI for owner methods
            if source_info[0].get("ABI") and source_info[0].get("ABI") != "Contract source code not verified":
                try:
                    contract_abi = json.loads(source_info[0].get("ABI"))
                    full_contract = self.web3.eth.contract(
                        address=Web3.to_checksum_address(token_address),
                        abi=contract_abi
                    )
                    
                    return self._check_owner_methods(full_contract)
                except Exception as e:
                    logger.debug(f"Error creating contract with full ABI: {str(e)}")
            
            # Check source code for owner patterns
            source_code = source_info[0].get("SourceCode", "")
            if source_code:
                # Check for Ownable patterns
                ownable_patterns = ["is Ownable", "contract Ownable", "import.*Ownable", "using Ownable"]
                if any(pattern in source_code for pattern in ownable_patterns):
                    # Look for transferOwnership in constructor
                    constructor_pattern = r"constructor\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
                    constructor_match = re.search(constructor_pattern, source_code, re.DOTALL)
                    
                    if constructor_match:
                        constructor_body = constructor_match.group(1)
                        transfer_pattern = r"(?:_)?transferOwnership\s*\(\s*([^)]+)\s*\)"
                        transfer_match = re.search(transfer_pattern, constructor_body)
                        
                        if transfer_match:
                            owner_param = transfer_match.group(1).strip()
                            if owner_param.startswith('0x') and len(owner_param) >= 40:
                                return owner_param
                
                # Check state variables for owner
                state_patterns = [
                    r"address\s+(?:public|private|internal)?\s+owner\s*=\s*([^;]+)",
                    r"address\s+(?:public|private|internal)?\s+admin\s*=\s*([^;]+)",
                    r"address\s+(?:public|private|internal)?\s+governance\s*=\s*([^;]+)",
                    r"address\s+(?:public|private|internal)?\s+_owner\s*=\s*([^;]+)"
                ]
                
                for pattern in state_patterns:
                    state_match = re.search(pattern, source_code)
                    if state_match:
                        owner_value = state_match.group(1).strip()
                        if owner_value.startswith('0x') and len(owner_value) >= 40:
                            return owner_value.strip()
            
            return None
        except Exception as e:
            logger.warning(f"Error getting owner from Etherscan source code: {str(e)}")
            return None
    
    async def _check_proxy_implementation(self, token_address):
        """Check if contract is a proxy and get implementation owner."""
        try:
            async with aiohttp.ClientSession() as session:
                # Check EIP-1967 implementation slot
                try:
                    implementation_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
                    implementation_address = self.web3.eth.get_storage_at(
                        Web3.to_checksum_address(token_address), 
                        Web3.to_hex(hexstr=implementation_slot)
                    )
                    
                    if implementation_address and int(implementation_address.hex(), 16) != 0:
                        implementation_address = '0x' + implementation_address.hex()[-40:]
                        implementation_address = Web3.to_checksum_address(implementation_address)
                        
                        proxy_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={implementation_address}&apikey={self.etherscan_api_key}"
                        
                        async with session.get(proxy_url) as resp:
                            if resp.status == 200:
                                proxy_data = await resp.json()
                                
                                if proxy_data["status"] == "1" and len(proxy_data["result"]) > 0:
                                    impl_abi = proxy_data["result"][0].get("ABI")
                                    if impl_abi and impl_abi != "Contract source code not verified":
                                        impl_contract = self.web3.eth.contract(
                                            address=Web3.to_checksum_address(token_address),
                                            abi=json.loads(impl_abi)
                                        )
                                        
                                        return self._check_owner_methods(impl_contract)
                except Exception as e:
                    logger.debug(f"Error checking EIP-1967 proxy: {str(e)}")
                
                # Check proxy from Etherscan API
                proxy_check_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={self.etherscan_api_key}"
                async with session.get(proxy_check_url) as resp:
                    if resp.status == 200:
                        proxy_data = await resp.json()
                        
                        if proxy_data["status"] == "1" and len(proxy_data["result"]) > 0:
                            if proxy_data["result"][0].get("Implementation"):
                                impl_address = proxy_data["result"][0].get("Implementation")
                                if Web3.is_address(impl_address):
                                    impl_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={impl_address}&apikey={self.etherscan_api_key}"
                                    
                                    async with session.get(impl_url) as impl_resp:
                                        if impl_resp.status == 200:
                                            impl_data = await impl_resp.json()
                                            
                                            if impl_data["status"] == "1" and len(impl_data["result"]) > 0:
                                                impl_abi = impl_data["result"][0].get("ABI")
                                                if impl_abi and impl_abi != "Contract source code not verified":
                                                    combined_abi = json.loads(proxy_data["result"][0].get("ABI", "[]"))
                                                    combined_abi.extend(json.loads(impl_abi))
                                                    
                                                    combined_contract = self.web3.eth.contract(
                                                        address=Web3.to_checksum_address(token_address),
                                                        abi=combined_abi
                                                    )
                                                    
                                                    return self._check_owner_methods(combined_contract)
            return None
        except Exception as e:
            logger.warning(f"Error checking proxy contract: {str(e)}")
            return None
    
    async def _check_ownership_events(self, token_address):
        """Check OwnershipTransferred events to find current owner."""
        try:
            async with aiohttp.ClientSession() as session:
                events_url = f"https://api.etherscan.io/api?module=logs&action=getLogs&address={token_address}&topic0=0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0&apikey={self.etherscan_api_key}"
                async with session.get(events_url) as resp:
                    if resp.status == 200:
                        events_data = await resp.json()
                        
                        if events_data["status"] == "1" and len(events_data["result"]) > 0:
                            latest_event = events_data["result"][-1]
                            
                            if len(latest_event["topics"]) >= 3:
                                new_owner = "0x" + latest_event["topics"][2][-40:]
                                if Web3.is_address(new_owner):
                                    return Web3.to_checksum_address(new_owner)
            return None
        except Exception as e:
            logger.warning(f"Error checking ownership events: {str(e)}")
            return None
    
    async def _check_contract_creator(self, token_address):
        """Check contract creator as potential owner."""
        try:
            async with aiohttp.ClientSession() as session:
                creation_url = f"https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={token_address}&apikey={self.etherscan_api_key}"
                async with session.get(creation_url) as resp:
                    if resp.status == 200:
                        creation_data = await resp.json()
                        
                        if creation_data["status"] == "1" and len(creation_data["result"]) > 0:
                            creator_address = creation_data["result"][0]["contractCreator"]
                            if Web3.is_address(creator_address):
                                return Web3.to_checksum_address(creator_address)
            return None
        except Exception as e:
            logger.warning(f"Error checking contract creator: {str(e)}")
            return None
    
    def _get_verification_status(self, token_address, token_info):
        """Get contract verification status from Etherscan."""
        if self.etherscan:
            try:
                source_code = self.etherscan.get_contract_source_code(token_address)
                token_info["verified"] = len(source_code) > 0 and source_code[0].get("SourceCode", "") != ""
                
                if token_info["verified"]:
                    token_info["compiler_version"] = source_code[0].get("CompilerVersion", "")
                    token_info["license_type"] = source_code[0].get("LicenseType", "")
            except Exception as e:
                logger.error(f"Error getting verification status: {str(e)}")
    
    async def check_liquidity_pools(self, token_address: str) -> Dict[str, Any]:
        """
        Check liquidity pools for a token on major DEXes.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Dictionary with liquidity pool information
        """
        if not self.web3 or not self.web3.is_connected():
            return {"error": "Web3 connection not available"}
        
        result = {
            "has_liquidity": False,
            "pools": [],
            "is_locked": False,
            "lock_info": [],
            "total_liquidity_usd": 0
        }
        
        try:
            # Convert to checksum address
            token_address = Web3.to_checksum_address(token_address)
            weth_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # WETH address
            
            # Check DEX pairs
            await self._check_dex_pairs(token_address, weth_address, result)
            
            # Check liquidity locks
            await self._check_liquidity_locks(token_address, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in check_liquidity_pools: {str(e)}")
            return {"error": str(e)}
    
    async def _check_dex_pairs(self, token_address, weth_address, result):
        """Check DEX pairs for the token."""
        # Check Uniswap V2
        uni_v2_factory = self.web3.eth.contract(
            address=Web3.to_checksum_address(self.dex_addresses['uniswap_v2_factory']),
            abi=self.factory_abi
        )
        uni_v2_pair = uni_v2_factory.functions.getPair(token_address, weth_address).call()
        
        if uni_v2_pair != "0x0000000000000000000000000000000000000000":
            result["has_liquidity"] = True
            result["pools"].append({
                "dex": "Uniswap V2",
                "pair_address": uni_v2_pair,
                "pair_type": "TOKEN/WETH"
            })
        
        # Check SushiSwap
        sushi_factory = self.web3.eth.contract(
            address=Web3.to_checksum_address(self.dex_addresses['sushiswap_factory']),
            abi=self.factory_abi
        )
        sushi_pair = sushi_factory.functions.getPair(token_address, weth_address).call()
        
        if sushi_pair != "0x0000000000000000000000000000000000000000":
            result["has_liquidity"] = True
            result["pools"].append({
                "dex": "SushiSwap",
                "pair_address": sushi_pair,
                "pair_type": "TOKEN/WETH"
            })
    
    async def _check_liquidity_locks(self, token_address, result):
        """Check if liquidity is locked in known lockers."""
        for locker_name, locker_address in self.locker_addresses.items():
            try:
                locker_contract = self.web3.eth.contract(
                    address=Web3.to_checksum_address(locker_address),
                    abi=self.locker_abi
                )
                
                # Check if token is locked
                locked_amount = locker_contract.functions.getLockedTokens(token_address).call()
                
                if locked_amount > 0:
                    result["is_locked"] = True
                    result["lock_info"].append({
                        "locker": locker_name,
                        "amount": locked_amount
                    })
                
                # Check LP tokens if pools exist
                for pool in result["pools"]:
                    locked_lp = locker_contract.functions.getLockedTokens(pool["pair_address"]).call()
                    if locked_lp > 0:
                        result["is_locked"] = True
                        result["lock_info"].append({
                            "locker": locker_name,
                            "pool": pool["dex"],
                            "amount": locked_lp
                        })
            
            except Exception as e:
                logger.warning(f"Error checking {locker_name} locks: {str(e)}")
    
    async def check_token_security(self, token_address: str) -> Dict[str, Any]:
        """
        Check token security issues.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Dictionary with security check results
        """
        if not self.etherscan:
            return {"error": "Etherscan API not configured"}
        
        if not Web3.is_address(token_address):
            return {"error": "Invalid Ethereum address format"}
        
        security_result = {
            "is_honeypot": False,
            "is_verified": False,
            "has_self_destruct": False,
            "has_blacklist": False,
            "has_mint": False,
            "has_pause": False,
            "has_revoke": False,
            "can_renounce_ownership": False,
            "liquidity_status": await self.check_liquidity_pools(token_address),
            "security_score": 0,
            "issues": []
        }
        
        try:
            # Get contract source code
            source_code = self.etherscan.get_contract_source_code(token_address)
            
            # Check if contract is verified
            if len(source_code) > 0 and source_code[0].get("SourceCode", "") != "":
                security_result["is_verified"] = True
                
                # Get the source code as string
                contract_source = source_code[0].get("SourceCode", "")
                
                # Run all security checks
                await self._run_security_checks(contract_source, security_result)
            else:
                security_result["issues"].append("Contract source code not verified")
            
            # Calculate security score
            security_result["security_score"] = self._calculate_security_score(security_result)
            
            return security_result
            
        except Exception as e:
            logger.error(f"Error in check_token_security: {str(e)}")
            return {"error": str(e)}
    
    async def _run_security_checks(self, contract_source, security_result):
        """Run all security checks on the contract source."""
        # 1. Check for self-destruct function
        self._check_selfdestruct(contract_source, security_result)
        
        # 2. Check for blacklist function
        self._check_blacklist(contract_source, security_result)
        
        # 3. Check for pause functions
        self._check_pause_function(contract_source, security_result)
        
        # 4. Check for revoke/modification functions
        self._check_revoke_functions(contract_source, security_result)
        
        # 5. Check for ownership renouncing capabilities
        self._check_ownership_renouncing(contract_source, security_result)
        
        # 6. Check for mint capability
        self._check_mint_capability(contract_source, security_result)
        
        # 7. Check for honeypot indicators
        self._check_honeypot_indicators(contract_source, security_result)
    
    def _check_selfdestruct(self, contract_source, security_result):
        """Check for self-destruct functionality."""
        if self.selfdestruct_pattern.search(contract_source.lower()):
            # Extract context around matches
            for term in ["selfdestruct(", "suicide(", "self.destruct", "destroy(address"]:
                start_idx = 0
                while True:
                    idx = contract_source.lower().find(term, start_idx)
                    if idx == -1:
                        break
                    
                    # Get context
                    ctx_start = max(0, idx - 30)
                    ctx_end = min(len(contract_source), idx + len(term) + 30)
                    context = contract_source[ctx_start:ctx_end]
                    
                    # Skip if in comment
                    if "//" in context[:context.lower().find(term)] or \
                       ("/*" in context[:context.lower().find(term)] and "*/" in context[context.lower().find(term):]):
                        start_idx = idx + len(term)
                        continue
                        
                    security_result["has_self_destruct"] = True
                    security_result["issues"].append("Contract contains selfdestruct function")
                    return
                    
                    start_idx = idx + len(term)
    
    def _check_blacklist(self, contract_source, security_result):
        """Check for blacklist functionality."""
        # Strategy 1: Check mapping patterns
        if self.blacklist_mapping_patterns.search(contract_source):
            security_result["has_blacklist"] = True
            security_result["issues"].append("Contract contains blacklist/blocklist function")
            return
        
        # Strategy 2: Check function patterns
        blacklist_function_patterns = [
            "function blacklist", "function blocklist", "function addtoblacklist", 
            "function addtoblocklist", "function setblacklisted", "function banaddress",
            "function ban(", "function exclude", "function addToBlockList"
        ]
        
        for pattern in blacklist_function_patterns:
            matches = self._find_matches_excluding_comments(contract_source, pattern)
            if matches and self._validate_blacklist_function(contract_source, pattern, matches):
                security_result["has_blacklist"] = True
                security_result["issues"].append("Contract contains blacklist/blocklist function")
                return
        
        # Strategy 3: Check transfer restrictions in transfer functions
        transfer_functions = self.function_pattern.findall(contract_source)
        for func_name, func_body in transfer_functions:
            if func_name.lower() in ['transfer', '_transfer', 'transferfrom']:
                blacklist_checks = [
                    "if (", "require(!", "require(", "assert(!"
                ]
                
                for check in blacklist_checks:
                    if check in func_body and self._is_likely_blacklist_check(func_body, []):
                        security_result["has_blacklist"] = True
                        security_result["issues"].append("Contract contains transfer restrictions")
                        return
    
    def _check_pause_function(self, contract_source, security_result):
        """Check for pause functionality."""
        if self.pause_patterns.search(contract_source):
            security_result["has_pause"] = True
            security_result["issues"].append("Contract can pause trading/transfers")
            return
        
        # Check transfer functions for pause conditions
        transfer_functions = self.function_pattern.findall(contract_source)
        for func_name, func_body in transfer_functions:
            if func_name.lower() in ['transfer', '_transfer', 'transferfrom']:
                pause_checks = [
                    "require(!paused", "require(!_paused", "require(tradingEnabled", 
                    "if (paused)", "if (_paused)", "if (!tradingEnabled)"
                ]
                
                for check in pause_checks:
                    if check.lower() in func_body.lower():
                        security_result["has_pause"] = True
                        security_result["issues"].append("Contract can pause trading/transfers")
                        return
    
    def _check_revoke_functions(self, contract_source, security_result):
        """Check for functions that can revoke transactions or modify balances."""
        revoke_patterns = [
            "function revoke", "function revert", "function reclaim",
            "function canceltransa", "function canceltx", "function reverttx",
            "function forcetransfer", "function seize", "function confiscate"
        ]
        
        for pattern in revoke_patterns:
            matches = self._find_matches_excluding_comments(contract_source, pattern)
            if matches:
                security_result["has_revoke"] = True
                security_result["issues"].append("Contract can revoke/revert transactions")
                return
        
        # Check admin functions that modify balances
        admin_pattern = r"(function\s+\w+\s*\([^)]*\)[^{]*\s+(onlyOwner|onlyAdmin|ownerOnly|adminOnly|hasRole|onlyRole)[^{]*\{)"
        admin_matches = re.findall(admin_pattern, contract_source, re.IGNORECASE)
        
        for match in admin_matches:
            func_start = contract_source.find(match[0])
            if func_start >= 0:
                # Extract function body
                brace_count = 1
                func_end = func_start + len(match[0])
                for i in range(func_start + len(match[0]), len(contract_source)):
                    if contract_source[i] == '{':
                        brace_count += 1
                    elif contract_source[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            func_end = i
                            break
                
                func_body = contract_source[func_start:func_end]
                balance_patterns = ["_balances[", "balances[", "balanceOf[", ".balance =", "balance +=", "balance -="]
                
                if any(pattern in func_body.lower() for pattern in balance_patterns):
                    security_result["has_revoke"] = True
                    security_result["issues"].append("Contract contains functions that can modify user balances")
                    return
    
    def _check_ownership_renouncing(self, contract_source, security_result):
        """Check for ownership renouncing capabilities."""
        renounce_patterns = ["function renounceownership", "function transferownership"]
        
        for pattern in renounce_patterns:
            matches = self._find_matches_excluding_comments(contract_source, pattern)
            if matches:
                security_result["can_renounce_ownership"] = True
                break
    
    def _check_mint_capability(self, contract_source, security_result):
        """Check for mint capability."""
        # Check function names
        mint_function_names = ["mint", "_mint", "minttoken", "createnewtoken", "create", "issue"]
        
        functions = self.function_pattern.findall(contract_source)
        for func_name, func_body in functions:
            if any(mint_name in func_name.lower() for mint_name in mint_function_names):
                # Skip internal functions that can't be called directly
                if "internal" in func_body.lower() and "external" not in func_body.lower() and "public" not in func_body.lower():
                    if not self._is_internal_function_exposed(contract_source, func_name):
                        continue
                
                security_result["has_mint"] = True
                security_result["issues"].append("Contract contains function to mint additional tokens")
                return
        
        # Check for mint patterns in function bodies
        mint_patterns = ["_mint(", "mint(", "totalSupply +=", "totalSupply.add"]
        
        for func_name, func_body in functions:
            if func_name.lower() == "constructor":
                continue
                
            for pattern in mint_patterns:
                if pattern.lower() in func_body.lower() and not ("burn" in func_name.lower() or "destroy" in func_name.lower()):
                    security_result["has_mint"] = True
                    security_result["issues"].append("Contract contains function to mint additional tokens")
                    return
        
        # Check for ERC20Mintable inheritance
        mintable_patterns = ["contract.*ERC20Mintable", "is.*Mintable", "is.*ERC20Mintable"]
        for pattern in mintable_patterns:
            if re.search(pattern, contract_source, re.IGNORECASE):
                security_result["has_mint"] = True
                security_result["issues"].append("Contract inherits from a mintable token contract")
                return
    
    def _check_honeypot_indicators(self, contract_source, security_result):
        """Check for honeypot indicators."""
        honeypot_indicators = [
            "cannot sell", "cannot transfer", "owner only transfer",
            "require(false)", "revert()", "transfer lock",
            "require(to != pair)", "transferFee > 90", 
            "if(to==pair) { require(false); }", "tax > 50"
        ]
        
        for indicator in honeypot_indicators:
            matches = self._find_matches_excluding_comments(contract_source, indicator)
            if matches:
                security_result["is_honeypot"] = True
                security_result["issues"].append(f"Potential honeypot indicator found: {indicator}")
                return
        
        # Check for high sell taxes
        sell_tax_patterns = [
            r"sell\w*tax\s*=\s*(\d+)",
            r"sell\w*fee\s*=\s*(\d+)",
            r"if\s*\(\s*\w+\s*==\s*pair\s*\)\s*{\s*\w+\s*=\s*(\d+)"
        ]
        
        for pattern in sell_tax_patterns:
            matches = re.findall(pattern, contract_source.lower())
            for match in matches:
                try:
                    tax_value = int(match)
                    if tax_value > 25:  # More than 25% sell tax is suspicious
                        security_result["is_honeypot"] = True
                        security_result["issues"].append(f"Potential honeypot: High sell tax ({tax_value}%)")
                        return
                except:
                    pass
    
    def _calculate_security_score(self, security_result):
        """Calculate security score based on findings."""
        base_score = 100
        
        if not security_result["is_verified"]:
            base_score -= 50  # Unverified contracts are highly risky
        
        if security_result["is_honeypot"]:
            base_score -= 100  # Honeypots are extremely dangerous
        
        if security_result["has_self_destruct"]:
            base_score -= 30  # Self-destruct is very dangerous
        
        if security_result["has_blacklist"]:
            base_score -= 15  # Blacklist is concerning
        
        if security_result["has_mint"]:
            base_score -= 20  # Minting can lead to inflation
        
        if security_result["has_pause"]:
            base_score -= 15  # Pausing can trap investors
        
        if security_result["has_revoke"]:
            base_score -= 25  # Direct balance modification is very dangerous
        
        # Check for liquidity lock status
        if security_result["liquidity_status"].get("has_liquidity", False):
            if security_result["liquidity_status"].get("is_locked", False):
                base_score += 10  # Locked liquidity is good
            else:
                base_score -= 15  # Unlocked liquidity is risky
        else:
            base_score -= 10  # No liquidity pools is concerning
        
        # Ensure score stays within 0-100 range
        return max(0, min(100, base_score))
    
    def _find_matches_excluding_comments(self, source_code: str, pattern: str) -> List[str]:
        """
        Find all matches of a pattern in source code, excluding matches in comments.
        
        Args:
            source_code: Source code to search in
            pattern: Pattern to search for
            
        Returns:
            List of matches excluding those in comments
        """
        matches = []
        source_lower = source_code.lower()
        pattern_lower = pattern.lower()
        
        # Find all occurrences of the pattern
        start_idx = 0
        while True:
            idx = source_lower.find(pattern_lower, start_idx)
            if idx == -1:
                break
            
            # Check if pattern is within a comment
            line_start = source_lower.rfind("\n", 0, idx) + 1
            comment_start = source_lower.rfind("//", line_start, idx)
            
            # Check if pattern is within a block comment
            block_comment_start = source_lower.rfind("/*", 0, idx)
            block_comment_end = source_lower.rfind("*/", 0, idx)
            in_block_comment = block_comment_start > block_comment_end
            
            # If not in a comment, add to matches
            if comment_start == -1 and not in_block_comment:
                # Get some context (10 chars before and after)
                ctx_start = max(0, idx - 10)
                ctx_end = min(len(source_code), idx + len(pattern) + 10)
                context = source_code[ctx_start:ctx_end]
                matches.append(context)
            
            # Move to the next occurrence
            start_idx = idx + len(pattern_lower)
        
        return matches
    
    def _is_internal_function_exposed(self, contract_source: str, internal_func_name: str) -> bool:
        """Check if an internal function is exposed through other public/external functions."""
        func_call_pattern = f"{internal_func_name}\\s*\\("
        
        # Extract all public/external functions
        public_funcs_pattern = r"function\s+(\w+)\s*\([^)]*\)[^{]*(?:public|external)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
        public_funcs = re.findall(public_funcs_pattern, contract_source, re.DOTALL | re.IGNORECASE)
        
        for _, func_body in public_funcs:
            if re.search(func_call_pattern, func_body, re.IGNORECASE):
                return True
                
        return False
    
    def _is_likely_blacklist_check(self, function_body: str, restriction_matches: list) -> bool:
        """Determine if a function body likely contains blacklist checks."""
        # Check for blacklist terms
        blacklist_terms = [
            "blacklist", "blocklist", "banned", "restricted", "frozen", "blocked", 
            "exclude", "deny", "sanction", "lock address", "locked", "freeze"
        ]
        
        function_body_lower = function_body.lower()
        if any(term in function_body_lower for term in blacklist_terms):
            return True
        
        # Check for denial patterns
        transfer_denial_patterns = [
            "require", "assert", "revert", "return false", "cannot", "failed", 
            "rejected", "unauthorized", "not authorized"
        ]
        
        return any(term in function_body_lower for term in transfer_denial_patterns)
    
    def _validate_blacklist_function(self, contract_source: str, pattern: str, matches: List[str]) -> bool:
        """Validate if a found pattern is likely to be a real blacklist function."""
        # Extract the function name
        function_name = pattern.replace("function ", "").split("(")[0].strip()
        
        # Find the complete function in the source code
        function_start_idx = contract_source.lower().find(pattern.lower())
        if function_start_idx == -1:
            return False
            
        # Get parameter section
        param_start = contract_source.find("(", function_start_idx)
        param_end = contract_source.find(")", param_start)
        params = contract_source[param_start+1:param_end]
        
        # Check for address parameters
        has_address_param = "address" in params.lower()
        
        # Find opening brace
        opening_brace_idx = contract_source.find("{", function_start_idx)
        if opening_brace_idx == -1:
            return False
            
        # Find matching closing brace
        brace_count = 1
        function_end_idx = opening_brace_idx + 1
        while brace_count > 0 and function_end_idx < len(contract_source):
            if contract_source[function_end_idx] == '{':
                brace_count += 1
            elif contract_source[function_end_idx] == '}':
                brace_count -= 1
            function_end_idx += 1
            
        # Extract function body
        function_body = contract_source[opening_brace_idx+1:function_end_idx]
        
        # Check for typical patterns in blacklist functions
        blacklist_indicators = ["= true", "= false", "[", "mappings", "mapping", "revert", "require"]
        
        # A real blacklist function should have address parameters and some indicators
        return has_address_param and any(indicator in function_body.lower() for indicator in blacklist_indicators)

# Create singleton instance
ethereum_client = EthereumClient()