import logging
import json
import os
import threading
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Data file to store anime list
DATA_FILE = 'anime_data.json'

class AnimeFilterBot:
    def __init__(self):
        pass
        
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
            'Available Commands:\n'
            '/filters <anime_name> - Add an anime to the filter list\n'
            '/list - Show all anime in the filter list\n'
            '/stop - Stop showing filters\n'
            '/restart - Restart showing filters\n'
            '/help - Show detailed help message\n'
            '/count - Show how many anime are in your list'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        await update.message.reply_text(
            '🎌 Anime Filters Bot - Detailed Help\n\n'
            'Commands:\n'
            '• /filters <anime_name> - Add an anime to the filter list\n'
            '• /list - Show all anime names\n'
            '• /stop - Stop showing filters in this chat\n'
            '• /restart - Restart showing filters in this chat\n'
            '• /count - Show how many anime are in your list\n'
            '• /help - Show this help message\n\n'
            'Usage:\n'
            '1. Use "/filters Jujutsu Kaisen" to add an anime\n'
            '2. Use "/list" to see all anime names\n'
            '3. Use "/stop" to temporarily disable filters\n'
            '4. Use "/restart" to enable filters again'
        )
    
    async def add_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add anime to filter list"""
        if not context.args:
            await update.message.reply_text(
                '❌ Please provide an anime name!\n'
                'Example: /filters Demon Slayer\n\n'
                'You can add multiple anime at once:\n'
                '/filters Naruto, One Piece, Attack on Titan'
            )
            return
        
        anime_names = ' '.join(context.args)
        
        # Support both comma-separated and space-separated inputs
        if ',' in anime_names:
            anime_list = [name.strip() for name in anime_names.split(',') if name.strip()]
        else:
            anime_list = [anime_names]
        
        chat_id = str(update.effective_chat.id)
        
        # Load current data
        data = self.load_anime_data()
        
        # Initialize chat data if not exists
        if chat_id not in data:
            data[chat_id] = {'anime_list': [], 'filters_active': True}
        
        added_count = 0
        already_exists = []
        
        for anime_name in anime_list:
            # Add anime if not already in list
            if anime_name and anime_name not in data[chat_id]['anime_list']:
                data[chat_id]['anime_list'].append(anime_name)
                added_count += 1
            elif anime_name:
                already_exists.append(anime_name)
        
        if added_count > 0:
            self.save_anime_data(data)
            
            response = f'✅ Added {added_count} anime to the filter list!\n'
            response += f'Total anime: {len(data[chat_id]["anime_list"])}'
            
            if already_exists:
                response += f'\n\n⚠️ {len(already_exists)} anime already existed: {", ".join(already_exists[:5])}'
                if len(already_exists) > 5:
                    response += f' and {len(already_exists) - 5} more'
            
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                f'⚠️ All provided anime already exist in the filter list!\n'
                f'Current count: {len(data[chat_id]["anime_list"])}'
            )
    
    async def list_anime(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all anime as a simple bulleted list"""
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
                '🚫 Filters are currently stopped in this chat.\n'
                'Use /restart to enable them again.'
            )
            return
        
        anime_list = data[chat_id]['anime_list']
        
        # Create a simple bulleted list
        anime_text = "\n".join([f"• {anime}" for anime in anime_list])
        
        await update.message.reply_text(
            f'🎌 Anime List ({len(anime_list)} total):\n\n{anime_text}'
        )
    
    async def count_anime(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show how many anime are in the list"""
        chat_id = str(update.effective_chat.id)
        data = self.load_anime_data()
        
        if chat_id not in data or not data[chat_id]['anime_list']:
            await update.message.reply_text(
                '📝 No anime in the filter list yet!\n'
                'Use /filters <anime_name> to add some.'
            )
            return
        
        anime_count = len(data[chat_id]['anime_list'])
        await update.message.reply_text(
            f'📊 You have {anime_count} anime in your filter list.\n'
            f'Use /list to view them all.'
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
            '🚫 Filters have been stopped in this chat!\n'
            'Users won\'t be able to see the anime list until filters are reactivated with /restart.'
        )
    
    async def start_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start/restart showing filters"""
        chat_id = str(update.effective_chat.id)
        data = self.load_anime_data()
        
        if chat_id not in data:
            data[chat_id] = {'anime_list': [], 'filters_active': True}
            anime_count = 0
        else:
            data[chat_id]['filters_active'] = True
            anime_count = len(data[chat_id]['anime_list'])
        
        self.save_anime_data(data)
        
        await update.message.reply_text(
            f'✅ Filters have been activated!\n'
            f'Users can now see anime names using /list\n'
            f'Total anime in list: {anime_count}'
        )

# Flask web server for health checks and webhooks
app = Flask(__name__)
bot_instance = None

@app.route('/')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'bot': 'Anime Filter Bot',
        'version': '1.0.0'
    })

@app.route('/status')
def bot_status():
    """Bot status endpoint"""
    # Count total anime across all chats
    if bot_instance:
        data = bot_instance.load_anime_data()
        total_anime = sum(len(chat_data.get('anime_list', [])) for chat_data in data.values())
        total_chats = len(data)
        active_chats = sum(1 for chat_data in data.values() if chat_data.get('filters_active', True))
        
        return jsonify({
            'status': 'running',
            'total_chats': total_chats,
            'active_chats': active_chats,
            'total_anime': total_anime
        })
    return jsonify({'status': 'bot not initialized'})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for Telegram updates"""
    # This can be used for webhook mode instead of polling
    return jsonify({'status': 'webhook received'})

def run_flask_server():
    """Run Flask server in a separate thread"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def main():
    """Start the bot and web server."""
    global bot_instance
    
    # Get bot token from environment variable
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    # Create bot instance
    bot_instance = AnimeFilterBot()
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", bot_instance.start))
    application.add_handler(CommandHandler("help", bot_instance.help_command))
    application.add_handler(CommandHandler("filters", bot_instance.add_filter))
    application.add_handler(CommandHandler("list", bot_instance.list_anime))
    application.add_handler(CommandHandler("count", bot_instance.count_anime))
    application.add_handler(CommandHandler("stop", bot_instance.stop_filters))
    application.add_handler(CommandHandler("restart", bot_instance.start_filters))
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    logger.info("Flask web server started on port 5000")
    
    # Run the bot
    logger.info("Starting Anime Filter Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()


