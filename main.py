import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

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

# Get filters for a specific page
def get_filters_page(page=0, per_page=50):
    conn = sqlite3.connect('filters.db')
    c = conn.cursor()
    offset = page * per_page
    c.execute("SELECT name FROM filters ORDER BY name LIMIT ? OFFSET ?", (per_page, offset))
    filters = [row[0] for row in c.fetchall()]
    
    # Get total count
    c.execute("SELECT COUNT(*) FROM filters")
    total_count = c.fetchone()[0]
    
    conn.close()
    return filters, total_count

# Search filters
def search_filters(query):
    conn = sqlite3.connect('filters.db')
    c = conn.cursor()
    c.execute("SELECT name FROM filters WHERE name LIKE ? ORDER BY name", ('%' + query + '%',))
    filters = [row[0] for row in c.fetchall()]
    conn.close()
    return filters

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Welcome to Anime Filter Bot!\n\n"
        "Use /filter [anime_name] to add a new anime filter\n"
        "Use /filters to see all available filters\n"
        "Use /search [query] to search for filters\n"
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

# Show filters with pagination
def show_filters(update: Update, context: CallbackContext):
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 0
    
    filters, total_count = get_filters_page(page)
    total_pages = (total_count + 49) // 50  # Calculate total pages (ceil division)
    
    if not filters:
        update.message.reply_text("No filters added yet. Use /filter [name] to add one.")
        return
    
    # Create buttons for filters
    keyboard = []
    for i in range(0, len(filters), 2):
        row = []
        if i < len(filters):
            row.append(InlineKeyboardButton(filters[i], callback_data=f"copy:{filters[i]}"))
        if i + 1 < len(filters):
            row.append(InlineKeyboardButton(filters[i+1], callback_data=f"copy:{filters[i+1]}"))
        keyboard.append(row)
    
    # Add navigation buttons if needed
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page:{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"Filters (Page {page+1}/{max(1, total_pages)}):\nClick on an anime to copy its name:",
        reply_markup=reply_markup
    )

# Search command
def search_filters_command(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Please provide a search query. Example: /search Naruto")
        return
    
    query = " ".join(context.args)
    filters = search_filters(query)
    
    if not filters:
        update.message.reply_text(f"No filters found for '{query}'")
        return
    
    # Create buttons for search results
    keyboard = []
    for i in range(0, len(filters), 2):
        row = []
        if i < len(filters):
            row.append(InlineKeyboardButton(filters[i], callback_data=f"copy:{filters[i]}"))
        if i + 1 < len(filters):
            row.append(InlineKeyboardButton(filters[i+1], callback_data=f"copy:{filters[i+1]}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"Search results for '{query}':\nClick on an anime to copy its name:",
        reply_markup=reply_markup
    )

# Handle button clicks
def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    
    if data.startswith("copy:"):
        filter_name = data[5:]  # Remove "copy:" prefix
        query.answer(f"Copied '{filter_name}' to clipboard!", show_alert=True)
    elif data.startswith("page:"):
        page = int(data[5:])  # Remove "page:" prefix and convert to int
        filters, total_count = get_filters_page(page)
        total_pages = (total_count + 49) // 50
        
        # Create buttons for filters
        keyboard = []
        for i in range(0, len(filters), 2):
            row = []
            if i < len(filters):
                row.append(InlineKeyboardButton(filters[i], callback_data=f"copy:{filters[i]}"))
            if i + 1 < len(filters):
                row.append(InlineKeyboardButton(filters[i+1], callback_data=f"copy:{filters[i+1]}"))
            keyboard.append(row)
        
        # Add navigation buttons if needed
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page:{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            f"Filters (Page {page+1}/{max(1, total_pages)}):\nClick on an anime to copy its name:",
            reply_markup=reply_markup
        )

# Stop command
def stop_bot(update: Update, context: CallbackContext):
    update.message.reply_text("Stopping the bot...")

def error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

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
    dp.add_handler(CommandHandler("search", search_filters_command))
    dp.add_handler(CommandHandler("stop", stop_bot))
    dp.add_handler(CallbackQueryHandler(button_callback))
    
    # Log all errors
    dp.add_error_handler(error)
    
    # Start the Bot
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == "__main__":
    main()
    
