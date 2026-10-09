import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import json
import time

from flight_bot.utils import check_id, log_function, update_data

# Variable definition

# Retrieve .env info
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def start(update: Update, context):
    id = update.effective_user.id

    if check_id(id, CHAT_ID):
        name = update.effective_user.first_name

        await update.message.reply_text(f"Ciao {name}!\nBenvenuto nella ricerca dei viaggi a poco prezzo!")

        log_function()

    else:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] > Blocked access from {id}")

async def help(update: Update, context):
    id = update.effective_user.id

    if check_id(id, CHAT_ID):
        text = "/start - Fa partire il bot\n/help - Mostra questa pagina di aiuto"

        await update.message.reply_text(text)

        log_function()
    else: print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] > Blocked access from {id}")

def run():
    # Create the app for the bot with the token
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add the handlers
    app.add_handler(CallbackQueryHandler(btns_handler))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))

    # Start the polling waiting
    print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] > Bot ready for messages ...")
    app.run_polling()
