import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Data file to store anime list
DATA_FILE = 'anime_data.json'

class AnimeFilterBot:
    def __init__(self):
        self.filters_active = {}  # Track which chats have active filters
        
    def load_anime_data(self):
        """Load anime data from JSON file"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def save_anime_data(self, data):
        """Save anime data to JSON file"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        await update.message.reply_text(
            '🎌 Welcome to Anime Filters Bot!\n\n'
            'Commands:\n'
            '/filters <anime_name> - Add an anime to the filter list\n'
            '/list - Show all anime in the filter list\n'
            '/stop - Stop showing filters\n'
            '/help - Show this help message'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        await update.message.reply_text(
            '🎌 Anime Filters Bot Help\n\n'
            'Commands:\n'
            '• /filters <anime_name> - Add an anime to the filter list\n'
            '• /list - Show all anime names (copyable text)\n'
            '• /stop - Stop showing filters\n'
            '• /help - Show this help message\n\n'
            'Usage:\n'
            '1. Use "/filters Jujutsu Kaisen" to add an anime\n'
            '2. Use "/list" to see all anime names\n'
            '3. Tap and hold any anime name to copy it'
        )
    
    async def add_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add anime to filter list"""
        if not context.args:
            await update.message.reply_text(
                '❌ Please provide an anime name!\n'
                'Example: /filters Demon Slayer'
            )
            return
        
        anime_name = ' '.join(context.args)
        chat_id = str(update.effective_chat.id)
        
        # Load current data
        data = self.load_anime_data()
        
        # Initialize chat data if not exists
        if chat_id not in data:
            data[chat_id] = {'anime_list': [], 'filters_active': True}
        
        # Add anime if not already in list
        if anime_name not in data[chat_id]['anime_list']:
            data[chat_id]['anime_list'].append(anime_name)
            self.save_anime_data(data)
            
            await update.message.reply_text(
                f'✅ Added "{anime_name}" to the filter list!\n'
                f'Total anime: {len(data[chat_id]["anime_list"])}'
            )
        else:
            await update.message.reply_text(
                f'⚠️ "{anime_name}" is already in the filter list!'
            )
    
    async def list_anime(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all anime as copyable text"""
        chat_id = str(update.effective_chat.id)
        data = self.load_anime_data()
        
        if chat_id not in data or not data[chat_id]['anime_list']:
            await update.message.reply_text(
                '📝 No anime in the filter list yet!\n'
                'Use /filters <anime_name> to add some.'
            )
            return
        
        if not data[chat_id].get('filters_active', True):
            await update.message.reply_text(
                '🚫 Filters are currently stopped.\n'
                'Ask an admin to restart them.'
            )
            return
        
        anime_list = data[chat_id]['anime_list']
        
        # Create text list of anime names
        anime_text = '\n'.join([f'• {anime}' for anime in anime_list])
        
        await update.message.reply_text(
            f'🎌 **Anime Filter List ({len(anime_list)} total):**\n\n'
            f'{anime_text}\n\n'
            '📋 Tap and hold any anime name above to copy it!',
            parse_mode='Markdown'
        )
    
    
    async def stop_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop showing filters"""
        chat_id = str(update.effective_chat.id)
        data = self.load_anime_data()
        
        if chat_id not in data:
            data[chat_id] = {'anime_list': [], 'filters_active': False}
        else:
            data[chat_id]['filters_active'] = False
        
        self.save_anime_data(data)
        
        await update.message.reply_text(
            '🚫 Filters have been stopped!\n'
            'Users won\'t be able to see the anime list until filters are reactivated.'
        )
    
    async def start_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start/restart showing filters"""
        chat_id = str(update.effective_chat.id)
        data = self.load_anime_data()
        
        if chat_id not in data:
            data[chat_id] = {'anime_list': [], 'filters_active': True}
        else:
            data[chat_id]['filters_active'] = True
        
        self.save_anime_data(data)
        
        await update.message.reply_text(
            '✅ Filters have been activated!\n'
            'Users can now see and click on anime names using /list'
        )

def main():
    """Start the bot."""
    # Get bot token from environment variable
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    # Create bot instance
    bot = AnimeFilterBot()
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("filters", bot.add_filter))
    application.add_handler(CommandHandler("list", bot.list_anime))
    application.add_handler(CommandHandler("stop", bot.stop_filters))
    application.add_handler(CommandHandler("restart", bot.start_filters))  # Alternative to start filters
    
    # Run the bot
    logger.info("Starting Anime Filter Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()


