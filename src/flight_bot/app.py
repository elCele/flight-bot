import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json
import html
from math import floor

from flight_bot.utils import *

# Retrieve .env info
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Buttons handler function
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    callback = query.data

    # ====== SEARCH ======
    if callback == "return_to_menu_search":
        keyboard = [
            [InlineKeyboardButton("🗓️ Cerca per data", callback_data="search_by_date_0")],
            [InlineKeyboardButton("🛫 Cerca per partenza", callback_data="search_by_departure")],
            [InlineKeyboardButton("🛬 Cerca per destinazione", callback_data="search_by_arrival")],
            [InlineKeyboardButton("👨🏼‍✈️️ Cerca per compagnia", callback_data="search_by_airline")]
        ]
        
        await query.edit_message_text("Scegli tra queste opzioni di ricerca", reply_markup=InlineKeyboardMarkup(keyboard))

    elif callback.startswith("search_by_date_"):
        flights = get_flights_by('date')

        possible_date = list(flights.keys())

        index = 5
        page = int(callback.split('_')[-1])
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
            [InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu_search")]
        ]

        await query.edit_message_text(
            f"🗓️ Ecco a te le date disponibili - pagina {page}/{max_page}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif callback == "search_by_departure":
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        departure_id = data['departure_id'].split(',')
        
        keyboard = [[InlineKeyboardButton(f"🛫 {d}", callback_data=f"departure_{d}_1") for d in departure_id]]
        keyboard.append([InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu_search")])

        await query.edit_message_text("🛫 Ecco a te gli aeroporti di partenza disponibili", reply_markup=InlineKeyboardMarkup(keyboard))

    elif callback == "search_by_arrival":
        keyboard = [
            [InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu_search")]
        ]

        await query.edit_message_text("🛬 Ecco a te le destinazioni disponibili", reply_markup=InlineKeyboardMarkup(keyboard))

    elif callback == "search_by_airline":
        keyboard = [
            [InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu_search")]
        ]

        await query.edit_message_text("️️️👨🏼‍✈️️ Ecco a te le compagnie disponibili", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- Search by departure ---
    elif callback.startswith("departure_"):
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        _, departure_airport, page = callback.split('_', 2)
        page = int(page)

        selected_flights = {}
        for k, day_flights in data['flights'].items():
            filtered = [fl for fl in day_flights if fl['departure_airport_id'] == departure_airport]
            if filtered:
                selected_flights[k] = filtered

        keys = list(selected_flights)
        max_page = len(keys)

        if max_page == 0:
            await query.edit_message_text(
                f"Nessun volo da {departure_airport}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu_search")]])
            )
            return

        navigation_buttons = []
        
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"departure_{departure_airport}_{page - 1}"))
        if page < max_page:
            navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"departure_{departure_airport}_{page + 1}"))
        else:
            navigation_buttons = [
                InlineKeyboardButton("⬅️", callback_data=f"departure_{departure_airport}_{page - 1}"),
                InlineKeyboardButton("➡️", callback_data=f"departure_{departure_airport}_{page + 1}")
            ]

        keyboard = [
            navigation_buttons,
            [InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu_search")]
        ]

        day = keys[page - 1]
        text = f"🗓️ <b>{day}</b>\n\n" + '\n'.join(
            f"✈️ {fl['departure_airport_id']} -> {fl['arrival_airport_id']} a {fl['price']} {data['currency']} - {fl['flight_number']}"
            for fl in selected_flights[day]
        )

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # ====== FILTERS ======
    elif callback == "return_to_menu_filters":
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        text = (
            f"🛫 <b>Partenze:</b> {', '.join(data['departure_id'].split(','))}\n\n"
            f"🛬 <b>Arrivi:</b> {', '.join(data['arrival_id'].split(','))}\n\n"
            f"💰 <b>Prezzo max:</b> {data['max_price']} {data['currency']}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🛫 Modifica partenze", callback_data="update_departure_id")],
            [InlineKeyboardButton("🛬 Modifica arrivi", callback_data="update_arrival_id")],
            [InlineKeyboardButton("💰 Modifica prezzo", callback_data="update_max_price")]
        ]
        
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- Departures ---
    elif callback == "update_departure_id":
        context.user_data['menu_message_id'] = query.message.message_id

        keyboard = [
            [
                InlineKeyboardButton("➕️ Aggiungi", callback_data="add_departure_id"),
                InlineKeyboardButton("➖️ Rimuovi", callback_data="remove_departure_id")
            ],
            [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
        ]

        await query.edit_message_text("Partenze: scegli l'azione da eseguire", reply_markup=InlineKeyboardMarkup(keyboard))

    elif callback == "add_departure_id":
        context.user_data['current_state'] = "waiting_add_departure_id"
        context.user_data['menu_message_id'] = query.message.message_id

        keyboard = [
            [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
        ]
        
        await query.edit_message_text("Partenze: scrivi il codice IATA dell'aeroporto da inserire", reply_markup=InlineKeyboardMarkup(keyboard))

    elif callback == "remove_departure_id":
        context.user_data['current_state'] = "waiting_remove_departure_id"
        context.user_data['menu_message_id'] = query.message.message_id
        
        keyboard = [
            [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
        ]
        
        await query.edit_message_text("Partenze: scrivi il codice IATA dell'aeroporto da rimuovere", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- Arrivals ---
    elif callback == "update_arrival_id":
        context.user_data['menu_message_id'] = query.message.message_id
    
        keyboard = [
            [
                InlineKeyboardButton("➕️ Aggiungi", callback_data="add_arrival_id"),
                InlineKeyboardButton("➖️ Rimuovi", callback_data="remove_arrival_id")
            ],
            [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
        ]
    
        await query.edit_message_text("Arrivi: scegli l'azione da eseguire", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif callback == "add_arrival_id":
        context.user_data['current_state'] = "waiting_add_arrival_id"
        context.user_data['menu_message_id'] = query.message.message_id
    
        keyboard = [
            [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
        ]
    
        await query.edit_message_text("Arrivi: scrivi il codice IATA dell'aeroporto da inserire", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif callback == "remove_arrival_id":
        context.user_data['current_state'] = "waiting_remove_arrival_id"
        context.user_data['menu_message_id'] = query.message.message_id
    
        keyboard = [
            [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
        ]
    
        await query.edit_message_text("Arrivi: scrivi il codice IATA dell'aeroporto da rimuovere", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # --- Max price ---
    elif callback == "update_max_price":
        context.user_data['current_state'] = "waiting_max_price"
        context.user_data['menu_message_id'] = query.message.message_id

        keyboard = [
            [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
        ]

        await query.edit_message_text("Scrivi il nuovo prezzo massimo:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    log(0, callback)

# User messagge handler function
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("current_state")

    if state == "waiting_add_departure_id":
        new_iata = update.message.text.strip()
        chat_id = update.effective_chat.id
        menu_msg_id = context.user_data.get("menu_message_id")

        try:
            await update.message.delete()
        except Exception:
            pass

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            departure_id = data['departure_id'].split(',')

            departure_id.append(new_iata)

            update_data('departure_id', ','.join(departure_id))

            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            text = (
                f"🛫 <b>Partenze:</b> {', '.join(data['departure_id'].split(','))}\n\n"
                f"🛬 <b>Arrivi:</b> {', '.join(data['arrival_id'].split(','))}\n\n"
                f"💰 <b>Prezzo max:</b> {data['max_price']} {data['currency']}"
            )
            
            keyboard = [
                [InlineKeyboardButton("🛫 Modifica partenze", callback_data="update_departure_id")],
                [InlineKeyboardButton("🛬 Modifica arrivi", callback_data="update_arrival_id")],
                [InlineKeyboardButton("💰 Modifica prezzo", callback_data="update_max_price")]
            ]
            
            if menu_msg_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

            log(0, state)

        except Exception as e:
            log(1, e)
            if menu_msg_id:
                keyboard = [
                    [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
                ]
    
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text="Si è verificato un errore durante l'aggiunta dell'aeroporto",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

        context.user_data.pop("current_state", None)
        context.user_data.pop("menu_message_id", None)

    elif state == "waiting_remove_departure_id":
        iata_to_remove = update.message.text.strip()
        chat_id = update.effective_chat.id
        menu_msg_id = context.user_data.get("menu_message_id")

        try:
            await update.message.delete()
        except Exception:
            pass

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            departure_id = data['departure_id'].split(',')

            if iata_to_remove in departure_id:
                departure_id.remove(iata_to_remove)

                update_data('departure_id', ','.join(departure_id))

                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                text = (
                    f"🛫 <b>Partenze:</b> {', '.join(data['departure_id'].split(','))}\n\n"
                    f"🛬 <b>Arrivi:</b> {', '.join(data['arrival_id'].split(','))}\n\n"
                    f"💰 <b>Prezzo max:</b> {data['max_price']} {data['currency']}"
                )

                keyboard = [
                    [InlineKeyboardButton("🛫 Modifica partenze", callback_data="update_departure_id")],
                    [InlineKeyboardButton("🛬 Modifica arrivi", callback_data="update_arrival_id")],
                    [InlineKeyboardButton("💰 Modifica prezzo", callback_data="update_max_price")]
                ]

                if menu_msg_id:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=menu_msg_id,
                        text=text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )

                log(0, state)
            else:
                raise Exception("Value not found in the departure_id array")

        except Exception as e:
            log(1, e)
            if menu_msg_id:
                keyboard = [
                    [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
                ]

                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text="Lo IATA indicato non è presente, controllare l'ortografia",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

        context.user_data.pop("current_state", None)
        context.user_data.pop("menu_message_id", None)
    
    elif state == "waiting_add_arrival_id":
        new_iata = update.message.text.strip()
        chat_id = update.effective_chat.id
        menu_msg_id = context.user_data.get("menu_message_id")

        try:
            await update.message.delete()
        except Exception:
            pass

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            arrival_id = data['arrival_id'].split(',')

            arrival_id.append(new_iata)

            update_data('arrival_id', ','.join(arrival_id))

            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            text = (
                f"🛫 <b>Partenze:</b> {', '.join(data['departure_id'].split(','))}\n\n"
                f"🛬 <b>Arrivi:</b> {', '.join(data['arrival_id'].split(','))}\n\n"
                f"💰 <b>Prezzo max:</b> {data['max_price']} {data['currency']}"
            )
            
            keyboard = [
                [InlineKeyboardButton("🛫 Modifica partenze", callback_data="update_departure_id")],
                [InlineKeyboardButton("🛬 Modifica arrivi", callback_data="update_arrival_id")],
                [InlineKeyboardButton("💰 Modifica prezzo", callback_data="update_max_price")]
            ]
            
            if menu_msg_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

            log(0, state)

        except Exception as e:
            log(1, e)
            if menu_msg_id:
                keyboard = [
                    [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
                ]
    
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text="Si è verificato un errore durante l'aggiunta dell'aeroporto",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

        context.user_data.pop("current_state", None)
        context.user_data.pop("menu_message_id", None)
    
    elif state == "waiting_remove_arrival_id":
        iata_to_remove = update.message.text.strip()
        chat_id = update.effective_chat.id
        menu_msg_id = context.user_data.get("menu_message_id")

        try:
            await update.message.delete()
        except Exception:
            pass

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            arrival_id = data['arrival_id'].split(',')

            if iata_to_remove in arrival_id:
                arrival_id.remove(iata_to_remove)

                update_data('arrival_id', ','.join(arrival_id))

                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                text = (
                    f"🛫 <b>Partenze:</b> {', '.join(data['departure_id'].split(','))}\n\n"
                    f"🛬 <b>Arrivi:</b> {', '.join(data['arrival_id'].split(','))}\n\n"
                    f"💰 <b>Prezzo max:</b> {data['max_price']} {data['currency']}"
                )

                keyboard = [
                    [InlineKeyboardButton("🛫 Modifica partenze", callback_data="update_departure_id")],
                    [InlineKeyboardButton("🛬 Modifica arrivi", callback_data="update_arrival_id")],
                    [InlineKeyboardButton("💰 Modifica prezzo", callback_data="update_max_price")]
                ]

                if menu_msg_id:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=menu_msg_id,
                        text=text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )

                log(0, state)
            else:
                raise Exception("Value not found in the arrival_id array")

        except Exception as e:
            log(1, e)
            if menu_msg_id:
                keyboard = [
                    [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
                ]

                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text="Lo IATA indicato non è presente, controllare l'ortografia",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

        context.user_data.pop("current_state", None)
        context.user_data.pop("menu_message_id", None)
    
    elif state == "waiting_max_price":
        new_max_price = update.message.text.strip()
        chat_id = update.effective_chat.id
        menu_msg_id = context.user_data.get("menu_message_id")

        try:
            await update.message.delete()
        except Exception:
            pass

        try:
            update_data('max_price', float(new_max_price))

            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            text = (
                f"🛫 <b>Partenze:</b> {', '.join(data['departure_id'].split(','))}\n\n"
                f"🛬 <b>Arrivi:</b> {', '.join(data['arrival_id'].split(','))}\n\n"
                f"💰 <b>Prezzo max:</b> {data['max_price']} {data['currency']}"
            )
            
            keyboard = [
                [InlineKeyboardButton("🛫 Modifica partenze", callback_data="update_departure_id")],
                [InlineKeyboardButton("🛬 Modifica arrivi", callback_data="update_arrival_id")],
                [InlineKeyboardButton("💰 Modifica prezzo", callback_data="update_max_price")]
            ]

            if menu_msg_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

            log(0, state)

        except Exception as e:
            log(1, e)
            if menu_msg_id:
                keyboard = [
                    [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]
                ]

                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text="Si è verificato un errore durante il salvataggio del prezzo",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

        context.user_data.pop("current_state", None)
        context.user_data.pop("menu_message_id", None)
    
    else:
        await update.message.reply_text("Usa i pulsanti o i comandi suggeriti per interagire con il bot")

# Commands functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not check_id(user_id, CHAT_ID):
        log(1, "ID not recognized")
        return
    
    name = update.effective_user.first_name

    await update.message.reply_text(f"Ciao {name}!\nBenvenuto nella ricerca dei viaggi a poco prezzo!")

    log(0)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def get_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not check_id(user_id, CHAT_ID):
        log(1, "ID not recognized")
        return

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        text = (
            f"🛫 <b>Partenze:</b> {', '.join(data['departure_id'].split(','))}\n\n"
            f"🛬 <b>Arrivi:</b> {', '.join(data['arrival_id'].split(','))}\n\n"
            f"💰 <b>Prezzo max:</b> {data['max_price']} {data['currency']}"
        )

        keyboard = [
            [InlineKeyboardButton("🛫 Modifica partenze", callback_data="update_departure_id")],
            [InlineKeyboardButton("🛬 Modifica arrivi", callback_data="update_arrival_id")],
            [InlineKeyboardButton("💰 Modifica prezzo", callback_data="update_max_price")]
        ]

        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
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

    # Add the message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))


    # Start the polling waiting
    log(0, "Bot ready for messages ...")
    app.run_polling()
