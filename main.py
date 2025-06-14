#!/usr/bin/env python3
"""
Main entry point for the Quotex VIP Channel Bot
"""

import logging
import os
from bot import QuotexVIPBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the bot"""
    try:
        # Initialize and start the bot
        bot = QuotexVIPBot()
        logger.info("Starting Quotex VIP Channel Bot...")
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    main()
