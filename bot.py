"""
Main bot implementation for Quotex VIP Channel Bot
"""

import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import Database
from verification_simple import VerificationService
from admin import AdminHandler
from config import Config

logger = logging.getLogger(__name__)

class QuotexVIPBot:
    def __init__(self):
        self.token = Config.BOT_TOKEN
        self.db = Database(Config.DATABASE_PATH)
        self.verification_service = VerificationService()
        self.admin_handler = AdminHandler(self.db)

        if not self.token:
            raise ValueError("BOT_TOKEN not provided in environment variables")

        # Initialize the application
        self.application = Application.builder().token(self.token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup command and message handlers"""
        # User commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("verify", self.verify_command))

        # Admin commands
        self.application.add_handler(CommandHandler("admin_add_links", self.admin_handler.add_links_command))
        self.application.add_handler(CommandHandler("admin_stats", self.admin_handler.stats_command))
        self.application.add_handler(CommandHandler("admin_users", self.admin_handler.users_command))
        self.application.add_handler(CommandHandler("admin_broadcast", self.admin_handler.broadcast_command))

        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        logger.info("Bot handlers setup complete")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not update.message:
            return

        user = update.message.from_user
        logger.info(f"User {user.id} ({user.username}) started the bot")

        await update.message.reply_text(
            Config.WELCOME_MESSAGE
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if not update.message:
            return

        await update.message.reply_text(
            Config.HELP_MESSAGE
        )

    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify command"""
        if not update.message:
            return

        user = update.message.from_user
        telegram_id = user.id

        # Check if user is already verified
        if self.db.is_user_verified(telegram_id):
            await update.message.reply_text(Config.ALREADY_VERIFIED)
            return

        # Get Quotex user ID from command arguments
        if not context.args:
            await update.message.reply_text(
                f"{Config.INVALID_USER_ID}\n\n"
                f"🔗 **Haven't registered yet?**\n"
                f"Register first: https://broker-qx.pro/sign-up/?lid=996329"
            )
            return

        quotex_user_id = context.args[0].strip()

        # Validate Quotex user ID format (basic validation)
        if not self._is_valid_quotex_id(quotex_user_id):
            await update.message.reply_text(
                f"{Config.INVALID_USER_ID}\n\n"
                f"🔗 **Haven't registered yet?**\n"
                f"Register first: https://broker-qx.pro/sign-up/?lid=996329"
            )
            return

        logger.info(f"Verification request from {telegram_id} for Quotex ID: {quotex_user_id}")

        # Send processing message
        processing_msg = await update.message.reply_text(
            "🔍 Verifying your Quotex registration with our partner bot...\n"
            "⏳ This may take a few moments, please wait..."
        )

        try:
            # Verify with external service (this may take a few seconds)
            is_verified = self.verification_service.verify_quotex_user(quotex_user_id)

            # Log the verification attempt
            self.db.log_verification_attempt(telegram_id, quotex_user_id, is_verified)

            if is_verified:
                # Get an unused VIP link
                vip_link_data = self.db.get_unused_vip_link()

                if not vip_link_data:
                    await processing_msg.edit_text(Config.NO_LINKS_AVAILABLE)
                    return

                link_id, vip_link = vip_link_data

                # Mark link as used and add user to database
                if self.db.mark_link_as_used(link_id, telegram_id):
                    self.db.add_user(telegram_id, quotex_user_id, link_id)

                    # Send success message with VIP link
                    success_message = (
                        f"{Config.VERIFICATION_SUCCESS}\n\n"
                        f"🔗 {vip_link}\n\n"
                        f"⚠️ This link is unique to you and can only be used once. "
                        f"Don't share it with others!"
                    )

                    await processing_msg.edit_text(success_message)

                    logger.info(f"User {telegram_id} successfully verified and received VIP link")
                else:
                    await processing_msg.edit_text("❌ Error processing your verification. Please try again.")
            else:
                await processing_msg.edit_text(Config.VERIFICATION_FAILED)
                logger.info(f"Verification failed for user {telegram_id} with Quotex ID: {quotex_user_id}")

        except Exception as e:
            logger.error(f"Error during verification process: {e}")
            await processing_msg.edit_text("❌ An error occurred during verification. Please try again later.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages"""
        if not update.message:
            return

        message_text = update.message.text.strip()

        # Check if message looks like a Quotex user ID
        if self._is_valid_quotex_id(message_text):
            user = update.message.from_user
            telegram_id = user.id

            # Check if user is already verified
            if self.db.is_user_verified(telegram_id):
                await update.message.reply_text(Config.ALREADY_VERIFIED)
                return

            # Ask if they want to verify this user ID
            await update.message.reply_text(
                f"🆔 I detected a Quotex User ID: `{message_text}`\n\n"
                f"🔍 Would you like me to verify this ID for VIP access?\n\n"
                f"✅ Type **yes** or **y** to verify\n"
                f"❌ Type **no** or **n** to cancel\n\n"
                f"⚠️ **Important:** Make sure you registered using our referral link:\n"
                f"👉 https://broker-qx.pro/sign-up/?lid=996329",
                parse_mode='Markdown'
            )

            # Store the user ID for verification confirmation
            context.user_data['pending_verification'] = message_text

        elif message_text.lower() in ['yes', 'y', 'verify', 'confirm']:
            # Check if there's a pending verification
            pending_id = context.user_data.get('pending_verification')
            
            if pending_id:
                # Clear the pending verification
                del context.user_data['pending_verification']
                
                # Start the verification process
                await self._process_verification(update, pending_id)
            else:
                await update.message.reply_text(
                    "❓ There's no pending verification.\n\n"
                    "📝 Please send your Quotex User ID first."
                )

        elif message_text.lower() in ['no', 'n', 'cancel']:
            # Cancel pending verification
            if 'pending_verification' in context.user_data:
                del context.user_data['pending_verification']
                await update.message.reply_text(
                    "❌ Verification cancelled.\n\n"
                    "📝 Send your Quotex User ID anytime to try again."
                )
            else:
                await update.message.reply_text(
                    "❓ There's nothing to cancel.\n\n"
                    "📝 **To get VIP access:**\n"
                    "1️⃣ Register: https://broker-qx.pro/sign-up/?lid=996329\n"
                    "2️⃣ Send your Quotex User ID\n\n"
                    "💬 Type /help for more information."
                )
        else:
            # Generic help message for unrecognized input
            await update.message.reply_text(
                "❓ I didn't understand that.\n\n"
                "📝 **To get VIP access:**\n"
                "1️⃣ Register: https://broker-qx.pro/sign-up/?lid=996329\n"
                "2️⃣ Send your Quotex User ID (numbers only)\n\n"
                "💬 Type /help for more information."
            )

    def _is_valid_quotex_id(self, user_id: str) -> bool:
        """Validate Quotex user ID format"""
        # Basic validation - adjust according to actual Quotex ID format
        if not user_id:
            return False

        # Remove any non-digit characters for validation
        clean_id = re.sub(r'\D', '', user_id)

        # Check if it's a reasonable length (adjust as needed)
        return len(clean_id) >= 4 and len(clean_id) <= 20 and clean_id.isdigit()

    async def _process_verification(self, update: Update, quotex_user_id: str):
        """Process verification for a given Quotex user ID"""
        if not update.message:
            return

        user = update.message.from_user
        telegram_id = user.id

        logger.info(f"Processing verification for {telegram_id} with Quotex ID: {quotex_user_id}")

        # Send processing message
        processing_msg = await update.message.reply_text(
            "🔍 Verifying your Quotex registration with our partner bot...\n"
            "⏳ This may take a few moments, please wait..."
        )

        try:
            # Verify with external service (this may take a few seconds)
            is_verified = self.verification_service.verify_quotex_user(quotex_user_id)

            # Log the verification attempt
            self.db.log_verification_attempt(telegram_id, quotex_user_id, is_verified)

            if is_verified:
                # Get an unused VIP link
                vip_link_data = self.db.get_unused_vip_link()

                if not vip_link_data:
                    await processing_msg.edit_text(Config.NO_LINKS_AVAILABLE)
                    return

                link_id, vip_link = vip_link_data

                # Mark link as used and add user to database
                if self.db.mark_link_as_used(link_id, telegram_id):
                    self.db.add_user(telegram_id, quotex_user_id, link_id)

                    # Send success message with VIP link
                    success_message = (
                        f"{Config.VERIFICATION_SUCCESS}\n\n"
                        f"🔗 {vip_link}\n\n"
                        f"⚠️ This link is unique to you and can only be used once. "
                        f"Don't share it with others!"
                    )

                    await processing_msg.edit_text(success_message)

                    logger.info(f"User {telegram_id} successfully verified and received VIP link")
                else:
                    await processing_msg.edit_text("❌ Error processing your verification. Please try again.")
            else:
                await processing_msg.edit_text(Config.VERIFICATION_FAILED)
                logger.info(f"Verification failed for user {telegram_id} with Quotex ID: {quotex_user_id}")

        except Exception as e:
            logger.error(f"Error during verification process: {e}")
            await processing_msg.edit_text("❌ An error occurred during verification. Please try again later.")

    def run(self):
        """Start the bot"""
        try:
            # Test verification service connection
            logger.info("Testing verification connection...")
            if not self.verification_service.test_connection():
                logger.error("Failed to connect to verification service")
                return

            logger.info("Verification service connection successful")

            logger.info("Starting bot polling...")

            # Start the bot
            self.application.run_polling(
                allowed_updates=['message', 'callback_query'],
                drop_pending_updates=True
            )

        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise

    async def broadcast_to_users(self, message: str) -> int:
        """Broadcast message to all verified users"""
        users = self.db.get_recent_users(limit=1000)
        sent_count = 0

        for user in users:
            try:
                await self.application.bot.send_message(
                    chat_id=user['telegram_id'],
                    text=message,
                    parse_mode='HTML'
                )
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to user {user['telegram_id']}: {e}")

        logger.info(f"Broadcast sent to {sent_count}/{len(users)} users")
        return sent_count