#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
English language strings
"""

EN_STRINGS = {
    # Common
    'welcome': 'Welcome to the Token Security Bot!',
    'language_prompt': 'Please select your language:',
    'language_selected': 'English language selected!',
    'start_message': 'This bot helps you analyze token security on multiple blockchains.',
    'blockchain_prompt': 'Please select the blockchain network for token analysis:',
    'blockchain_selected': 'You have selected {network} network.',
    
    # Commands help
    'command_help': """Available commands:
/start - Start the bot
/help - Show help
/check - Check token security
/report - Generate PDF report
/balance - View your balance
/referral - View your referral link
/email - Send report via email
/language - Change language""",
    
    # Errors and messages
    'invalid_syntax': 'Invalid syntax. Please try again.',
    'unsupported_blockchain': 'Unsupported blockchain. Supported blockchains: {chains}',
    'feature_in_development': 'This feature is under development. Please try again later.',
    
    # Referral
    'referral_link': 'Here is your referral link. Share it if you find this bot useful:\n{link}',
    'referral_stats': 'Your referral statistics:\n- Direct referrals (F1): {direct}\n- Indirect referrals (F2): {indirect}',
    
    # Token analysis
    'enter_address': 'Please enter the token contract address:',
    'processing_address': 'Processing the address...',
    'address_required': 'Please enter a valid contract address.',
    'analyzing_token': 'Analyzing token {address} on {network}. Please wait, this may take some time...',
    'security_check_results': '🔒 SECURITY CHECK RESULTS 🔒\n\n✅ No honeypot detected\n✅ Contract is verified\n✅ No self-destruct function\n✅ No blacklist function\n✅ No mint function\n\nOverall Security Score: 95/100',
    'advanced_analysis_results': '📊 ADVANCED ANALYSIS RESULTS 📊\n\nToken Distribution:\n- Top 10 holders own 35% of supply\n- Developer wallet holds 3% of supply\n- Liquidity locked for 365 days\n\nSwap Impact (1 ETH):\n- Buy tax: 2%\n- Sell tax: 3%\n- Price impact: 0.5%\n\nRisk Assessment: LOW',
    'token_analysis_result': 'Token Analysis Results:',
    'token_name': 'Name',
    'token_symbol': 'Symbol',
    'token_total_supply': 'Total Supply',
    'token_decimals': 'Decimals',
    'token_address': 'Contract Address',
    'token_blockchain': 'Blockchain',
    'token_owner': 'Owner',
    'token_risk_level': 'Risk Level',
    'token_security_issues': 'Security Issues:',
    'token_no_security_issues': 'No security issues found!',
    'token_not_found': 'Token not found or not a valid token',
    'analysis_failed': 'Analysis failed. Please try again later.',
    
    # Reports
    'download_report': 'Download PDF Report',
    'no_analysis_available': 'No token analysis available. Please analyze a token first with /check.',
    'generating_report': 'Generating PDF report...',
    'report_generation_failed': 'Failed to generate report. Please try again later.',
    
    # Email
    'enter_email': 'Please enter your email address to receive the report:',
    'invalid_email': 'Invalid email address. Please enter a valid email.',
    'sending_email': 'Sending email. This may take a moment...',
    'email_sent': 'Report has been sent to your email!',
    'email_sending_failed': 'Failed to send email. Please try again later.',
    
    # Risk levels
    'risk_level_safe': 'LOW RISK',
    'risk_level_low': 'LOW RISK',
    'risk_level_medium': 'MEDIUM RISK',
    'risk_level_high': 'HIGH RISK',
    'risk_level_critical': 'EXTREMELY RISKY',
    
    # Payment
    'payment_required': 'This feature requires payment to use.',
    'payment_instructions': 'Please send {amount} USDT to the following address:',
    'payment_waiting': 'Waiting for payment confirmation...',
    'payment_confirmed': 'Payment confirmed! You can now use the feature.',
    'payment_failed': 'Payment verification failed. Please try again or contact support.',
    'insufficient_balance': 'Your balance is insufficient. Current balance: {balance} USDT',
    
    # Balance
    'balance_info': 'Your current balance: {balance} USDT\nReferral earnings: {referral} USDT',
    
    # Admin panel
    'admin_panel': 'Admin Panel - Select an option:',
    'admin_prices': 'Price Settings',
    'admin_users': 'User Management',
    'admin_stats': 'Statistics',
    'admin_access_denied': 'Access denied. You are not authorized to use admin commands.',
    
    # Command list
    'command_list': "List of commands:\n" \
                  "/start - Start the bot\n" \
                  "/help - Show help\n" \
                  "/check - Check token security\n" \
                  "/report - Generate PDF report\n" \
                  "/balance - Check your balance\n" \
                  "/referral - View your referral link\n" \
                  "/email - Send report via email\n" \
                  "/language - Change language",
    'command_list_intro': "Here are the commands to use the Bot:",
    
    # Security analysis header
    'security_analysis_header': 'SMART CONTRACT ANALYSIS',
    'token_info_header': 'TOKEN INFORMATION',
    'dangerous_functions': 'DANGEROUS FUNCTIONS',
    'risk_assessment': 'ASSESSMENT',
    
    # Token info
    'total_supply': 'Total Supply',
    'holder_count': 'Total Holders',
    'dex_liquidity': 'Liquidity Pool (DEX)',
    'transaction_tax': 'Transaction Tax',
    'tax_info': 'Buy {buy} / Sell {sell}',
    'contract_owner': 'Contract Owner',
    
    # Dangerous functions
    'has_mint_warning': 'Can mint unlimited tokens',
    'has_blacklist_warning': 'Contract has blacklist function for user wallets',
    'has_pause_warning': 'Contract owner can pause trading (can buy but cannot sell)',
    'has_revoke_warning': 'Contract owner can modify balances from user wallets',
    'has_self_destruct_warning': 'Contract contains self-destruct function',
    'honeypot_warning': 'Potentially a honeypot',
    'no_dangerous_functions': 'No dangerous functions detected in this contract',
    'contract_not_verified_warning': 'Contract is not verified on Etherscan',
    
    # Risk assessment
    'critical_risk': 'EXTREMELY RISKY',
    'critical_risk_description': 'EXTREMELY RISKY: This contract contains very dangerous vulnerabilities, the risk of fraud when investing is very high, please consider carefully',
    'high_risk': 'HIGH RISK',
    'high_risk_description': 'HIGH RISK: The contract integrates functions that can potentially harm investors, research the project carefully before making an investment decision',
    'low_risk_description': 'No dangerous functions detected in this contract, carefully research other factors before making an investment decision',
    
    # Check result
    'check_failed': 'Token check failed. Please try again later.',
    
    # Status
    'not_verified': 'Not verified',
    
    # Disclaimer
    'analysis_disclaimer': 'Note: Bot analyzes risk based on contract source code directly on the Blockchain, information is for reference only. Users are responsible for their own research and investment decisions!',
} 