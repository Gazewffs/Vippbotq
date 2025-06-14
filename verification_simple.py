"""
Real verification service using Telethon to interact with QuotexPartnerBot
"""

import logging
import asyncio
import threading
import time
import subprocess
import sys
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

class VerificationService:
    def __init__(self):
        self.quotex_bot_username = '@QuotexPartnerBot'
        self.session_file = 'verification_session'
        logger.info("Verification service initialized (isolated mode)")

    def verify_quotex_user(self, quotex_user_id: str) -> bool:
        """
        Verify if a Quotex user ID was registered through our referral link
        Uses subprocess to completely isolate the verification process
        """
        try:
            logger.info(f"Verifying user ID: {quotex_user_id}")

            # Create a separate Python script to run verification
            script_content = f'''
import asyncio
import sys
from telethon import TelegramClient
from telethon.errors import FloodWaitError

async def verify_user():
    api_id = {Config.TELEGRAM_API_ID or "None"}
    api_hash = "{Config.TELEGRAM_API_HASH or ""}"

    if not api_id or not api_hash:
        print("ERROR: API credentials not configured")
        return False

    client = TelegramClient('verification_session', api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("ERROR: Not authorized")
            return False

        # Get QuotexPartnerBot
        quotex_bot = await client.get_entity('@QuotexPartnerBot')

        # Send verification message
        await client.send_message(quotex_bot, "/{quotex_user_id}")

        # Wait for response
        await asyncio.sleep(3)

        # Get recent messages
        messages = await client.get_messages(quotex_bot, limit=5)

        for msg in messages:
            if msg.text and "{quotex_user_id}" in msg.text:
                response_text = msg.text.lower()

                # Check result - be more specific about the failure cases
                failure_indicators = ['was not found', 'not found', 'invalid', 'not registered', 'error', 'failed', 'not valid']
                success_indicators = ['registered', 'verified', 'valid', 'success', 'confirmed', 'deposits sum:', 'deposit sum:']

                # First check for failure indicators (more specific)
                if any(indicator in response_text for indicator in failure_indicators):
                    print("FAILED")
                    return False

                # Check for deposits sum which indicates successful registration
                if 'deposits sum:' in response_text or 'deposit sum:' in response_text:
                    print("SUCCESS")
                    return True

                # Then check for other success indicators
                if any(indicator in response_text for indicator in success_indicators):
                    print("SUCCESS")
                    return True

        print("NO_RESPONSE")
        return False

    except Exception as e:
        print(f"ERROR: {{e}}")
        return False
    finally:
        if client.is_connected():
            await client.disconnect()

if __name__ == "__main__":
    result = asyncio.run(verify_user())
    sys.exit(0 if result else 1)
'''

            # Write script to temporary file
            with open('temp_verify.py', 'w') as f:
                f.write(script_content)

            # Run verification in subprocess
            result = subprocess.run([sys.executable, 'temp_verify.py'], 
                                  capture_output=True, text=True, timeout=30)

            # Clean up temp file
            try:
                import os
                os.remove('temp_verify.py')
            except:
                pass

            # Check result
            if result.returncode == 0:
                output = result.stdout.strip()
                if "SUCCESS" in output:
                    logger.info(f"Verification successful for user ID: {quotex_user_id}")
                    return True
                elif "FAILED" in output:
                    logger.info(f"Verification failed for user ID: {quotex_user_id}")
                    return False
                else:
                    logger.warning(f"No clear verification response for user ID: {quotex_user_id}")
                    return False
            else:
                error_output = result.stderr.strip()
                logger.error(f"Verification subprocess failed: {error_output}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Verification timeout")
            return False
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            return False

    def test_connection(self) -> bool:
        """Test connection to verification service"""
        try:
            logger.info("Testing verification connection (isolated mode)")

            # Simple test script
            script_content = f'''
import asyncio
import sys
from telethon import TelegramClient

async def test_connection():
    api_id = {Config.TELEGRAM_API_ID or "None"}
    api_hash = "{Config.TELEGRAM_API_HASH or ""}"

    if not api_id or not api_hash:
        print("ERROR: API credentials not configured")
        return False

    client = TelegramClient('verification_session', api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("ERROR: Not authorized")
            return False

        # Try to get QuotexPartnerBot
        quotex_bot = await client.get_entity('@QuotexPartnerBot')
        print("SUCCESS: Connected to QuotexPartnerBot")
        return True

    except Exception as e:
        print(f"ERROR: {{e}}")
        return False
    finally:
        if client.is_connected():
            await client.disconnect()

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
'''

            # Write script to temporary file
            with open('temp_test.py', 'w') as f:
                f.write(script_content)

            # Run test in subprocess
            result = subprocess.run([sys.executable, 'temp_test.py'], 
                                  capture_output=True, text=True, timeout=15)

            # Clean up temp file
            try:
                import os
                os.remove('temp_test.py')
            except:
                pass

            # Check result
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                logger.info("Connection test successful")
                return True
            else:
                logger.error(f"Connection test failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Connection test timeout")
            return False
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return False