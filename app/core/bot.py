#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Core module for the Telegram bot.
Manages bot initialization, commands, and callbacks.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from config.config import (
    TELEGRAM_BOT_TOKEN, 
    ADMIN_USER_IDS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_BLOCKCHAINS,
)
from app.i18n.text_provider import translator
from app.utils.logger import get_logger
from app.security.checker_manager import checker_manager
from app.reporting.report_generator import report_generator
from app.referral.referral_system import referral_system

# Conversation states
LANGUAGE_SELECTION = 0
BLOCKCHAIN_SELECTION = 1
TOKEN_ADDRESS = 2
EMAIL_INPUT = 3
PAYMENT_CONFIRMATION = 4
ADMIN_COMMAND = 5

logger = get_logger(__name__)


class TelegramBot:
    """Telegram bot core class."""
    
    def __init__(self):
        """Initialize the Telegram bot."""
        self.token = TELEGRAM_BOT_TOKEN
        if not self.token:
            logger.error("Bot token not set in environment variables!")
            raise ValueError("Bot token not set. Please check your .env file.")
            
        # Parse admin IDs
        try:
            self.admin_ids = [int(uid) for uid in ADMIN_USER_IDS]
        except Exception as e:
            logger.warning(f"Failed to parse admin IDs: {e}")
            self.admin_ids = []
        
        # Initialize bot application
        self.application = Application.builder().token(self.token).build()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Telegram bot initialized")
    
    def _register_handlers(self):
        """Register command and message handlers."""
        # Basic commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("language", self.language_command))
        
        # Token analysis commands
        self.application.add_handler(CommandHandler("check", self.check_command))
        
        # Payment and referral commands
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("referral", self.referral_command))
        
        # Report and email commands
        self.application.add_handler(CommandHandler("report", self.report_command))
        self.application.add_handler(CommandHandler("email", self.email_command))
        
        # Admin commands (admin only)
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        
        # Handle callback queries
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Handle regular messages
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.handle_message
        ))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /start command:
        - Welcome the user
        - Ask for language selection
        - Process referral code if any
        """
        # Get user ID
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        logger.info(f"User {user_id} ({username}) started the bot")
        
        # Check for referral code
        if context.args and len(context.args) > 0 and context.args[0].startswith("ref_"):
            referral_code = context.args[0]
            logger.info(f"User {user_id} used referral code: {referral_code}")
            # Register referral
            referral_success = referral_system.register_referral(user_id, referral_code)
            if referral_success:
                logger.info(f"User {user_id} registered with referral code {referral_code}")
        
        # Store user data
        if not context.user_data.get('user_id'):
            context.user_data['user_id'] = user_id
            context.user_data['username'] = username
        
        # Show language selection menu
        keyboard = []
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            keyboard.append([
                InlineKeyboardButton(
                    text=lang_name, 
                    callback_data=f"lang_{lang_code}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌐 Choose Language / Chọn Ngôn Ngữ:",
            reply_markup=reply_markup
        )
        
        return LANGUAGE_SELECTION
    
    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /language command to change language."""
        # Show language selection menu in horizontal layout
        keyboard = []
        row = []
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            button = InlineKeyboardButton(
                text=lang_name, 
                callback_data=f"lang_{lang_code}"
            )
            row.append(button)
        keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌐 Choose Language / Chọn Ngôn Ngữ:",
            reply_markup=reply_markup
        )
        
        return LANGUAGE_SELECTION
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command."""
        language = context.user_data.get('language', 'en')
        help_text = translator.get_text('command_help', language)
        
        await update.message.reply_text(help_text)
    
    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /check command for token security check."""
        language = context.user_data.get('language', 'en')
        
        # Set analysis type to 'complete'
        context.user_data['analysis_type'] = 'complete'
        
        # Show blockchain options directly
        await self.show_blockchain_options(update, context)
        
        return BLOCKCHAIN_SELECTION
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /analyze command for advanced token analysis."""
        language = context.user_data.get('language', 'en')
        context.user_data['analysis_type'] = 'advanced'
        
        # Show blockchain options
        await self.show_blockchain_options(update, context)
        
        return BLOCKCHAIN_SELECTION
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /balance command to check user balance."""
        language = context.user_data.get('language', 'en')
        user_id = update.effective_user.id
        
        # TODO: Implement get balance from database
        balance = 0.0
        referral_earnings = 0.0
        
        await update.message.reply_text(
            translator.get_text('balance_info', language, balance=balance, referral=referral_earnings)
        )
    
    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /referral command to view referral information."""
        language = context.user_data.get('language', 'en')
        user_id = update.effective_user.id
        
        # Generate referral link
        bot_username = (await self.application.bot.get_me()).username
        referral_link = referral_system.generate_referral_link(user_id, bot_username)
        
        # Get referral statistics
        direct_referrals, indirect_referrals = referral_system.get_referral_stats(user_id)
        
        # Send referral information
        await update.message.reply_text(
            translator.get_text('referral_link', language, link=referral_link)
        )
        
        await update.message.reply_text(
            translator.get_text('referral_stats', language, direct=direct_referrals, indirect=indirect_referrals)
        )
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /report command to generate PDF report."""
        language = context.user_data.get('language', 'en')
        
        # Check if token was analyzed before
        if not context.user_data.get('last_analyzed_token'):
            await update.message.reply_text(
                translator.get_text('no_analysis_available', language)
            )
            return
        
        # TODO: Implement PDF report generation
        await update.message.reply_text(
            translator.get_text('generating_report', language)
        )
    
    async def email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /email command to send report via email."""
        language = context.user_data.get('language', 'en')
        
        # Check if token was analyzed before
        if not context.user_data.get('last_analyzed_token'):
            await update.message.reply_text(
                translator.get_text('no_analysis_available', language)
            )
            return
        
        # Ask for email address
        await update.message.reply_text(
            translator.get_text('enter_email', language)
        )
        
        context.user_data['waiting_for'] = 'email_address'
        return EMAIL_INPUT
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /admin command."""
        user_id = update.effective_user.id
        language = context.user_data.get('language', 'en')
        
        # Check if user is admin
        if user_id not in self.admin_ids:
            await update.message.reply_text("Access denied. You are not an admin.")
            return
        
        # Show admin menu
        keyboard = [
            [InlineKeyboardButton("💲 Price Settings", callback_data="admin_prices")],
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            translator.get_text('admin_panel', language),
            reply_markup=reply_markup
        )
        
        return ADMIN_COMMAND
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        # Get callback data
        callback_data = query.data
        
        # Process based on callback data
        if callback_data.startswith('lang_'):
            await self.handle_language_selection(update, context, callback_data)
        
        # Handle blockchain selection
        elif callback_data.startswith('chain_'):
            await self.handle_blockchain_selection(update, context, callback_data)
        
        # Handle analysis type selection
        elif callback_data.startswith('analysis_'):
            await self.handle_analysis_selection(update, context, callback_data)
        
        # Handle admin actions
        elif callback_data.startswith('admin_'):
            await self.handle_admin_callback(update, context, callback_data)
    
    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle language selection."""
        query = update.callback_query
        language_code = callback_data.split('_')[1]
        context.user_data['language'] = language_code
        
        # Send confirmation message
        language_name = SUPPORTED_LANGUAGES[language_code]
        await query.edit_message_text(
            text=translator.get_text('language_selected', language_code, lang_name=language_name)
        )
        
        # Send welcome message
        welcome_message = translator.get_text('welcome', language_code)
        await query.message.reply_text(welcome_message)
        
        # Show user balance
        user_id = context.user_data['user_id']
        # TODO: Implement get balance from database
        balance = 0.0
        referral_earnings = 0.0
        await query.message.reply_text(
            translator.get_text('balance_info', language_code, balance=balance, referral=referral_earnings)
        )

        # Send command list introduction
        command_intro = translator.get_text('command_list_intro', language_code)
        
        # Get the actual command list (without the old intro/header if any)
        command_list_full = translator.get_text('command_list', language_code)
        actual_commands = command_list_full # Default
        try:
            # If the full string contained a newline, assume the part after is the list
            if '\\\\n' in command_list_full:
                actual_commands = command_list_full.split('\\\\n', 1)[1]
            # Otherwise, actual_commands remains the full string (might just be the list)
        except Exception as e:
            logger.warning(f"Error splitting command list string: {e}. Using full string: {command_list_full}")
            actual_commands = command_list_full # Fallback

        # Combine the new intro and the actual commands
        if actual_commands: # Ensure commands exist before combining
            final_message = f"{command_intro}\\\\n{actual_commands}"
        else:
            final_message = command_intro # Only show intro if commands are empty/missing
            
        await query.message.reply_text(final_message)
        
        return ConversationHandler.END # End conversation after language selection
    
    async def handle_blockchain_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle blockchain selection."""
        query = update.callback_query
        blockchain = callback_data.split('_')[1]
        context.user_data['selected_blockchain'] = blockchain
        
        language = context.user_data.get('language', 'en')
        
        # Send confirmation message
        blockchain_name = SUPPORTED_BLOCKCHAINS[blockchain]['name']
        await query.edit_message_text(
            text=translator.get_text('blockchain_selected', language, network=blockchain_name)
        )
        
        # Ask for token address
        await query.message.reply_text(
            translator.get_text('enter_address', language)
        )
        
        context.user_data['waiting_for'] = 'token_address'
        
        return TOKEN_ADDRESS
    
    async def handle_analysis_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle analysis type selection."""
        query = update.callback_query
        analysis_type = callback_data.split('_')[1]
        context.user_data['analysis_type'] = analysis_type
        
        language = context.user_data.get('language', 'en')
        
        # Send confirmation message
        await query.edit_message_text(
            text=translator.get_text('analysis_type_selected', language, analysis_type=analysis_type)
        )
        
        # Show blockchain options
        await self.show_blockchain_options(update, context)
        
        return BLOCKCHAIN_SELECTION
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle admin callback."""
        query = update.callback_query
        
        admin_action = callback_data.split('_')[1]
        
        language = context.user_data.get('language', 'en')
        
        # TODO: Implement admin actions handling
        await query.edit_message_text(
            text=translator.get_text('feature_in_development', language)
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages."""
        # Get current language
        language = context.user_data.get('language', 'en')
        text = update.message.text
        
        # Check what we're waiting for
        waiting_for = context.user_data.get('waiting_for')
        
        if waiting_for == 'token_address':
            # Waiting for token address
            address = text.strip()
            
            # Check if address is valid (basic)
            if not address.startswith('0x') or len(address) != 42:
                await update.message.reply_text(
                    translator.get_text('address_required', language)
                )
                return
            
            # Send processing message
            await update.message.reply_text(
                translator.get_text('processing_address', language)
            )
            
            # Get selected blockchain
            blockchain = context.user_data.get('selected_blockchain')
            analysis_type = context.user_data.get('analysis_type', 'basic')
            
            # Reset waiting state
            context.user_data['waiting_for'] = None
            
            # Analyze token
            await update.message.reply_text(
                translator.get_text('analyzing_token', language, address=address, network=SUPPORTED_BLOCKCHAINS[blockchain]['name'])
            )
            
            try:
                # Actually run the token security check
                token_check_result = await checker_manager.check_token(address, blockchain)
                
                if token_check_result.get("status") == "error":
                    # Handle error
                    await update.message.reply_text(
                        translator.get_text('analysis_failed', language) + f": {token_check_result.get('error', 'Unknown error')}"
                    )
                    return
                
                # Format and display combined analysis results
                analysis_message = self._format_security_results(token_check_result, language)
                await update.message.reply_text(analysis_message, parse_mode="HTML", disable_web_page_preview=True)
                
                # Store analysis results
                context.user_data['last_analyzed_token'] = {
                    'address': address,
                    'blockchain': blockchain,
                    'analysis_type': analysis_type,
                    'result': token_check_result,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error analyzing token: {str(e)}", exc_info=True)
                await update.message.reply_text(
                    translator.get_text('analysis_failed', language) + f": {str(e)}"
                )
            
            # Show referral link after analysis
            user_id = update.effective_user.id
            bot_username = (await self.application.bot.get_me()).username
            referral_link = referral_system.generate_referral_link(user_id, bot_username)
            referral_link_text = translator.get_text('referral_link', language, link=referral_link)
            await update.message.reply_text(referral_link_text)
            
        elif waiting_for == 'email_address':
            # Waiting for email address
            email = text.strip()
            
            # Check if email is valid (basic)
            if '@' not in email or '.' not in email:
                await update.message.reply_text(
                    translator.get_text('invalid_email', language)
                )
                return
            
            # Send processing message
            await update.message.reply_text(
                translator.get_text('sending_email', language)
            )
            
            context.user_data['waiting_for'] = None
            
            # TODO: Implement send email
            # Send sample results
            await update.message.reply_text(
                translator.get_text('feature_in_development', language)
            )
            
        else:
            # Not waiting for anything, show help
            await update.message.reply_text(
                translator.get_text('command_help', language)
            )
    
    async def show_blockchain_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show blockchain selection options."""
        language = context.user_data.get('language', 'en')
        
        # Create keyboard with supported blockchains in 2 columns layout
        keyboard = []
        current_row = []
        
        for chain_id, chain_info in SUPPORTED_BLOCKCHAINS.items():
            button = InlineKeyboardButton(
                f"{chain_info['icon']} {chain_info['name']} ({chain_info['symbol']})",
                callback_data=f"chain_{chain_id}"
            )
            current_row.append(button)
            
            # Add row to keyboard when it has 2 buttons
            if len(current_row) == 2:
                keyboard.append(current_row)
                current_row = []
        
        # Add remaining buttons if any
        if current_row:
            keyboard.append(current_row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            translator.get_text('blockchain_prompt', language),
            reply_markup=reply_markup
        )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Error: {context.error}", exc_info=context.error)
    
    def run(self):
        """Run the bot."""
        logger.info("Starting the bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    def _format_security_results(self, token_check_result: Dict[str, Any], language: str) -> str:
        """Format security check results for display."""
        if token_check_result.get("status") != "success":
            return translator.get_text('check_failed', language)
        
        token_info = token_check_result.get("token", {})
        security = token_check_result.get("security", {})
        
        # Format header
        result_message = f"🔍 {translator.get_text('security_analysis_header', language)}\n\n"
        
        # Basic token information
        result_message += f"* {translator.get_text('token_info_header', language)}:\n"
        result_message += f"- {translator.get_text('token_name', language)}: {token_info.get('name', 'N/A')}\n"
        result_message += f"- {translator.get_text('token_symbol', language)}: {token_info.get('symbol', 'N/A')}\n"
        
        # Format owner address
        owner = token_info.get('owner', 'N/A')
        owner_link = token_info.get('owner_link', '')
        if owner != 'N/A' and owner_link:
            owner_display = f"<a href='{owner_link}'>{owner}</a>"
        else:
            owner_display = owner
        result_message += f"- {translator.get_text('contract_owner', language)}: {owner_display}\n"
        
        # Format total supply
        total_supply = token_info.get('total_supply', 'N/A')
        if total_supply != 'N/A':
            total_supply = f"{total_supply:,.3f}"
        result_message += f"- {translator.get_text('total_supply', language)}: {total_supply}\n"
        
        # Holders count
        result_message += f"- {translator.get_text('holder_count', language)}: N/A\n"
        
        # DEX liquidity
        result_message += f"- {translator.get_text('dex_liquidity', language)}: {translator.get_text('not_verified', language)}\n"
        
        # Transaction tax
        result_message += f"- {translator.get_text('transaction_tax', language)}: {translator.get_text('tax_info', language, buy='0%', sell='0%')}\n\n"
        
        # Security issues
        result_message += f"* {translator.get_text('dangerous_functions', language)}:\n"
        
        # Check for dangerous functions
        has_dangerous_functions = False
        
        # First check if contract is verified
        if not security.get('is_verified', True):
            has_dangerous_functions = True
            result_message += f"⚠️ {translator.get_text('contract_not_verified_warning', language)}\n"
        
        if security.get('has_mint', False):
            has_dangerous_functions = True
            result_message += f"⚠️ {translator.get_text('has_mint_warning', language)}\n"
            
        if security.get('has_blacklist', False):
            has_dangerous_functions = True
            result_message += f"⚠️ {translator.get_text('has_blacklist_warning', language)}\n"
            
        if security.get('has_pause', False):
            has_dangerous_functions = True
            result_message += f"⚠️ {translator.get_text('has_pause_warning', language)}\n"
            
        if security.get('has_revoke', False):
            has_dangerous_functions = True
            result_message += f"⚠️ {translator.get_text('has_revoke_warning', language)}\n"
            
        if security.get('is_honeypot', False):
            has_dangerous_functions = True
            result_message += f"⚠️ {translator.get_text('honeypot_warning', language)}\n"
            
        if security.get('has_self_destruct', False):
            has_dangerous_functions = True
            result_message += f"⚠️ {translator.get_text('has_self_destruct_warning', language)}\n"
        
        if not has_dangerous_functions and security.get('is_verified', True):
            result_message += f"✅ {translator.get_text('no_dangerous_functions', language)}\n"
        
        # Determine risk level
        # High number of dangerous functions = critical risk
        risk_level = "low"
        dangerous_count = sum([
            1 if not security.get('is_verified', True) else 0,
            1 if security.get('has_mint', False) else 0,
            1 if security.get('has_blacklist', False) else 0,
            1 if security.get('has_pause', False) else 0,
            1 if security.get('has_revoke', False) else 0,
            1 if security.get('is_honeypot', False) else 0,
            1 if security.get('has_self_destruct', False) else 0
        ])
        
        if security.get('is_honeypot', False) or not security.get('is_verified', True):
            risk_level = "critical"  # Honeypot or unverified contracts are critical risk
        elif dangerous_count >= 3:
            risk_level = "critical"  # 3+ dangerous functions = critical risk
        elif dangerous_count >= 1:
            risk_level = "high"      # 1-2 dangerous functions = high risk
        
        # Risk assessment
        if risk_level == "critical":
            result_message += f"\n* {translator.get_text('risk_assessment', language)}: {translator.get_text('critical_risk', language)}\n"
            result_message += f"{translator.get_text('critical_risk_description', language)}\n\n"
        elif risk_level == "high":
            result_message += f"\n* {translator.get_text('risk_assessment', language)}: {translator.get_text('high_risk', language)}\n"
            result_message += f"{translator.get_text('high_risk_description', language)}\n\n"
        else:
            result_message += f"\n* {translator.get_text('risk_assessment', language)}: {translator.get_text('risk_level_low', language)}\n"
            result_message += f"{translator.get_text('low_risk_description', language)}\n\n"
        
        # Disclaimer
        result_message += f"{translator.get_text('analysis_disclaimer', language)}"
        
        return result_message
    
    def _format_advanced_results(self, token_check_result: Dict[str, Any], language: str) -> str:
        """
        Format advanced analysis results for display.
        
        Args:
            token_check_result: Token check result dictionary
            language: User language
            
        Returns:
            Formatted message string
        """
        # No longer needed as we combined both basic and advanced analysis into a single message
        return ""