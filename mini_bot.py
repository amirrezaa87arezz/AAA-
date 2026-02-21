import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext

# Load data from data.json
with open('data.json', 'r') as f:
    data = json.load(f)

TOKEN = 'YOUR_BOT_TOKEN_HERE'

# Bot Initialization
updater = Updater(token=TOKEN, use_context=True)

# Start command

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton('Buy', callback_data='buy'),
                 InlineKeyboardButton('Test', callback_data='test')],
                [InlineKeyboardButton('Services', callback_data='services'),
                 InlineKeyboardButton('Renew', callback_data='renew')],
                [InlineKeyboardButton('Profile', callback_data='profile'),
                 InlineKeyboardButton('Support', callback_data='support')],
                [InlineKeyboardButton('Guide', callback_data='guide'),
                 InlineKeyboardButton('Invite', callback_data='invite')],
                [InlineKeyboardButton('Testimonials', callback_data='testimonials')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Welcome to the VPN Sales Bot! Choose an option:', reply_markup=reply_markup)

# Handle button clicks

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'buy':
        query.edit_message_text(text='Redirecting to buy options...')
        # Logic for buy
    elif query.data == 'test':
        query.edit_message_text(text='Testing options...')
        # Logic for test
    elif query.data == 'services':
        query.edit_message_text(text='Services offered...')
        # Logic for services
    elif query.data == 'renew':
        query.edit_message_text(text='Renew options...')
        # Logic for renew
    elif query.data == 'profile':
        query.edit_message_text(text='Profile management...')
        # Logic for profile
    elif query.data == 'support':
        query.edit_message_text(text='Support options...')
        # Logic for support
    elif query.data == 'guide':
        query.edit_message_text(text='Guides available...')
        # Logic for guide
    elif query.data == 'invite':
        query.edit_message_text(text='Invite your friends...')
        # Logic for invite
    elif query.data == 'testimonials':
        query.edit_message_text(text='Testimonials...')
        # Logic for testimonials

# Add handlers
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CallbackQueryHandler(button))

# Start the bot
updater.start_polling()
updater.idle()