import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import json
import html
from math import floor

from flight_bot.utils import check_id, log, update_data, data_path, get_flights_by

# Retrieve .env info
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Buttons handler function
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "return_to_menu":
        keyboard = [
            [InlineKeyboardButton("🗓️ Cerca per data", callback_data="search_by_date_0")],
            [InlineKeyboardButton("🛫 Cerca per partenza", callback_data="search_by_departure")],
            [InlineKeyboardButton("🛬 Cerca per destinazione", callback_data="search_by_arrival")],
            [InlineKeyboardButton("👨🏼‍✈️️ Cerca per compagnia", callback_data="search_by_airline")]
        ]
        
        await query.edit_message_text("Scegli tra queste opzioni di ricerca", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("search_by_date_"):
        flights = get_flights_by('date')

        possible_date = list(flights.keys())

        index = 5
        page = int(query.data.split('_')[-1])
        max_page = floor(len(possible_date) / index)

        navigation_buttons = []

        if page == 1:
            navigation_buttons = [InlineKeyboardButton("➡️", callback_data=f"search_by_date_{page + 1}")]
        elif page == max_page:
            navigation_buttons = [InlineKeyboardButton("⬅️", callback_data=f"search_by_date_{page - 1}")]
        else:
            navigation_buttons = [
                InlineKeyboardButton("⬅️", callback_data=f"search_by_date_{page - 1}"),
                InlineKeyboardButton("➡️", callback_data=f"search_by_date_{page + 1}")
            ]

        start_point = (page - 1) * index
        end_point = start_point + index

        while True:
            try:
                to_show = possible_date[start_point:end_point]
                break
            except IndexError:
                end_point -= 1
                continue

        keyboard = [
            *[[InlineKeyboardButton(f"🗓️ {d}", callback_data=f"date_{d}")] for d in to_show],
            navigation_buttons,
            [InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu")]
        ]

        await query.edit_message_text(
            f"🗓️ Ecco a te le date disponibili - pagina {page}/{max_page}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "search_by_departure":
        keyboard = [
            [InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu")]
        ]

        await query.edit_message_text("🛫 Ecco a te gli aeroporti di partenza disponibili", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "search_by_arrival":
        keyboard = [
            [InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu")]
        ]

        await query.edit_message_text("🛬 Ecco a te le destinazioni disponibili", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "search_by_airline":
        keyboard = [
            [InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu")]
        ]

        await query.edit_message_text("️️️👨🏼‍✈️️ Ecco a te le compagnie disponibili", reply_markup=InlineKeyboardMarkup(keyboard))

    log(0, query.data)

# Command functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not check_id(user_id, CHAT_ID):
        log(1, "ID not recognized")
        return
    
    name = update.effective_user.first_name

    await update.message.reply_text(f"Ciao {name}!\nBenvenuto nella ricerca dei viaggi a poco prezzo!")

    log(0)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):            # fix the output layout
    user_id = update.effective_user.id

    if not check_id(user_id, CHAT_ID):
        log(1, "ID not recognized")
        return

    text = (
        "🔹️ /start - Fa partire il bot\n"
        "🔹️ /help - Mostra questa lista di comandi\n"
        "🔹️ /filters - Mostra la lista di filtri su cui si basa la ricerca\n",
        "🔹️ /search - Fa partire la ricerca"
    )

    await update.message.reply_text(text)

    log(0)

async def get_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):         # fix the output layout
    user_id = update.effective_user.id

    if not check_id(user_id, CHAT_ID):
        log(1, "ID not recognized")
        return

    try:
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
    except Exception as e:
        log(1, e)
        return

async def search_flights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_id(user_id, CHAT_ID):
        log(1, "ID not recognized")
        return

    try:
        keyboard = [
            [InlineKeyboardButton("🗓️ Cerca per data", callback_data="search_by_date_1")],
            [InlineKeyboardButton("🛫 Cerca per partenza", callback_data="search_by_departure")],
            [InlineKeyboardButton("🛬 Cerca per destinazione", callback_data="search_by_arrival")],
            [InlineKeyboardButton("👨🏼‍✈️️ Cerca per compagnia", callback_data="search_by_airline")]
        ]

        await update.message.reply_text("Scegli tra queste opzioni di ricerca", reply_markup=InlineKeyboardMarkup(keyboard))

        log(0)
    except Exception as e:
        log(1, e)
        return

def run():
    # Create the app for the bot with the token
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add the handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("filters", get_filters))
    app.add_handler(CommandHandler("search", search_flights))

    # Add the button handler
    app.add_handler(CallbackQueryHandler(button_handler))

    # Start the polling waiting
    log(0, "Bot ready for messages ...")
    app.run_polling()
