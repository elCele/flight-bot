import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import json
import time

from flight_bot.utils import check_id, log_function, reset_json, update_data

# Variable definition

# Retrieve .env info
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def btns_handler(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data() == "set_airports_btn":
        await update_airports(update, context)


async def start(update: Update, context):
    id = update.effective_user.id

    if check_id(id, CHAT_ID):
        reset_json()
        name = update.effective_user.first_name

        buttons = InlineKeyboardButton(
            "✈️ Imposta i tuoi Aeroporti", callback_data="set_airports_btn"
        )

        keyboard = InlineKeyboardMarkup([[buttons]])

        await update.message.reply_text(
            f"Ciao {name}!\nBenvenuto nella ricerca dei viaggi a poco prezzo!\nPremi il pulsante qui sotto per iniziare:",
            reply_markup=keyboard
        )

        update_data("name", name)
        log_function()

    else:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] > Blocked access from {id}")

async def help(update: Update, context):
    id = update.effective_user.id

    if check_id(id, CHAT_ID):
        text = "/start - Fa partire il bot\n/help - Mostra questa pagina di aiuto\n/set_airports cod1 cod2 ... - Definisce gli aereoporti da controllare tramite i codici IATA"

        await update.message.reply_text(text)

        log_function()
    else: print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] > Blocked access from {id}")

async def update_airports(update: Update, context):
    id = update.effective_user.id

    if check_id(id, CHAT_ID):
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text("Inserisci i codici IATA dei tuoi aeroporti abituali separati da spazi:")
        else:
            await update.message.reply_text("Inserisci i codici IATA dei tuoi aeroporti abituali separati da spazi:")

        log_function()

    else:
        print(f" > Blocked access from {id}")

def run():
    # Create the app for the bot with the token
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add the handlers
    app.add_handler(CallbackQueryHandler(btns_handler))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("set_airports", update_airports, has_args=True))

    # Start the polling waiting
    print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] > Bot ready for messages ...")
    app.run_polling()
