#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Referral system module.
Manages user referrals and commissions.
"""

import random
import string
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ReferralSystem:
    """Manages user referrals and commissions."""
    
    def __init__(self):
        """Initialize referral system."""
        self.referrals = {}  # Dictionary to store referrals
        logger.info("Referral system initialized")
    
    def generate_referral_code(self, user_id):
        """
        Generate a unique referral code for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Referral code
        """
        # Generate a random string
        letters = string.ascii_letters + string.digits
        random_part = ''.join(random.choice(letters) for i in range(8))
        
        # Create a referral code
        referral_code = f"ref_{user_id}_{random_part}"
        
        return referral_code
    
    def generate_referral_link(self, user_id, bot_username):
        """
        Generate a referral link for a user.
        
        Args:
            user_id: User ID
            bot_username: Bot username
            
        Returns:
            Referral link
        """
        referral_code = self.generate_referral_code(user_id)
        
        # Save the referral code
        if user_id not in self.referrals:
            self.referrals[user_id] = {
                'code': referral_code,
                'refers': [],
                'earnings': 0.0
            }
        
        # Create a referral link
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"
        
        return referral_link
    
    def register_referral(self, user_id, referral_code):
        """
        Register a referral.
        
        Args:
            user_id: User ID
            referral_code: Referral code
            
        Returns:
            True if referral was registered, False otherwise
        """
        # Parse referral code
        try:
            parts = referral_code.split('_')
            if len(parts) < 2:
                logger.warning(f"Invalid referral code format: {referral_code}")
                return False
            
            referrer_id = int(parts[1])
            
            # Check if referrer exists
            if referrer_id not in self.referrals:
                logger.warning(f"Referrer {referrer_id} not found")
                return False
            
            # Check if user is not referring themselves
            if user_id == referrer_id:
                logger.warning(f"User {user_id} tried to refer themselves")
                return False
            
            # Add referral
            self.referrals[referrer_id]['refers'].append(user_id)
            logger.info(f"User {user_id} was referred by {referrer_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error registering referral: {str(e)}")
            return False
    
    def get_referral_stats(self, user_id):
        """
        Get referral statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (direct_referrals, indirect_referrals)
        """
        if user_id not in self.referrals:
            return 0, 0
        
        direct_referrals = len(self.referrals[user_id]['refers'])
        indirect_referrals = 0
        
        # TODO: Implement indirect referrals calculation
        
        return direct_referrals, indirect_referrals
    
    def calculate_commission(self, user_id, amount):
        """
        Calculate commission for referrals.
        
        Args:
            user_id: User ID
            amount: Transaction amount
            
        Returns:
            None
        """
        # TODO: Implement commission calculation
        pass


# Create singleton instance
referral_system = ReferralSystem() 