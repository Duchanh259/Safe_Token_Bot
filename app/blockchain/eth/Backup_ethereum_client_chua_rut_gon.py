#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ethereum blockchain client.
Handles interaction with Ethereum blockchain and Etherscan API.
"""

import os
import json
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
            
            # Get token name, symbol, decimals, and total supply
            try:
                token_info["name"] = token_contract.functions.name().call()
                token_info["symbol"] = token_contract.functions.symbol().call()
                token_info["decimals"] = token_contract.functions.decimals().call()
                total_supply = token_contract.functions.totalSupply().call()
                token_info["total_supply"] = total_supply / (10 ** token_info["decimals"])
            except Exception as e:
                logger.error(f"Error getting token information: {str(e)}")
            
            # Try to get contract owner if possible
            try:
                owner_address = None
                
                # Mở rộng danh sách phương thức để lấy địa chỉ owner
                owner_methods = [
                    'owner', 'getOwner', 'admin', 'getAdmin', 'governance', 
                    'authority', 'manager', 'controller', 'masterMinter',
                    'administrator', 'adminAddress', 'contractOwner', 'creator',
                    'deployer', 'dev', 'treasury', 'team', 'operator',
                    'master', 'executor', 'moderator', 'superAdmin', 'supervisor'
                ]
                
                # Kiểm tra các phương thức để lấy địa chỉ owner
                for method in owner_methods:
                    if hasattr(token_contract.functions, method):
                        try:
                            owner_address = getattr(token_contract.functions, method)().call()
                            if owner_address and Web3.is_address(owner_address):
                                break
                        except Exception as e:
                            logger.debug(f"Error calling {method}(): {str(e)}")
                            continue
                
                # Nếu không lấy được owner từ các method phổ biến, thử các phương pháp khác
                if (not owner_address or not Web3.is_address(owner_address)) and self.etherscan:
                    try:
                        # Lấy source code và ABI từ Etherscan
                        source_info = self.etherscan.get_contract_source_code(token_address)
                        
                        if len(source_info) > 0:
                            # 1. Kiểm tra ABI
                            if source_info[0].get("ABI") and source_info[0].get("ABI") != "Contract source code not verified":
                                try:
                                    contract_abi = json.loads(source_info[0].get("ABI"))
                                    
                                    # Kiểm tra trong ABI có hàm owner không
                                    for item in contract_abi:
                                        if item.get("name") in owner_methods and item.get("type") == "function" and item.get("stateMutability") == "view":
                                            # Tạo contract mới với ABI đầy đủ
                                            try:
                                                full_contract = self.web3.eth.contract(
                                                    address=Web3.to_checksum_address(token_address),
                                                    abi=contract_abi
                                                )
                                                
                                                for method in owner_methods:
                                                    if hasattr(full_contract.functions, method):
                                                        try:
                                                            potential_owner = getattr(full_contract.functions, method)().call()
                                                            if potential_owner and Web3.is_address(potential_owner):
                                                                owner_address = potential_owner
                                                                break
                                                        except Exception as e:
                                                            logger.debug(f"Error calling {method}() with full ABI: {str(e)}")
                                                            continue
                                            except Exception as e:
                                                logger.debug(f"Error creating contract with full ABI: {str(e)}")
                                
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Error parsing contract ABI: {str(e)}")
                            
                            # 2. Kiểm tra source code cho các pattern phổ biến về owner
                            source_code = source_info[0].get("SourceCode", "")
                            if not owner_address and source_code:
                                # Tìm kiếm trong source code cho địa chỉ được khai báo
                                # Kiểm tra xem có sử dụng Ownable của OpenZeppelin không
                                ownable_patterns = [
                                    "is Ownable", 
                                    "contract Ownable", 
                                    "import.*Ownable", 
                                    "using Ownable"
                                ]
                                
                                has_ownable = any(pattern in source_code for pattern in ownable_patterns)
                                if has_ownable:
                                    # Nếu sử dụng Ownable, tìm kiếm việc chuyển owner trong constructor
                                    try:
                                        import re
                                        # Tìm constructor
                                        constructor_pattern = r"constructor\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
                                        constructor_match = re.search(constructor_pattern, source_code, re.DOTALL)
                                        
                                        if constructor_match:
                                            constructor_body = constructor_match.group(1)
                                            
                                            # Tìm transferOwnership hoặc _transferOwnership trong constructor
                                            transfer_pattern = r"(?:_)?transferOwnership\s*\(\s*([^)]+)\s*\)"
                                            transfer_match = re.search(transfer_pattern, constructor_body)
                                            
                                            if transfer_match:
                                                # Có thể owner được set trong constructor
                                                owner_param = transfer_match.group(1).strip()
                                                
                                                # Nếu là địa chỉ tĩnh, lấy luôn địa chỉ đó
                                                if owner_param.startswith('0x') and len(owner_param) >= 40:
                                                    owner_address = owner_param
                                                # Nếu là tham số, tìm định nghĩa tham số
                                                else:
                                                    # Tìm trong constructor parameters
                                                    param_pattern = r"constructor\s*\(\s*[^)]*" + owner_param + r"\s*:\s*address[^)]*\)"
                                                    if re.search(param_pattern, source_code):
                                                        # Tham số là địa chỉ, nhưng không thể biết giá trị từ source code
                                                        # Cần kiểm tra transaction tạo contract
                                                        pass
                                    except Exception as e:
                                        logger.debug(f"Error parsing constructor for owner: {str(e)}")
                                
                                # Kiểm tra xác định owner trong biến state
                                if not owner_address:
                                    try:
                                        import re
                                        # Tìm biến state owner/admin được khai báo
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
                                                # Nếu là địa chỉ tĩnh
                                                if owner_value.startswith('0x') and len(owner_value) >= 40:
                                                    owner_address = owner_value.strip()
                                                    break
                                    except Exception as e:
                                        logger.debug(f"Error parsing state variables for owner: {str(e)}")
                    except Exception as e:
                        logger.warning(f"Error getting owner from Etherscan source code: {str(e)}")
                
                # 3. Kiểm tra xem contract có phải là proxy không
                if (not owner_address or not Web3.is_address(owner_address)) and self.etherscan_api_key:
                    try:
                        async with aiohttp.ClientSession() as session:
                            # Kiểm tra proxy EIP-1967
                            try:
                                # Kiểm tra implementation slot EIP-1967
                                implementation_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
                                implementation_address = self.web3.eth.get_storage_at(
                                    Web3.to_checksum_address(token_address), 
                                    Web3.to_hex(hexstr=implementation_slot)
                                )
                                
                                # Chuyển đổi bytes sang địa chỉ
                                if implementation_address and int(implementation_address.hex(), 16) != 0:
                                    implementation_address = '0x' + implementation_address.hex()[-40:]
                                    implementation_address = Web3.to_checksum_address(implementation_address)
                                    
                                    # Lấy ABI và source code của implementation
                                    proxy_params = f"module=contract&action=getsourcecode&address={implementation_address}&apikey={self.etherscan_api_key}"
                                    proxy_url = f"https://api.etherscan.io/api?{proxy_params}"
                                    
                                    async with session.get(proxy_url) as resp:
                                        if resp.status == 200:
                                            proxy_data = await resp.json()
                                            
                                            if proxy_data["status"] == "1" and len(proxy_data["result"]) > 0:
                                                try:
                                                    impl_abi = proxy_data["result"][0].get("ABI")
                                                    if impl_abi and impl_abi != "Contract source code not verified":
                                                        impl_contract = self.web3.eth.contract(
                                                            address=Web3.to_checksum_address(token_address),
                                                            abi=json.loads(impl_abi)
                                                        )
                                                        
                                                        # Thử các phương thức owner trên implementation contract
                                                        for method in owner_methods:
                                                            if hasattr(impl_contract.functions, method):
                                                                try:
                                                                    owner_address = getattr(impl_contract.functions, method)().call()
                                                                    if owner_address and Web3.is_address(owner_address):
                                                                        break
                                                                except Exception as e:
                                                                    logger.debug(f"Error calling {method}() on implementation contract: {str(e)}")
                                                                    continue
                                                except Exception as e:
                                                    logger.debug(f"Error getting implementation contract: {str(e)}")
                            except Exception as e:
                                logger.debug(f"Error checking EIP-1967 proxy: {str(e)}")
                            
                            # Kiểm tra proxy chung từ Etherscan API
                            if not owner_address or not Web3.is_address(owner_address):
                                proxy_check_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={self.etherscan_api_key}"
                                async with session.get(proxy_check_url) as resp:
                                    if resp.status == 200:
                                        proxy_data = await resp.json()
                                        
                                        if proxy_data["status"] == "1" and len(proxy_data["result"]) > 0:
                                            # Kiểm tra nếu contract là proxy
                                            if proxy_data["result"][0].get("Implementation"):
                                                impl_address = proxy_data["result"][0].get("Implementation")
                                                if Web3.is_address(impl_address):
                                                    # Lấy ABI của implementation
                                                    impl_params = f"module=contract&action=getsourcecode&address={impl_address}&apikey={self.etherscan_api_key}"
                                                    impl_url = f"https://api.etherscan.io/api?{impl_params}"
                                                    
                                                    async with session.get(impl_url) as impl_resp:
                                                        if impl_resp.status == 200:
                                                            impl_data = await impl_resp.json()
                                                            
                                                            if impl_data["status"] == "1" and len(impl_data["result"]) > 0:
                                                                try:
                                                                    impl_abi = impl_data["result"][0].get("ABI")
                                                                    if impl_abi and impl_abi != "Contract source code not verified":
                                                                        # Nối proxy ABI với implementation ABI
                                                                        try:
                                                                            combined_abi = json.loads(proxy_data["result"][0].get("ABI", "[]"))
                                                                            combined_abi.extend(json.loads(impl_abi))
                                                                            
                                                                            combined_contract = self.web3.eth.contract(
                                                                                address=Web3.to_checksum_address(token_address),
                                                                                abi=combined_abi
                                                                            )
                                                                            
                                                                            # Thử các phương thức owner trên combined contract
                                                                            for method in owner_methods:
                                                                                if hasattr(combined_contract.functions, method):
                                                                                    try:
                                                                                        owner_address = getattr(combined_contract.functions, method)().call()
                                                                                        if owner_address and Web3.is_address(owner_address):
                                                                                            break
                                                                                    except Exception as e:
                                                                                        logger.debug(f"Error calling {method}() on combined contract: {str(e)}")
                                                                                        continue
                                                                        except Exception as e:
                                                                            logger.debug(f"Error creating combined contract: {str(e)}")
                                                                except Exception as e:
                                                                    logger.debug(f"Error parsing implementation ABI: {str(e)}")
                    except Exception as e:
                        logger.warning(f"Error checking proxy contract: {str(e)}")
                
                # 4. Kiểm tra từ các event để tìm owner
                if (not owner_address or not Web3.is_address(owner_address)) and self.etherscan_api_key:
                    try:
                        async with aiohttp.ClientSession() as session:
                            # Tìm event OwnershipTransferred
                            events_url = f"https://api.etherscan.io/api?module=logs&action=getLogs&address={token_address}&topic0=0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0&apikey={self.etherscan_api_key}"
                            async with session.get(events_url) as resp:
                                if resp.status == 200:
                                    events_data = await resp.json()
                                    
                                    if events_data["status"] == "1" and len(events_data["result"]) > 0:
                                        # Lấy event gần nhất
                                        latest_event = events_data["result"][-1]
                                        
                                        # Parse topics (topic 2 là new owner)
                                        if len(latest_event["topics"]) >= 3:
                                            new_owner = "0x" + latest_event["topics"][2][-40:]
                                            if Web3.is_address(new_owner):
                                                owner_address = Web3.to_checksum_address(new_owner)
                    except Exception as e:
                        logger.warning(f"Error checking ownership events: {str(e)}")
                
                # 5. Nếu không tìm thấy owner với các phương pháp trên, thử kiểm tra contract creator
                if (not owner_address or not Web3.is_address(owner_address)) and self.etherscan_api_key:
                    try:
                        async with aiohttp.ClientSession() as session:
                            # Lấy transaction tạo contract
                            creation_url = f"https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={token_address}&apikey={self.etherscan_api_key}"
                            async with session.get(creation_url) as resp:
                                if resp.status == 200:
                                    creation_data = await resp.json()
                                    
                                    if creation_data["status"] == "1" and len(creation_data["result"]) > 0:
                                        creator_address = creation_data["result"][0]["contractCreator"]
                                        if Web3.is_address(creator_address):
                                            # Trong nhiều trường hợp, contract creator cũng là owner
                                            if not owner_address:
                                                owner_address = Web3.to_checksum_address(creator_address)
                    except Exception as e:
                        logger.warning(f"Error checking contract creator: {str(e)}")
                
                if owner_address and Web3.is_address(owner_address):
                    # Lưu cả địa chỉ đầy đủ và địa chỉ rút gọn
                    token_info["owner_full"] = owner_address
                    # Tạo URL Etherscan cho địa chỉ owner
                    token_info["owner_link"] = f"https://etherscan.io/address/{owner_address}"
                    # Tạo địa chỉ rút gọn dạng 0xABC...XYZ (6 ký tự đầu, 4 ký tự cuối)
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
            
            # Check if address is a contract
            token_info["is_contract"] = self.web3.eth.get_code(Web3.to_checksum_address(token_address)) != "0x"
            
            # Get contract verification status from Etherscan
            if self.etherscan:
                try:
                    # Get source code from Etherscan
                    source_code = self.etherscan.get_contract_source_code(token_address)
                    token_info["verified"] = len(source_code) > 0 and source_code[0].get("SourceCode", "") != ""
                    
                    # Extract contract creation info if available
                    if token_info["verified"]:
                        token_info["compiler_version"] = source_code[0].get("CompilerVersion", "")
                        token_info["license_type"] = source_code[0].get("LicenseType", "")
                except Exception as e:
                    logger.error(f"Error getting verification status: {str(e)}")
            
            return token_info
            
        except Exception as e:
            logger.error(f"Error in get_token_information: {str(e)}")
            return {"error": str(e)}
    
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
            
            # Check liquidity locks
            for locker_name, locker_address in self.locker_addresses.items():
                try:
                    locker_contract = self.web3.eth.contract(
                        address=Web3.to_checksum_address(locker_address),
                        abi=self.locker_abi
                    )
                    
                    # Check if token or its LP tokens are locked
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
            
            return result
            
        except Exception as e:
            logger.error(f"Error in check_liquidity_pools: {str(e)}")
            return {"error": str(e)}
    
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
                
                # 1. Check for self-destruct function
                has_selfdestruct = False
                
                # Method 1: Look for actual selfdestruct/suicide function calls in context
                if "selfdestruct(" in contract_source.lower() or "suicide(" in contract_source.lower() or "self.destruct" in contract_source.lower() or "destroy(address" in contract_source.lower():
                    # Extract context around the selfdestruct call
                    for term in ["selfdestruct(", "suicide(", "self.destruct", "destroy(address"]:
                        if term in contract_source.lower():
                            # Find all occurrences of the term
                            start_idx = 0
                            while True:
                                idx = contract_source.lower().find(term, start_idx)
                                if idx == -1:
                                    break
                                
                                # Get context (30 chars before and after)
                                ctx_start = max(0, idx - 30)
                                ctx_end = min(len(contract_source), idx + 30)
                                context = contract_source[ctx_start:ctx_end]
                                
                                # Skip if it's in a comment
                                if "//" in context[:context.lower().find(term)]:
                                    start_idx = idx + len(term)
                                    continue
                                
                                # Skip if it's in a comment block
                                if "/*" in context[:context.lower().find(term)] and "*/" in context[context.lower().find(term):]:
                                    start_idx = idx + len(term)
                                    continue
                                
                                # It's likely a real selfdestruct call
                                has_selfdestruct = True
                                break
                                
                            if has_selfdestruct:
                                break
                
                # Method 2: Look for function definitions that include selfdestruct
                if not has_selfdestruct:
                    selfdestruct_functions = []
                    try:
                        # Extract functions containing selfdestruct
                        functions_parts = contract_source.lower().split("function ")
                        for part in functions_parts[1:]:
                            # Extract function definition
                            if "{" in part:
                                function_def = part.split("{")[0]
                                function_body = part.split("{", 1)[1].split("}", 1)[0] if "}" in part else part
                                
                                # Check if function body contains selfdestruct or related terms
                                if "selfdestruct" in function_body or "suicide" in function_body or "self.destruct" in function_body or "destroy(address" in function_body or "delete this" in function_body:
                                    selfdestruct_functions.append(function_def)
                    except Exception as e:
                        logger.warning(f"Error parsing selfdestruct functions: {e}")
                    
                    if selfdestruct_functions:
                        has_selfdestruct = True
                
                if has_selfdestruct:
                    security_result["has_self_destruct"] = True
                    security_result["issues"].append("Contract contains selfdestruct function")
                
                # 2. Check for blacklist function - improved detection with more comprehensive approach
                has_blacklist = False
                
                # Method 1: Look for blacklist mappings with enhanced patterns
                blacklist_mapping_patterns = [
                    "mapping.*blacklist", 
                    "mapping.*blocklist",
                    "mapping.*blacklisted",
                    "mapping.*banned",
                    "mapping.*excluded",
                    "mapping.*excluida",
                    "mapping.*restricted",
                    "mapping.*blocked",
                    "mapping.*frozen",
                    "mapping.*denylist",
                    "mapping.*ban",
                    "mapping.*sanctions",
                    "mapping.*isrestricted",
                    "mapping.*isblacklisted",
                    "mapping.*frozenAccount",
                    "mapping.*lockAccount",
                    "mapping.*frozenAddresses",
                    "mapping.*lockedAddresses"
                ]
                
                for pattern in blacklist_mapping_patterns:
                    matches = self._find_matches_excluding_comments(contract_source, pattern)
                    if matches:
                        has_blacklist = True
                        break
                
                # Method 2: Look for simple variable declarations that might store blacklist status
                if not has_blacklist:
                    blacklist_var_declarations = [
                        "bool.*blacklisted", 
                        "bool.*blocklisted",
                        "bool.*banned",
                        "bool.*restricted",
                        "bool.*blocked",
                        "bool.*frozen",
                        "address.*blacklisted"
                    ]
                    
                    for pattern in blacklist_var_declarations:
                        matches = self._find_matches_excluding_comments(contract_source, pattern)
                        if matches:
                            has_blacklist = True
                            break
                
                # Method 3: Look for blacklist functions with more comprehensive patterns
                if not has_blacklist:
                    blacklist_function_patterns = [
                        "function blacklist", 
                        "function blocklist",
                        "function addtoblacklist", 
                        "function addtoblocklist",
                        "function setblacklisted", 
                        "function setblocklisted",
                        "function banaddress",
                        "function ban(",
                        "function exclude",
                        "function addToBlockList",
                        "function blockAddress",
                        "function restrictAddress",
                        "function freezeAddress",
                        "function setRestricted",
                        "function addToExcluded",
                        "function denyAccount",
                        "function blockAccount",
                        "function setBlocked",
                        "function excludeAccount",
                        "function addBan",
                        "function setFrozen",
                        "function lock(address",
                        "function lockAddress",
                        "function sanction",
                        "function freeze(",
                        "function freezeAccount",
                        "function blockUser",
                        "function setUnTradable",
                        "function setNotTrading",
                        "function banUser",
                        "function setTransferBlock"
                    ]
                    
                    for pattern in blacklist_function_patterns:
                        matches = self._find_matches_excluding_comments(contract_source, pattern)
                        if matches:
                            # Validate that this is likely a proper blacklist function by checking context
                            is_valid_blacklist = self._validate_blacklist_function(contract_source, pattern, matches)
                            if is_valid_blacklist:
                                has_blacklist = True
                                break
                
                # Method 4: Look for blacklist-like variables and checks with expanded patterns
                if not has_blacklist:
                    blacklist_var_patterns = [
                        "_blacklisted", 
                        "_blocklisted",
                        "blacklisted[", 
                        "blocklisted[",
                        "isblacklisted", 
                        "isblocklisted",
                        "require(!blacklisted", 
                        "require(!blocklisted",
                        "isexcluded",
                        "isbanned",
                        "_blocked",
                        "blocked[",
                        "restricted[",
                        "isrestricted",
                        "isfrozen",
                        "frozen[",
                        "banned[",
                        "denied[",
                        "denylist[",
                        "isblocked",
                        "require(!restricted",
                        "require(!frozen",
                        "require(! blocked",
                        "require(!isblacklisted",
                        "frozenAccount[",
                        "lockedAccount[",
                        "require(!frozenAccount",
                        "require(!lockedAccount"
                    ]
                    
                    for pattern in blacklist_var_patterns:
                        matches = self._find_matches_excluding_comments(contract_source, pattern)
                        if matches:
                            has_blacklist = True
                            break
                
                # Method 5: Look for direct transfer restrictions within _transfer functions
                if not has_blacklist:
                    # Check the content of all _transfer, transfer and transferFrom functions 
                    try:
                        import re
                        transfer_function_patterns = [
                            r"function\s+_transfer\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
                            r"function\s+transfer\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
                            r"function\s+transferFrom\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
                        ]
                        
                        restriction_checks = [
                            r"if\s*\([^)]*\[\s*([a-zA-Z0-9_]+)\s*\]\s*\)",
                            r"require\s*\(\s*!\s*[^)]*\[\s*([a-zA-Z0-9_]+)\s*\]\s*\)",
                            r"require\s*\(\s*[^)]*\[\s*([a-zA-Z0-9_]+)\s*\]\s*==\s*false\s*\)",
                            r"assert\s*\(\s*!\s*[^)]*\[\s*([a-zA-Z0-9_]+)\s*\]\s*\)",
                            r"canTransfer\s*\(([^)]*)\)",
                            r"_canTransfer\s*\(([^)]*)\)",
                            r"isAllowed\s*\(([^)]*)\)",
                            r"isBlocked\s*\(([^)]*)\)",
                            r"isRestricted\s*\(([^)]*)\)",
                            r"isFrozen\s*\(([^)]*)\)",
                            r"isLocked\s*\(([^)]*)\)",
                            r"if\s*\([^)]*==\s*false\s*\)",
                            r"if\s*\(\s*[^)]*msg\.sender[^)]*\)\s*{[^}]*revert",
                            r"if\s*\(\s*[^)]*from[^)]*\)\s*{[^}]*revert",
                            r"if\s*\(\s*[^)]*to[^)]*\)\s*{[^}]*revert"
                        ]
                        
                        for func_pattern in transfer_function_patterns:
                            transfer_funcs = re.findall(func_pattern, contract_source, re.DOTALL | re.IGNORECASE)
                            
                            for func_body in transfer_funcs:
                                # Look for any restriction checks within the function body
                                for restriction in restriction_checks:
                                    restriction_matches = re.findall(restriction, func_body, re.IGNORECASE | re.DOTALL)
                                    if restriction_matches:
                                        # Examine context to ensure it's likely a blacklist and not just a standard check
                                        if self._is_likely_blacklist_check(func_body, restriction_matches):
                                            has_blacklist = True
                                            break
                                
                                if has_blacklist:
                                    break
                            
                            if has_blacklist:
                                break
                    except Exception as e:
                        logger.warning(f"Error in transfer function blacklist detection: {e}")
                
                # Method 6: Advanced regex analysis for transfer restrictions based on address
                if not has_blacklist:
                    try:
                        # Look for restrictions in transfer functions
                        transfer_restriction_patterns = [
                            r"function\s+transfer.*\{.*require\s*\(\s*.*\!\s*([a-zA-Z0-9_]+)\s*\[\s*([a-zA-Z0-9_]+)\s*\]\s*\)",
                            r"function\s+transfer.*\{.*if\s*\(\s*([a-zA-Z0-9_]+)\s*\[\s*([a-zA-Z0-9_]+)\s*\]\s*\)\s*revert",
                            r"function\s+transferFrom.*\{.*require\s*\(\s*.*\!\s*([a-zA-Z0-9_]+)\s*\[\s*([a-zA-Z0-9_]+)\s*\]\s*\)",
                            r"function\s+transferFrom.*\{.*if\s*\(\s*([a-zA-Z0-9_]+)\s*\[\s*([a-zA-Z0-9_]+)\s*\]\s*\)\s*revert",
                            r"function\s+_transfer.*\{.*require\s*\(\s*.*\!\s*([a-zA-Z0-9_]+)\s*\[\s*([a-zA-Z0-9_]+)\s*\]\s*\)",
                            r"function\s+_transfer.*\{.*if\s*\(\s*([a-zA-Z0-9_]+)\s*\[\s*([a-zA-Z0-9_]+)\s*\]\s*\)\s*revert"
                        ]
                        
                        for pattern in transfer_restriction_patterns:
                            matches = re.findall(pattern, contract_source, re.DOTALL | re.IGNORECASE)
                            if matches:
                                # For each mapping name, check if it's likely a blacklist
                                for mapping_name, _ in matches:
                                    mapping_name_lower = mapping_name.lower()
                                    # Check with a broader set of blacklist-related terms
                                    if self._is_blacklist_mapping_name(mapping_name_lower):
                                        has_blacklist = True
                                        break
                                
                                # Also do a broader context check
                                if not has_blacklist:
                                    for mapping_name, var_name in matches:
                                        # Find the whole function containing this check
                                        func_start = max(0, contract_source.lower().find(pattern.split('\\{')[0].replace('\\s*', ' ').lower()))
                                        if func_start > 0:
                                            # Get a wide context (500 chars around)
                                            context_start = max(0, func_start - 100)
                                            context_end = min(len(contract_source), func_start + 600)
                                            func_context = contract_source[context_start:context_end]
                                            
                                            # Look for blacklist terms near this check
                                            if self._has_blacklist_terms_in_context(func_context):
                                                has_blacklist = True
                                                break
                                
                                if has_blacklist:
                                    break
                        
                        # Search for functions that prevent transfers if conditions are met
                        if not has_blacklist:
                            transfer_block_patterns = [
                                r"canTransfer\(address\s+([a-zA-Z0-9_]+)\)\s*.*\{",
                                r"_beforeTokenTransfer\(.*\{.*require\(",
                                r"function\s+transfer.*\{\s*.*\s*require\((\w+)\(",
                                r"function\s+_transfer.*\{\s*.*\s*if\s*\(!\s*(\w+)\(",
                                r"_isBlacklisted\(address\s+([a-zA-Z0-9_]+)\)\s*.*\{",
                                r"_validateTransfer\(.*\{",
                                r"_authorizeTransfer\(.*\{",
                                r"validateTransfer\(.*\{",
                                r"checkTransferAllowed\(.*\{"
                            ]
                            
                            for pattern in transfer_block_patterns:
                                matches = re.findall(pattern, contract_source, re.DOTALL | re.IGNORECASE)
                                if matches:
                                    # Look around these functions to find blacklist-related terms
                                    for match in matches:
                                        # Convert to string if it's not already (can be tuple)
                                        if isinstance(match, tuple):
                                            match = match[0]
                                        
                                        # Find the function context
                                        func_pattern = pattern.replace('\\(', '\\s*\\(').replace('\\{', '\\s*\\{')
                                        func_match = re.search(func_pattern, contract_source, re.DOTALL | re.IGNORECASE)
                                        if func_match:
                                            func_start_idx = func_match.start()
                                            # Get a wider context around this area
                                            context_start = max(0, func_start_idx - 300)
                                            context_end = min(len(contract_source), func_start_idx + 500)
                                            function_context = contract_source[context_start:context_end]
                                            
                                            # Check for blacklist terms in context with broader terms list
                                            if self._has_blacklist_terms_in_context(function_context):
                                                has_blacklist = True
                                                break
                                
                                if has_blacklist:
                                    break
                    except Exception as e:
                        logger.warning(f"Error in advanced blacklist detection: {e}")
                
                # Method 7: Check for OpenZeppelin AccessControl implementation with blacklist roles
                if not has_blacklist:
                    try:
                        # Look for role-based access control with blacklist-related roles
                        role_patterns = [
                            r"bytes32\s+.*\s+(\w+_ROLE)\s*=",
                            r"constant\s+bytes32\s+(\w+_ROLE)\s*=",
                            r"hasRole\((\w+_ROLE)",
                            r"grantRole\((\w+_ROLE)"
                        ]
                        
                        for pattern in role_patterns:
                            matches = re.findall(pattern, contract_source, re.DOTALL | re.IGNORECASE)
                            for role_name in matches:
                                role_name_lower = role_name.lower()
                                if self._is_blacklist_mapping_name(role_name_lower):
                                    has_blacklist = True
                                    break
                            
                            if has_blacklist:
                                break
                    except Exception as e:
                        logger.warning(f"Error in role-based blacklist detection: {e}")
                
                # Method 8: Check for inheritance from blacklist-related contracts
                if not has_blacklist:
                    try:
                        # Look for contract inheritance that suggests blacklist functionality
                        inheritance_patterns = [
                            r"contract\s+\w+\s+is\s+([^{]*)Blacklist",
                            r"contract\s+\w+\s+is\s+([^{]*)Blocklist",
                            r"contract\s+\w+\s+is\s+([^{]*)Freezable",
                            r"contract\s+\w+\s+is\s+([^{]*)Restrictable",
                            r"contract\s+\w+\s+is\s+([^{]*)AddressFilter",
                            r"contract\s+\w+\s+is\s+([^{]*)TransferRestriction",
                            r"contract\s+\w+\s+is\s+([^{]*)Pausable",
                            r"contract\s+\w+\s+is\s+([^{]*)Lockable"
                        ]
                        
                        for pattern in inheritance_patterns:
                            if re.search(pattern, contract_source, re.IGNORECASE | re.DOTALL):
                                has_blacklist = True
                                break
                    except Exception as e:
                        logger.warning(f"Error in inheritance-based blacklist detection: {e}")
                
                # Method 9: Check for events that suggest blacklist functionality
                if not has_blacklist:
                    try:
                        # Look for events related to blacklisting
                        event_patterns = [
                            r"event\s+(\w*Blacklist\w*)\(",
                            r"event\s+(\w*Block\w*Address\w*)\(",
                            r"event\s+(\w*Freeze\w*)\(",
                            r"event\s+(\w*Ban\w*)\(",
                            r"event\s+(\w*Lock\w*Address\w*)\(",
                            r"event\s+(\w*Restrict\w*)\("
                        ]
                        
                        for pattern in event_patterns:
                            if re.search(pattern, contract_source, re.IGNORECASE | re.DOTALL):
                                has_blacklist = True
                                break
                    except Exception as e:
                        logger.warning(f"Error in event-based blacklist detection: {e}")
                
                if has_blacklist:
                    security_result["has_blacklist"] = True
                    security_result["issues"].append("Contract contains blacklist/blocklist function")
                
                # 3. Check for pause functions that can pause trading/transfers - enhanced detection
                has_pause = False
                
                # Method 1: Look for explicit pause functions and variables
                pause_patterns = [
                    "function pause", 
                    "whennotpaused", 
                    "whenpaused",
                    "_paused", 
                    "paused()", 
                    "ispause",
                    "function toggletrading",
                    "trading = false",
                    "enabletrading",
                    "disabletrading",
                    "tradingenabled",
                    "tradingactive",
                    "tradingstatus",
                    "function tradingStatus",
                    "_tradingOpen",
                    "tradingOpen",
                    "tradingEnabled",
                    "function enableTrading",
                    "function disableTrading",
                    "_tradingEnabled",
                    "function setTrading"
                ]
                
                for pattern in pause_patterns:
                    matches = self._find_matches_excluding_comments(contract_source, pattern)
                    if matches:
                        # Validate that this is likely a pause function/variable and not a false positive
                        if self._validate_pause_match(contract_source, pattern, matches):
                            has_pause = True
                            break
                
                # Method 2: Check for inheritance from Pausable contracts
                if not has_pause:
                    try:
                        import re
                        # Common Pausable contract inheritance patterns
                        pausable_inheritance_patterns = [
                            r"contract\s+\w+\s+is\s+([^{]*)Pausable",
                            r"contract\s+\w+\s+is\s+([^{]*)Freezable",
                            r"contract\s+\w+\s+is\s+([^{]*)TradingControl",
                            r"import\s+[\"'].*Pausable[\"']",
                            r"import\s+[\"'].*Trading[\"']",
                            r"import\s+.*IPausable",
                            r"import\s+.*pausable/Pausable"
                        ]
                        
                        for pattern in pausable_inheritance_patterns:
                            if re.search(pattern, contract_source, re.IGNORECASE | re.DOTALL):
                                has_pause = True
                                break
                    except Exception as e:
                        logger.warning(f"Error in pausable inheritance analysis: {e}")
                
                # Method 3: Check for pause-related events
                if not has_pause:
                    try:
                        # Look for events related to pausing
                        pause_event_patterns = [
                            r"event\s+(\w*Pause\w*)\(",
                            r"event\s+(\w*Trading\w*)\(",
                            r"event\s+(\w*Freeze\w*)\(",
                            r"event\s+TradingEnabled\(",
                            r"event\s+TradingDisabled\("
                        ]
                        
                        for pattern in pause_event_patterns:
                            if re.search(pattern, contract_source, re.IGNORECASE | re.DOTALL):
                                has_pause = True
                                break
                    except Exception as e:
                        logger.warning(f"Error in pause event detection: {e}")
                
                # Method 4: Check for code that allows buying but not selling (enhanced)
                if not has_pause:
                    buy_sell_patterns = [
                        "if (from == pair && to != pair)",  # Typical pattern to restrict selling
                        "require(to == pair)",
                        "if (from == pair) {",
                        "sellblocked",
                        "require(canSell)",
                        "can_sell = false",
                        "sellEnabled",
                        "sellsEnabled",
                        "enableSells",
                        "disableSells",
                        "selling_enabled",
                        "sellingEnabled",
                        "require(selling_enabled)",
                        "_swapEnabled",
                        "swapsEnabled",
                        "swapEnabled",
                        "function enableSwap",
                        "function disableSwap"
                    ]
                    
                    for pattern in buy_sell_patterns:
                        matches = self._find_matches_excluding_comments(contract_source, pattern)
                        if matches:
                            has_pause = True
                            break
                
                # Method 5: Deep analysis of transfer functions for pause conditions
                if not has_pause:
                    try:
                        # Look for conditions in transfer functions that can disable transfers
                        transfer_function_patterns = [
                            r"function\s+_transfer\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
                            r"function\s+transfer\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
                            r"function\s+transferFrom\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
                        ]
                        
                        # Patterns that indicate transfer can be paused
                        transfer_pause_patterns = [
                            r"require\s*\(\s*(!?\s*paused)",
                            r"require\s*\(\s*(!?\s*_paused)",
                            r"require\s*\(\s*(tradingEnabled|_tradingEnabled|isTradingEnabled|tradingOpen|_tradingOpen)",
                            r"if\s*\(\s*paused\s*\)\s*revert",
                            r"if\s*\(\s*_paused\s*\)\s*revert",
                            r"if\s*\(\s*!tradingEnabled\s*\)\s*revert",
                            r"if\s*\(\s*!_tradingEnabled\s*\)\s*revert",
                            r"onlyWhenTradingEnabled",
                            r"onlyWhenNotPaused",
                            r"whenNotPaused",
                            r"modifier\s+onlyWhenTradingEnabled",
                            r"require\s*\(\s*canTransfer\("
                        ]
                        
                        # Check for pause patterns in transfer functions
                        for func_pattern in transfer_function_patterns:
                            transfer_funcs = re.findall(func_pattern, contract_source, re.DOTALL | re.IGNORECASE)
                            
                            for func_body in transfer_funcs:
                                # Look for any pause patterns within the function body
                                for pause_pattern in transfer_pause_patterns:
                                    if re.search(pause_pattern, func_body, re.IGNORECASE | re.DOTALL):
                                        has_pause = True
                                        break
                                
                                if has_pause:
                                    break
                                
                        # Check for canTransfer or similar helper methods
                        if not has_pause:
                            can_transfer_patterns = [
                                r"function\s+canTransfer\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
                                r"function\s+_canTransfer\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
                                r"function\s+_beforeTokenTransfer\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
                                r"function\s+_beforeTransfer\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
                            ]
                            
                            for func_pattern in can_transfer_patterns:
                                funcs = re.findall(func_pattern, contract_source, re.DOTALL | re.IGNORECASE)
                                
                                for func_body in funcs:
                                    # Look for trading status checks in these functions
                                    trading_check_patterns = [
                                        r"paused", r"_paused", r"tradingEnabled", r"_tradingEnabled", 
                                        r"tradingOpen", r"_tradingOpen", r"swapEnabled", r"_swapEnabled"
                                    ]
                                    
                                    for check in trading_check_patterns:
                                        if check.lower() in str(func_body).lower():
                                            has_pause = True
                                            break
                                    
                                    if has_pause:
                                        break
                    except Exception as e:
                        logger.warning(f"Error in transfer pause analysis: {e}")
                
                # Method 6: Check for onlyOwner functions that can control trading
                if not has_pause:
                    try:
                        # Pattern for onlyOwner functions
                        onlyowner_patterns = [
                            r"function\s+(\w+)\s*\([^)]*\)[^{]*\s+onlyOwner\s*[^{]*\{",
                            r"function\s+(\w+)\s*\([^)]*\)[^{]*\s+only\(owner\)\s*[^{]*\{",
                            r"function\s+(\w+)\s*\([^)]*\)[^{]*\s+onlyRole\([^)]*\)\s*[^{]*\{"
                        ]
                        
                        for pattern in onlyowner_patterns:
                            owner_funcs = re.findall(pattern, contract_source, re.DOTALL | re.IGNORECASE)
                            
                            for func_name in owner_funcs:
                                # Check if function name suggests trading control
                                func_name_lower = func_name.lower() if isinstance(func_name, str) else func_name[0].lower()
                                trading_control_names = [
                                    "pause", "unpause", "settrading", "enabletrading", "disabletrading",
                                    "toggletrading", "setpause", "pausetrading", "resumetrading", 
                                    "freezetrading", "unfreezetrading", "changetradingstatus"
                                ]
                                
                                if any(control_name in func_name_lower for control_name in trading_control_names):
                                    has_pause = True
                                    break
                            
                            if has_pause:
                                break
                    except Exception as e:
                        logger.warning(f"Error in onlyOwner trading control analysis: {e}")
                
                if has_pause:
                    security_result["has_pause"] = True
                    security_result["issues"].append("Contract can pause trading/transfers")
                
                # 4. Check for functions that can revoke/revert transactions or modify balances
                revoke_patterns = [
                    "function revoke", 
                    "function revert", 
                    "function reclaim",
                    "function canceltransa", 
                    "function canceltx", 
                    "function reverttx",
                    "function forcetransfer",
                    "function seize",
                    "function confiscate",
                    "function recover",
                    "function withdraw("
                ]
                
                # Patterns for directly modifying balances
                balance_modify_patterns = [
                    "_balances[",
                    "balances[",
                    "balanceOf[",
                    "_balanceOf[",
                    ".balance =",
                    "balance +=",
                    "balance -=",
                    ".transfer(",
                    ".transferFrom(",
                    "forceTransfer",
                    "_transfer",
                    "burnFrom",
                    "burn(",
                    "_burn",
                    "setBalance"
                ]
                
                # Check for revoke functions
                revoke_function_found = False
                for pattern in revoke_patterns:
                    matches = self._find_matches_excluding_comments(contract_source, pattern)
                    if matches:
                        revoke_function_found = True
                        security_result["has_revoke"] = True
                        security_result["issues"].append("Contract can revoke/revert transactions")
                        break
                
                # Check for admin functions that can modify balances
                if not revoke_function_found:
                    try:
                        # Mẫu để tìm các hàm có modifier onlyOwner/onlyAdmin và các phương thức tương tự
                        admin_pattern = r"(function\s+\w+\s*\([^)]*\)[^{]*\s+(onlyOwner|onlyAdmin|ownerOnly|adminOnly|hasRole|onlyRole)[^{]*\{)"
                        import re
                        admin_matches = re.findall(admin_pattern, contract_source, re.IGNORECASE)
                        
                        for match in admin_matches:
                            # Extract function content
                            func_body_start = contract_source.find(match[0]) + len(match[0])
                            
                            # Find the matching closing brace
                            brace_count = 1
                            func_body_end = func_body_start
                            for i in range(func_body_start, len(contract_source)):
                                if contract_source[i] == '{':
                                    brace_count += 1
                                elif contract_source[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        func_body_end = i
                                        break
                            
                            func_body = contract_source[func_body_start:func_body_end]
                            
                            # Check if function contains balance modification patterns
                            for pattern in balance_modify_patterns:
                                if pattern.lower() in func_body.lower():
                                    security_result["has_revoke"] = True
                                    security_result["issues"].append("Contract contains functions that can modify user balances")
                                    revoke_function_found = True
                                    break
                            
                            if revoke_function_found:
                                break
                            
                        # Kiểm tra các hàm được bảo vệ bằng điều kiện "require(msg.sender == owner)" hoặc tương tự
                        if not revoke_function_found:
                            func_pattern = r"function\s+(\w+)\s*\([^)]*\)[^{]*\{"
                            func_matches = re.findall(func_pattern, contract_source, re.IGNORECASE)
                            
                            for func_name in func_matches:
                                # Lấy nội dung hàm
                                func_start_idx = contract_source.lower().find(f"function {func_name.lower()}")
                                if func_start_idx != -1:
                                    # Tìm đoạn mã của hàm
                                    next_func_idx = contract_source.lower().find("function ", func_start_idx + 1)
                                    if next_func_idx != -1:
                                        function_context = contract_source[func_start_idx:next_func_idx]
                                    else:
                                        function_context = contract_source[func_start_idx:]
                                    
                                    # Kiểm tra xem hàm có kiểm tra owner hay không
                                    has_owner_check = any(check in function_context.lower() for check in [
                                        "require(msg.sender == owner", 
                                        "require(owner == msg.sender",
                                        "if(msg.sender == owner)",
                                        "if (msg.sender == owner)",
                                        "require(msg.sender == _owner",
                                        "require(_owner == msg.sender"
                                    ])
                                    
                                    # Kiểm tra xem hàm có chứa mẫu sửa đổi số dư không
                                    if has_owner_check:
                                        for pattern in balance_modify_patterns:
                                            if pattern.lower() in function_context.lower():
                                                security_result["has_revoke"] = True
                                                security_result["issues"].append("Contract contains owner functions that can modify user balances")
                                                revoke_function_found = True
                                                break
                                
                                if revoke_function_found:
                                    break
                    except Exception as e:
                        logger.warning(f"Error analyzing admin functions: {e}")
                
                # 5. Check for ownership renouncing capabilities
                renounce_patterns = [
                    "function renounceownership", 
                    "function transferownership"
                ]
                
                for pattern in renounce_patterns:
                    matches = self._find_matches_excluding_comments(contract_source, pattern)
                    if matches:
                        security_result["can_renounce_ownership"] = True
                        break
                
                # 6. Improved mint detection - look for functions to create new tokens
                # Check if this is a fixed supply token
                fixed_supply_patterns = [
                    "constructor.*totalSupply",
                    "_totalSupply.*constructor",
                    "totalSupply =.*constructor",
                    "constructor.*mint",
                    "constructor.*_mint"
                ]
                
                is_likely_fixed_supply = False
                for pattern in fixed_supply_patterns:
                    if pattern.lower() in contract_source.lower():
                        is_likely_fixed_supply = True
                        break
                
                # Check for mint capability regardless of fixed supply categorization
                # Extract function names
                contract_functions = []
                try:
                    functions_parts = contract_source.lower().split("function ")
                    for part in functions_parts[1:]:
                        if "(" in part:
                            function_name = part.split("(")[0].strip()
                            contract_functions.append(function_name)
                except Exception as e:
                    logger.warning(f"Error parsing functions: {e}")
                
                # Expanded list of mint-related function names
                mint_function_names = [
                    "mint", "_mint", "minttoken", "createnewtoken", "create", "issue", 
                    "generatetoken", "addtoken", "allocate", "allocatetoken", "newtoken", 
                    "makenewtoken", "distribute", "emission", "award", "reward", "airdrop", 
                    "tokenmint", "mintto", "addtosupply", "increasesupply", "addtokensto", 
                    "generatenew"
                ]
                
                # Additional patterns to check for in function bodies
                mint_patterns = [
                    "_mint(", 
                    "mint(", 
                    "totalSupply +=", 
                    "totalSupply =", 
                    "balances[", 
                    "_balances[", 
                    ".balanceOf[", 
                    "totalSupply = totalSupply.add", 
                    "_totalSupply = _totalSupply.add",
                    "_totalSupply +=",
                    "balance += amount",
                    ".transfer(",
                    ".transferFrom(",
                    "tokenSupply +="
                ]
                
                has_mint_function = False
                
                # First check: specific function names
                for func_name in contract_functions:
                    if any(mint_name in func_name for mint_name in mint_function_names):
                        # Get the full function context
                        function_context = ""
                        try:
                            func_start_idx = contract_source.lower().find(f"function {func_name}")
                            if func_start_idx != -1:
                                next_func_idx = contract_source.lower().find("function ", func_start_idx + 1)
                                if next_func_idx != -1:
                                    function_context = contract_source[func_start_idx:next_func_idx]
                                else:
                                    function_context = contract_source[func_start_idx:]
                        except Exception as e:
                            logger.warning(f"Error extracting function context: {e}")
                        
                        # Skip internal functions that can't be called directly, but only if they
                        # are truly internal-only (some contracts use mixed visibility)
                        if "internal" in function_context.lower() and "external" not in function_context.lower() and "public" not in function_context.lower():
                            # Still check if the internal function can be called by other public functions
                            if not self._is_internal_function_exposed(contract_source, func_name):
                                continue
                        
                        # Flag as potential mint function
                        has_mint_function = True
                        break
                
                # Second check: function body contains mint patterns
                if not has_mint_function:
                    # Extract all functions with their bodies
                    try:
                        import re
                        # Find all functions
                        function_pattern = r"function\s+(\w+)\s*\([^)]*\)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
                        all_functions = re.findall(function_pattern, contract_source, re.DOTALL | re.IGNORECASE)
                        
                        for func_name, func_body in all_functions:
                            # Skip constructor
                            if func_name.lower() == "constructor":
                                continue
                                
                            # Skip internal-only functions that aren't exposed
                            if "internal" in func_body.lower() and "external" not in func_body.lower() and "public" not in func_body.lower():
                                if not self._is_internal_function_exposed(contract_source, func_name):
                                    continue
                            
                            # Check for mint patterns in function body
                            for pattern in mint_patterns:
                                if pattern.lower() in func_body.lower():
                                    # Avoid false positives with token burning
                                    if "burn" in func_name.lower() or "destroy" in func_name.lower():
                                        continue
                                        
                                    # Further validate that this is likely a mint function
                                    if self._is_likely_mint_function(func_body):
                                        has_mint_function = True
                                        break
                                        
                            if has_mint_function:
                                break
                    except Exception as e:
                        logger.warning(f"Error analyzing function bodies for mint capability: {e}")
                
                # Third check: look for modifiers that can be used for minting
                if not has_mint_function:
                    try:
                        # Find all modifiers
                        modifier_pattern = r"modifier\s+(\w+)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
                        modifiers = re.findall(modifier_pattern, contract_source, re.DOTALL | re.IGNORECASE)
                        
                        for mod_name, mod_body in modifiers:
                            # Check if modifier name suggests minting capability
                            if any(mint_term in mod_name.lower() for mint_term in ["mint", "create", "generate", "issue"]):
                                # Find functions using this modifier
                                func_with_modifier_pattern = f"function\\s+(\\w+)\\s*\\([^)]*\\)[^{{]*{mod_name}[^{{]*\\{{"
                                funcs_with_modifier = re.findall(func_with_modifier_pattern, contract_source, re.IGNORECASE)
                                
                                if funcs_with_modifier:
                                    has_mint_function = True
                                    break
                    except Exception as e:
                        logger.warning(f"Error analyzing modifiers for mint capability: {e}")
                
                # Fourth check: ERC20 inherited templates
                if not has_mint_function:
                    # Check for common ERC20 mintable implementations
                    mintable_contract_patterns = [
                        "contract.*ERC20Mintable", 
                        "contract.*MintableToken",
                        "is.*Mintable", 
                        "is.*ERC20Mintable",
                        "IMintableToken", 
                        "IMintableERC20"
                    ]
                    
                    for pattern in mintable_contract_patterns:
                        if pattern.lower() in contract_source.lower():
                            has_mint_function = True
                            break
                
                # Set final result
                if has_mint_function:
                    security_result["has_mint"] = True
                    security_result["issues"].append("Contract contains function to mint additional tokens")
                
                # 7. Improved honeypot detection - look for patterns that prevent selling
                honeypot_indicators = [
                    "cannot sell", 
                    "cannot transfer", 
                    "owner only transfer",
                    "require(false)",
                    "revert()",
                    "transfer lock",
                    "sellLimit",
                    "maxSellAmount",
                    "require(to != pair)",  # Prevents selling to pairs
                    "require(sender == owner || recipient == owner)",  # Only owner can transfer
                    "transferFee > 90",  # Extremely high sell tax
                    "if(to==pair) { require(false); }",  # Direct prevention of selling
                    "tax > 50",  # Extremely high tax
                    "revert(\"Cannot sell\")"
                ]
                
                for indicator in honeypot_indicators:
                    matches = self._find_matches_excluding_comments(contract_source, indicator)
                    if matches:
                        security_result["is_honeypot"] = True
                        security_result["issues"].append(f"Potential honeypot indicator found: {indicator}")
                        break
                
                # Additional honeypot check - look for high sell taxes compared to buy taxes
                if not security_result["is_honeypot"]:
                    sell_tax_patterns = [
                        r"sell\w*tax\s*=\s*(\d+)",
                        r"sell\w*fee\s*=\s*(\d+)",
                        r"if\s*\(\s*\w+\s*==\s*pair\s*\)\s*{\s*\w+\s*=\s*(\d+)"
                    ]
                    
                    import re
                    for pattern in sell_tax_patterns:
                        matches = re.findall(pattern, contract_source.lower())
                        for match in matches:
                            try:
                                tax_value = int(match)
                                if tax_value > 25:  # More than 25% sell tax is suspicious
                                    security_result["is_honeypot"] = True
                                    security_result["issues"].append(f"Potential honeypot: High sell tax ({tax_value}%)")
                                    break
                            except:
                                pass
                        
                        if security_result["is_honeypot"]:
                            break
            else:
                security_result["issues"].append("Contract source code not verified")
            
            # Calculate security score (0-100)
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
            security_result["security_score"] = max(0, min(100, base_score))
            
            return security_result
            
        except Exception as e:
            logger.error(f"Error in check_token_security: {str(e)}")
            return {"error": str(e)}

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
        """
        Check if an internal function is exposed through other public/external functions.
        
        Args:
            contract_source: Source code to analyze
            internal_func_name: Name of the internal function to check
            
        Returns:
            True if the internal function can be called through public interfaces
        """
        try:
            # Simple check: see if any public/external function calls this internal function
            func_call_pattern = f"{internal_func_name}\\s*\\("
            
            # Extract all public/external functions
            import re
            public_funcs_pattern = r"function\s+(\w+)\s*\([^)]*\)[^{]*(?:public|external)[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
            public_funcs = re.findall(public_funcs_pattern, contract_source, re.DOTALL | re.IGNORECASE)
            
            for _, func_body in public_funcs:
                if re.search(func_call_pattern, func_body, re.IGNORECASE):
                    return True
                    
            return False
            
        except Exception as e:
            logger.warning(f"Error checking if internal function is exposed: {e}")
            # In case of errors, assume it might be exposed (safer)
            return True
            
    def _is_likely_mint_function(self, function_body: str) -> bool:
        """
        Determine if a function is likely to be a minting function based on its body.
        
        Args:
            function_body: Body of the function to analyze
            
        Returns:
            True if the function is likely a mint function
        """
        try:
            # Positive indicators (suggest minting)
            positive_indicators = [
                "_mint(", "mint(", "totalSupply +=", "totalSupply = totalSupply.add", 
                "totalSupply.add", "_totalSupply +=", "_totalSupply.add"
            ]
            
            # Negative indicators (suggest the function is not for minting)
            negative_indicators = [
                "burn(", "_burn(", "destroy(", "totalSupply -=", "totalSupply.sub",
                "_totalSupply -=", "_totalSupply.sub"
            ]
            
            # Check for positive indicators
            has_positive = any(indicator in function_body.lower() for indicator in positive_indicators)
            
            # Check for negative indicators
            has_negative = any(indicator in function_body.lower() for indicator in negative_indicators)
            
            # If has positive but no negative indicators, likely a mint function
            if has_positive and not has_negative:
                return True
                
            # If has both indicators, need more analysis
            if has_positive and has_negative:
                # Check which one seems more prominent
                pos_count = sum(function_body.lower().count(ind) for ind in positive_indicators)
                neg_count = sum(function_body.lower().count(ind) for ind in negative_indicators)
                
                return pos_count > neg_count
                
            return False
            
        except Exception as e:
            logger.warning(f"Error analyzing if function is likely mint: {e}")
            # In case of errors, assume it might be a mint function (safer)
            return True

    def _validate_blacklist_function(self, contract_source: str, pattern: str, matches: List[str]) -> bool:
        """
        Validate if a found pattern is likely to be a real blacklist function.
        
        Args:
            contract_source: Source code to analyze
            pattern: Pattern that was matched
            matches: List of matches found
            
        Returns:
            True if the pattern is likely a real blacklist function
        """
        try:
            # Extract the function name
            function_name = pattern.replace("function ", "").split("(")[0].strip()
            
            # Find the complete function in the source code
            function_start_idx = contract_source.lower().find(pattern.lower())
            if function_start_idx == -1:
                return False
                
            # Get a wider context around this function
            context_start = max(0, function_start_idx - 50)
            # Search for the function opening brace
            opening_brace_idx = contract_source.find("{", function_start_idx)
            if opening_brace_idx == -1:
                return False
                
            # Find the matching closing brace (accounting for nested braces)
            brace_count = 1
            function_end_idx = opening_brace_idx + 1
            while brace_count > 0 and function_end_idx < len(contract_source):
                if contract_source[function_end_idx] == '{':
                    brace_count += 1
                elif contract_source[function_end_idx] == '}':
                    brace_count -= 1
                function_end_idx += 1
                
            # Extract the function body
            function_body = contract_source[opening_brace_idx+1:function_end_idx]
            
            # Check for typical patterns in blacklist functions
            blacklist_indicators = [
                "= true", "= false", "[", "mappings", "mapping", 
                "revert", "require", "emit", "event"
            ]
            
            # At least one indicator should be present in a real blacklist function
            has_indicators = any(indicator in function_body.lower() for indicator in blacklist_indicators)
            
            # Check for address parameters
            param_start = contract_source.find("(", function_start_idx)
            param_end = contract_source.find(")", param_start)
            params = contract_source[param_start+1:param_end]
            has_address_param = "address" in params.lower()
            
            # A real blacklist function should have address parameters and some indicators
            return has_address_param and has_indicators
            
        except Exception as e:
            logger.warning(f"Error validating blacklist function: {e}")
            # In case of error, assume it might be a blacklist (safer)
            return True

    def _is_blacklist_mapping_name(self, name: str) -> bool:
        """
        Check if a mapping name appears to be related to blacklisting/blocking.
        
        Args:
            name: The mapping name to check
            
        Returns:
            True if the name is likely related to blacklisting
        """
        blacklist_terms = [
            "black", "block", "ban", "restrict", "frozen", "exclude", "deny", 
            "sanction", "lock", "disabled", "prohibited", "forbidden", "limited",
            "prevented", "banned", "froze", "dapp", "disabled", "notsend"
        ]
        
        return any(term in name for term in blacklist_terms)
    
    def _has_blacklist_terms_in_context(self, context: str) -> bool:
        """
        Check if a context contains blacklist-related terminology.
        
        Args:
            context: The context string to check
            
        Returns:
            True if the context contains blacklist-related terms
        """
        blacklist_terms = [
            "blacklist", "blocklist", "banned", "restricted", "frozen", "blocked", 
            "exclude", "deny", "sanction", "lock address", "locked", "freeze", 
            "freezing", "restriction", "block transfer", "prevent transfer", 
            "unauthorized", "not allowed", "disable trade", "banned address",
            "restricted address", "cannot transfer", "transfer not allowed"
        ]
        
        context_lower = context.lower()
        return any(term in context_lower for term in blacklist_terms)
    
    def _is_likely_blacklist_check(self, function_body: str, restriction_matches: list) -> bool:
        """
        Determine if a function body likely contains blacklist checks.
        
        Args:
            function_body: The function body to analyze
            restriction_matches: Matches found in restriction check patterns
            
        Returns:
            True if the function likely contains blacklist checks
        """
        # Check if there are restriction terms in the function body
        if self._has_blacklist_terms_in_context(function_body):
            return True
            
        # Check if any of the mapped variables have blacklist-related names
        for match in restriction_matches:
            if isinstance(match, tuple):
                for item in match:
                    if self._is_blacklist_mapping_name(str(item).lower()):
                        return True
            else:
                if self._is_blacklist_mapping_name(str(match).lower()):
                    return True
                    
        # Check if the restriction is in a context that suggests it's denying transfers
        transfer_denial_patterns = [
            "require", "assert", "revert", "return false", "cannot", "failed", 
            "rejected", "unauthorized", "not authorized"
        ]
        
        # Check if the function contains both restriction checks and denial terms
        function_body_lower = function_body.lower()
        return any(term in function_body_lower for term in transfer_denial_patterns)

    def _validate_pause_match(self, contract_source: str, pattern: str, matches: List[str]) -> bool:
        """
        Validates whether a pattern match truly indicates pause functionality.
        
        Args:
            contract_source: Full contract source code
            pattern: The pattern that was matched
            matches: The list of matches found
            
        Returns:
            True if the match likely indicates pause functionality
        """
        try:
            # For variables, check surrounding context
            if "_paused" in pattern or "paused()" in pattern or "ispause" in pattern:
                # For each match, get more context
                for match in matches:
                    # Get the original match location in the full source
                    idx = contract_source.lower().find(match.lower())
                    if idx >= 0:
                        # Get 100 chars around for context
                        start = max(0, idx - 50)
                        end = min(len(contract_source), idx + len(match) + 50)
                        context = contract_source[start:end].lower()
                        
                        # Check for transfer or trading context nearby
                        trading_terms = ["transfer", "trading", "trade", "transaction", "tx", "swap"]
                        if any(term in context for term in trading_terms):
                            return True
                            
                        # Check for usage in require statements or conditions
                        control_terms = ["require", "if", "when", "modifier", "!"]
                        if any(term in context for term in control_terms):
                            return True
                            
                return False  # No relevant context found
            
            # For function patterns like "function pause", check function body
            elif "function" in pattern:
                # Extract function name
                func_name = pattern.replace("function ", "").strip()
                
                # Find the function definition
                func_pattern = f"function\\s+{func_name}\\s*\\([^)]*\\)[^{{]*\\{{([^}}]*(?:\\{{[^}}]*\\}}[^}}]*)*?)\\}}"
                import re
                func_match = re.search(func_pattern, contract_source, re.DOTALL | re.IGNORECASE)
                
                if func_match:
                    func_body = func_match.group(1)
                    
                    # Check if function body contains pause-related actions
                    pause_actions = [
                        "paused = true", "paused=true", "_paused = true", "_paused=true",
                        "tradingEnabled = false", "tradingEnabled=false", 
                        "_tradingEnabled = false", "_tradingEnabled=false",
                        "trading = false", "trading=false",
                        "emit Pause", "emit TradingDisabled"
                    ]
                    
                    if any(action.lower() in func_body.lower() for action in pause_actions):
                        return True
                        
                    # If no explicit pause actions but function name strongly suggests pausing
                    if any(name in func_name.lower() for name in ["pause", "disabletrading", "freezetrading", "stoptrading"]):
                        return True
                        
                return False
            
            # For modifier patterns like "whenNotPaused", "whenPaused"
            elif "when" in pattern.lower():
                return True  # These are almost always related to pause functionality
                
            # For trading status variables
            elif "trading" in pattern.lower() or "tradingEnabled" in pattern.lower():
                # For each match, check if it's used in a boolean context
                for match in matches:
                    if " = true" in match.lower() or " = false" in match.lower() or "=true" in match.lower() or "=false" in match.lower():
                        return True
                        
                    # Check if it's used in conditions
                    if "require(" in match.lower() or "if(" in match.lower() or "if (" in match.lower():
                        return True
                        
                # Check if pattern is used in transfer functions
                transfer_contexts = ["transfer", "_transfer", "transferFrom"]
                for context in transfer_contexts:
                    # Find the transfer function
                    func_pattern = f"function\\s+{context}\\s*\\([^)]*\\)[^{{]*\\{{([^}}]*(?:\\{{[^}}]*\\}}[^}}]*)*?)\\}}"
                    func_match = re.search(func_pattern, contract_source, re.DOTALL | re.IGNORECASE)
                    
                    if func_match:
                        func_body = func_match.group(1)
                        
                        # Check if trading variable is used within transfer function
                        if pattern.lower() in func_body.lower():
                            return True
                
            # Default to true for other patterns to avoid false negatives
            return True
            
        except Exception as e:
            logger.warning(f"Error validating pause match: {e}")
            # In case of error, assume it might be a pause function (safer)
            return True


# Create singleton instance
ethereum_client = EthereumClient() 