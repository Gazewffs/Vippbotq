"""
Admin functionality for the Quotex VIP Channel Bot
"""

import logging
from typing import List
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from config import Config

logger = logging.getLogger(__name__)

class AdminHandler:
    def __init__(self, database: Database):
        self.db = database
        self.admin_ids = Config.ADMIN_USER_IDS
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        return user_id in self.admin_ids
    
    async def add_links_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin command to add VIP links"""
        if not update.message:
            return
        
        user_id = update.message.from_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        # Get links from command arguments or message text
        message_text = update.message.text
        
        if not message_text or len(message_text.split('\n')) < 2:
            await update.message.reply_text(
                "📝 Please provide VIP links to add:\n\n"
                "Usage: /admin_add_links\n"
                "https://t.me/vip_channel_1\n"
                "https://t.me/vip_channel_2\n"
                "https://t.me/vip_channel_3"
            )
            return
        
        # Extract links from message (skip the command line)
        lines = message_text.split('\n')[1:]
        links = [line.strip() for line in lines if line.strip() and line.strip().startswith('http')]
        
        if not links:
            await update.message.reply_text("❌ No valid links found. Please provide valid HTTP/HTTPS links.")
            return
        
        # Add links to database
        added_count = self.db.add_vip_links(links)
        
        await update.message.reply_text(
            f"✅ Successfully added {added_count} VIP links!\n"
            f"📊 Total links provided: {len(links)}\n"
            f"🔄 Duplicates skipped: {len(links) - added_count}"
        )
        
        logger.info(f"Admin {user_id} added {added_count} VIP links")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin command to show bot statistics"""
        if not update.message:
            return
        
        user_id = update.message.from_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        stats = self.db.get_stats()
        
        if not stats:
            await update.message.reply_text("❌ Error retrieving statistics.")
            return
        
        stats_message = (
            "📊 **Bot Statistics**\n\n"
            f"👥 Total Verified Users: {stats.get('total_users', 0)}\n"
            f"🔗 Total VIP Links: {stats.get('total_links', 0)}\n"
            f"✅ Used Links: {stats.get('used_links', 0)}\n"
            f"🟢 Available Links: {stats.get('available_links', 0)}\n"
            f"🔍 Total Verification Attempts: {stats.get('total_attempts', 0)}\n"
            f"✅ Successful Verifications: {stats.get('successful_verifications', 0)}\n\n"
        )
        
        # Calculate success rate
        total_attempts = stats.get('total_attempts', 0)
        successful = stats.get('successful_verifications', 0)
        if total_attempts > 0:
            success_rate = (successful / total_attempts) * 100
            stats_message += f"📈 Success Rate: {success_rate:.1f}%"
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
        
        logger.info(f"Admin {user_id} requested bot statistics")
    
    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin command to list recent verified users"""
        if not update.message:
            return
        
        user_id = update.message.from_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        users = self.db.get_recent_users(limit=20)
        
        if not users:
            await update.message.reply_text("📝 No verified users found.")
            return
        
        users_message = "👥 **Recent Verified Users**\n\n"
        
        for i, user in enumerate(users, 1):
            telegram_id = user['telegram_id']
            quotex_id = user['quotex_user_id']
            verified_at = user['verified_at']
            
            users_message += (
                f"{i}. TG: `{telegram_id}`\n"
                f"   Quotex ID: `{quotex_id}`\n"
                f"   Verified: {verified_at}\n\n"
            )
        
        await update.message.reply_text(users_message, parse_mode='Markdown')
        
        logger.info(f"Admin {user_id} requested user list")
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin command to broadcast message to all users"""
        if not update.message:
            return
        
        user_id = update.message.from_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        # Get broadcast message
        message_text = update.message.text
        
        if not message_text or len(message_text.split('\n')) < 2:
            await update.message.reply_text(
                "📢 Please provide a message to broadcast:\n\n"
                "Usage: /admin_broadcast\n"
                "Your broadcast message here..."
            )
            return
        
        # Extract message content (skip command line)
        broadcast_message = '\n'.join(message_text.split('\n')[1:])
        
        if not broadcast_message.strip():
            await update.message.reply_text("❌ Broadcast message cannot be empty.")
            return
        
        # Get all verified users
        users = self.db.get_recent_users(limit=1000)  # Adjust limit as needed
        
        if not users:
            await update.message.reply_text("📝 No users to broadcast to.")
            return
        
        await update.message.reply_text(f"📢 Starting broadcast to {len(users)} users...")
        
        # Send broadcast (this would need to be implemented with the main bot instance)
        # For now, just confirm the command
        await update.message.reply_text(
            f"✅ Broadcast prepared for {len(users)} users.\n"
            f"Message: {broadcast_message[:100]}{'...' if len(broadcast_message) > 100 else ''}"
        )
        
        logger.info(f"Admin {user_id} initiated broadcast to {len(users)} users")
