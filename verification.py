"""
Verification service for checking Quotex referral registrations using Telethon
"""

import logging
import asyncio
import time
from typing import Optional
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError
from config import Config

logger = logging.getLogger(__name__)

class VerificationService:
    def __init__(self):
        try:
            self.api_id = int(Config.TELEGRAM_API_ID) if Config.TELEGRAM_API_ID else None
        except (ValueError, TypeError):
            self.api_id = None
        
        self.api_hash = Config.TELEGRAM_API_HASH
        self.phone_number = Config.TELEGRAM_PHONE_NUMBER
        self.session_name = 'verification_session'
        self.quotex_bot_username = '@QuotexPartnerBot'
        self.client = None
        
        if not self.api_id or not self.api_hash:
            logger.warning("Telegram API credentials missing")

    async def initialize_client(self):
        """Initialize and authenticate the Telegram client"""
        try:
            if not self.api_id or not self.api_hash:
                logger.error("Telegram API credentials not configured")
                return False
            
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start(phone=self.phone_number)
            
            if not await self.client.is_user_authorized():
                logger.error("User not authorized")
                return False
            
            logger.info("Telegram client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {e}")
            return False

    def verify_quotex_user(self, quotex_user_id: str) -> bool:
        """
        Verify if a Quotex user ID was registered through our referral link
        This communicates with @QuotexPartnerBot to check the registration
        """
        try:
            # Run the async verification
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_verify_quotex_user(quotex_user_id))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            return False

    async def _async_verify_quotex_user(self, quotex_user_id: str) -> bool:
        """Async method to verify Quotex user ID"""
        try:
            # Initialize client if not done
            if not self.client:
                if not await self.initialize_client():
                    return False
            
            # Find the QuotexPartnerBot
            try:
                quotex_bot = await self.client.get_entity(self.quotex_bot_username)
            except Exception as e:
                logger.error(f"Could not find {self.quotex_bot_username}: {e}")
                return False
            
            # Send the verification message in the required format
            verification_message = f"/{quotex_user_id}"
            logger.info(f"Sending verification request to {self.quotex_bot_username}: {verification_message}")
            
            # Send message to QuotexPartnerBot
            await self.client.send_message(quotex_bot, verification_message)
            
            # Wait for response
            await asyncio.sleep(3)
            
            # Get recent messages from the bot
            messages = await self.client.get_messages(quotex_bot, limit=5)
            
            # Check the most recent messages for verification response
            for message in messages:
                if message.text:
                    message_text = message.text.lower()
                    
                    # Check for positive verification indicators
                    if any(keyword in message_text for keyword in ['found', 'verified', 'valid', 'registered', 'success']):
                        if quotex_user_id in message_text:
                            logger.info(f"Verification successful for user ID: {quotex_user_id}")
                            return True
                    
                    # Check for negative verification indicators
                    if any(keyword in message_text for keyword in ['not found', 'invalid', 'not registered', 'error', 'fail']):
                        if quotex_user_id in message_text:
                            logger.info(f"Verification failed for user ID: {quotex_user_id}")
                            return False
            
            # If no clear response found, assume failed
            logger.warning(f"No clear verification response for user ID: {quotex_user_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error during async verification: {e}")
            return False
    
    def test_verification_connection(self) -> bool:
        """Test if Telegram client can be initialized"""
        try:
            if not self.api_id or not self.api_hash:
                logger.warning("Telegram API credentials not provided")
                return False
            
            # Test client initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._test_client_connection())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Verification connection test failed: {e}")
            return False
    
    async def _test_client_connection(self) -> bool:
        """Test client connection async"""
        try:
            if await self.initialize_client():
                if self.client:
                    await self.client.disconnect()
                return True
            return False
        except Exception as e:
            logger.error(f"Client connection test error: {e}")
            return False