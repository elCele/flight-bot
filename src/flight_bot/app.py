import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import json
import html

from flight_bot.utils import check_id, log, update_data, data_path

# Retrieve .env info
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def start(update: Update, context):
    user_id = update.effective_user.id

    if not check_id(id, CHAT_ID):
        log(1, "ID not recognized")
        return
    
    name = update.effective_user.first_name

    await update.message.reply_text(f"Ciao {name}!\nBenvenuto nella ricerca dei viaggi a poco prezzo!")

    log(0)

async def help(update: Update, context):
    id = update.effective_user.id

    if not check_id(id, CHAT_ID):
        log(1, "ID not recognized")
        return

    text = (
        "🔹️ /start - Fa partire il bot\n"
        "🔹️ /help - Mostra questa lista di comandi\n"
        "🔹️ /filters - Mostra la lista di filtri su cui si basa la ricerca"
    )

    await update.message.reply_text(text)

    log(0)

async def get_filters(update: Update, context):
    user_id = update.effective_user.id

    if not check_id(user_id, CHAT_ID):
        log(1, "ID not recognized")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = [
        ("🛫", "Partenza", data['departure_id']),
        ("🛬", "Arrivo", data['arrival_id']),
        ("💰", "Prezzo max", f"{data['max_price']} {data['currency']}"),
    ]

    label_w = max(len(l) for _, l, _ in rows) + 3
    val_w = max(len(v) for _, _, v in rows)

    lines = []
    for emoji, label, value in rows:
        left = f"{emoji} {label}"
        left_w = len(label) + 3
        lines.append(f"{left}{' ' * (label_w - left_w)}  {value.rjust(val_w)}")

    text = (
        "✈️ <b>FILTRI RICERCA VOLO</b>\n"
        f"<pre>{html.escape(chr(1).join(lines))}</pre>"
    )

    await update.message.reply_text(text, parse_mode="HTML")
    
    log(0)

def run():
    # Create the app for the bot with the token
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add the handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("filters", get_filters))

    # Start the polling waiting
    log(0, "Bot ready for messages ...")
    app.run_polling()
