#!/usr/bin/env python3
"""
Authentication helper for Quotex VIP Bot
Run this once to authenticate your Telegram account
"""

import asyncio
from telethon import TelegramClient
from config import Config

async def authenticate():
    """Authenticate the Telegram client"""
    try:
        api_id = int(Config.TELEGRAM_API_ID)
        api_hash = Config.TELEGRAM_API_HASH
        phone = Config.TELEGRAM_PHONE_NUMBER
        
        client = TelegramClient('verification_session', api_id, api_hash)
        
        print("Starting authentication...")
        await client.start(phone=phone)
        
        if await client.is_user_authorized():
            print("✅ Authentication successful!")
            me = await client.get_me()
            print(f"Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
        else:
            print("❌ Authentication failed")
            
        await client.disconnect()
        
    except Exception as e:
        print(f"Error during authentication: {e}")

if __name__ == '__main__':
    asyncio.run(authenticate())