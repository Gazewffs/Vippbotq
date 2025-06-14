
#!/usr/bin/env python3
"""
One-time setup script to authenticate Telegram account
"""

import asyncio
import sys
from telethon import TelegramClient
from config import Config

async def setup_authentication():
    """Setup Telegram authentication interactively"""
    try:
        api_id = Config.TELEGRAM_API_ID
        api_hash = Config.TELEGRAM_API_HASH
        phone = Config.TELEGRAM_PHONE_NUMBER
        
        if not api_id or not api_hash or not phone:
            print("❌ Missing required configuration:")
            print("Please set the following environment variables:")
            print("- TELEGRAM_API_ID")
            print("- TELEGRAM_API_HASH") 
            print("- TELEGRAM_PHONE_NUMBER")
            return False
            
        try:
            api_id = int(api_id)
        except ValueError:
            print("❌ TELEGRAM_API_ID must be a valid integer")
            return False
        
        print(f"Setting up authentication for: {phone}")
        
        client = TelegramClient('verification_session', api_id, api_hash)
        await client.connect()
        
        if not await client.is_user_authorized():
            print("Sending verification code...")
            await client.send_code_request(phone)
            
            print("Please check your Telegram app or SMS for the verification code.")
            code = input("Enter the verification code: ")
            
            try:
                await client.sign_in(phone, code)
                print("✅ Authentication successful!")
            except Exception as e:
                if "password" in str(e).lower():
                    password = input("Two-factor authentication enabled. Enter your password: ")
                    await client.sign_in(password=password)
                    print("✅ Authentication successful!")
                else:
                    print(f"❌ Authentication failed: {e}")
                    return False
        else:
            print("✅ Already authenticated!")
        
        # Test the connection
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
        
        # Test QuotexPartnerBot connection
        try:
            quotex_bot = await client.get_entity('@QuotexPartnerBot')
            print(f"✅ Successfully found @QuotexPartnerBot: {quotex_bot.first_name}")
        except Exception as e:
            print(f"⚠️  Warning: Could not find @QuotexPartnerBot: {e}")
            print("This might affect verification functionality.")
        
        await client.disconnect()
        print("✅ Authentication setup complete! You can now start the bot.")
        return True
        
    except Exception as e:
        print(f"❌ Error during authentication setup: {e}")
        return False

if __name__ == '__main__':
    success = asyncio.run(setup_authentication())
    if not success:
        sys.exit(1)
