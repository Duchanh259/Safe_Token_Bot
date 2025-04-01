#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Multilingual module for the bot.
Supports English and Vietnamese.
"""
from typing import Dict, Any, Optional

from config.config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from app.i18n.en.strings import EN_STRINGS
from app.i18n.vi.strings import VI_STRINGS

# Dictionary to store language strings
LANGUAGE_STRINGS = {
    'en': EN_STRINGS,
    'vi': VI_STRINGS
}


class TextProvider:
    """Multilingual text provider class."""
    
    def __init__(self):
        """Initialize TextProvider."""
        self.default_language = DEFAULT_LANGUAGE
    
    def get_text(self, key: str, language: str = None, **kwargs) -> str:
        """
        Get text string by language.
        
        Args:
            key: String key to get
            language: Language code (en, vi)
            **kwargs: Parameters to substitute in the string
            
        Returns:
            Localized text string
        """
        lang = language or self.default_language
        
        # If language is not supported, use default language
        if lang not in SUPPORTED_LANGUAGES:
            lang = self.default_language
        
        # Get string from dictionary
        if key in LANGUAGE_STRINGS[lang]:
            text = LANGUAGE_STRINGS[lang][key]
        elif key in LANGUAGE_STRINGS[self.default_language]:
            # Fallback to default language if key not found
            text = LANGUAGE_STRINGS[self.default_language][key]
        else:
            # Return key if string not found
            return f"[{key}]"
        
        # Substitute parameters if any
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                # Ignore errors if parameters are missing
                pass
        
        return text


# Create singleton instance
translator = TextProvider() 