import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import sqlite3

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('filters.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS filters
                 (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    conn.commit()
    conn.close()

# Add filter to database
def add_filter(filter_name):
    conn = sqlite3.connect('filters.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO filters (name) VALUES (?)", (filter_name,))
        conn.commit()
        success = True
    except:
        success = False
    conn.close()
    return success

# Get all filters from database
def get_all_filters():
    conn = sqlite3.connect('filters.db')
    c = conn.cursor()
    c.execute("SELECT name FROM filters ORDER BY name")
    filters = [row[0] for row in c.fetchall()]
    conn.close()
    return filters

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Welcome to Anime Filter Bot!\n\n"
        "Use /filter [anime_name] to add a new anime filter\n"
        "Use /filters to see all available filters\n"
        "Use /stop to stop the bot"
    )

# Add filter command
def add_filter_command(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Please provide an anime name. Example: /filter Naruto")
        return
    
    filter_name = " ".join(context.args)
    if add_filter(filter_name):
        update.message.reply_text(f"Added filter: {filter_name}")
    else:
        update.message.reply_text(f"Filter '{filter_name}' already exists!")

# Show all filters
def show_filters(update: Update, context: CallbackContext):
    filters = get_all_filters()
    if not filters:
        update.message.reply_text("No filters added yet. Use /filter [name] to add one.")
        return
    
    # Create buttons in rows of 2 for better mobile layout
    keyboard = []
    for i in range(0, len(filters), 2):
        row = []
        if i < len(filters):
            row.append(InlineKeyboardButton(filters[i], callback_data=filters[i]))
        if i + 1 < len(filters):
            row.append(InlineKeyboardButton(filters[i+1], callback_data=filters[i+1]))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Click on an anime to copy its name:", reply_markup=reply_markup)

# Handle button clicks
def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer(f"Copied '{query.data}' to clipboard!", show_alert=True)

# Stop command
def stop_bot(update: Update, context: CallbackContext):
    update.message.reply_text("Stopping the bot...")

def main():
    # Initialize database
    init_db()
    
    # Get token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Please set the TELEGRAM_BOT_TOKEN environment variable")
        return
    
    # Create updater with the token
    updater = Updater(token, use_context=True)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("filter", add_filter_command))
    dp.add_handler(CommandHandler("filters", show_filters))
    dp.add_handler(CommandHandler("stop", stop_bot))
    dp.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the Bot
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()

if __name__ == "__main__":
    main()
    
