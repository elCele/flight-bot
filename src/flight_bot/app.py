import os
import html
from functools import wraps

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, Update
from telegram.error import BadRequest
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

from flight_bot.utils import (
    InvalidInput,
    add_iata,
    airport_picker_view,
    build_keyboard,
    cancel_row,
    check_id,
    date_view,
    dates_view,
    filters_view,
    flights_page_view,
    log,
    parse_price,
    read_data,
    remove_iata,
    search_menu_view,
    split_ids,
    update_data
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

FIELD_LABELS = {
    "departure_id": "Partenze",
    "arrival_id": "Arrivi"
}

FILTER_STATES = {
    "waiting_add_departure_id": ("departure_id", add_iata),
    "waiting_remove_departure_id": ("departure_id", remove_iata),
    "waiting_add_arrival_id": ("arrival_id", add_iata),
    "waiting_remove_arrival_id": ("arrival_id", remove_iata)
}


def authorized(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if user is None or not check_id(user.id, CHAT_ID):
            log(1, "ID not recognized")
            return

        return await func(update, context)

    return wrapper


def clear_state(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("current_state", None)
    context.user_data.pop("menu_message_id", None)


async def edit(query, text: str, markup):
    try:
        await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise


@authorized
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    callback = query.data

    if callback == "return_to_menu_search":
        await edit(query, *search_menu_view())

    elif callback.startswith("search_by_date_"):
        page = int(callback.rsplit('_', 1)[1])
        await edit(query, *dates_view(page))

    elif callback.startswith("date_"):
        selected_date = callback.split('_', 1)[1]
        await edit(query, *date_view(selected_date))

    elif callback == "search_by_departure":
        await edit(query, *airport_picker_view("departure"))

    elif callback == "search_by_arrival":
        await edit(query, *airport_picker_view("arrival"))

    elif callback.startswith(("departure_", "arrival_")):
        field, code, page = callback.split('_', 2)
        await edit(query, *flights_page_view(field, code, int(page)))

    elif callback == "return_to_menu_filters":
        clear_state(context)
        await edit(query, *filters_view(read_data()))

    elif callback in ("update_departure_id", "update_arrival_id"):
        field = callback.removeprefix("update_")

        context.user_data.pop("current_state", None)
        context.user_data['menu_message_id'] = query.message.message_id

        keyboard = build_keyboard(
            [
                InlineKeyboardButton("➕️ Aggiungi", callback_data=f"add_{field}"),
                InlineKeyboardButton("➖️ Rimuovi", callback_data=f"remove_{field}")
            ],
            cancel_row()
        )

        await edit(query, f"{FIELD_LABELS[field]}: scegli l'azione da eseguire", keyboard)

    elif callback in ("add_departure_id", "remove_departure_id", "add_arrival_id", "remove_arrival_id"):
        action, field = callback.split('_', 1)
        verb = "inserire" if action == "add" else "rimuovere"

        context.user_data['current_state'] = f"waiting_{callback}"
        context.user_data['menu_message_id'] = query.message.message_id

        await edit(
            query,
            f"{FIELD_LABELS[field]}: scrivi il codice IATA dell'aeroporto da {verb}",
            build_keyboard(cancel_row())
        )

    elif callback == "update_max_price":
        context.user_data['current_state'] = "waiting_max_price"
        context.user_data['menu_message_id'] = query.message.message_id

        await edit(query, "Scrivi il nuovo prezzo massimo:", build_keyboard(cancel_row()))

    log(0, callback)


@authorized
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("current_state")

    if state is None:
        await update.message.reply_text("Usa i pulsanti o i comandi suggeriti per interagire con il bot")
        return

    chat_id = update.effective_chat.id
    menu_msg_id = context.user_data.get("menu_message_id")
    text = update.message.text.strip()

    try:
        await update.message.delete()
    except Exception:
        pass

    keep_state = False

    try:
        if state == "waiting_max_price":
            update_data('max_price', parse_price(text))
        else:
            field, apply = FILTER_STATES[state]
            values = apply(split_ids(read_data()[field]), text)
            update_data(field, ','.join(values))

        view_text, markup = filters_view(read_data())
        log(0, state)

    except InvalidInput as e:
        log(1, e)
        keep_state = True
        view_text = html.escape(str(e))
        markup = build_keyboard(cancel_row())

    except Exception as e:
        log(1, e)
        view_text = "Si è verificato un errore durante il salvataggio"
        markup = build_keyboard(cancel_row())

    if not keep_state:
        clear_state(context)

    if menu_msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_msg_id,
                text=view_text,
                parse_mode="HTML",
                reply_markup=markup
            )
        except BadRequest as e:
            log(1, e)
    else:
        await context.bot.send_message(chat_id=chat_id, text=view_text, parse_mode="HTML", reply_markup=markup)


@authorized
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name

    await update.message.reply_text(f"Ciao {name}!\nBenvenuto nella ricerca dei viaggi a poco prezzo!")

    log(0)


@authorized
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔹️ /start - Fa partire il bot\n"
        "🔹️ /help - Mostra questa lista di comandi\n"
        "🔹️ /filters - Mostra la lista di filtri su cui si basa la ricerca\n"
        "🔹️ /search - Fa partire la ricerca"
    )

    await update.message.reply_text(text)

    log(0)


@authorized
async def get_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text, markup = filters_view(read_data())

        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)

        log(0)
    except Exception as e:
        log(1, e)


@authorized
async def search_flights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text, markup = search_menu_view()

        await update.message.reply_text(text, reply_markup=markup)

        log(0)
    except Exception as e:
        log(1, e)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log(1, context.error)


def run():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("filters", get_filters))
    app.add_handler(CommandHandler("search", search_flights))

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.add_error_handler(error_handler)

    log(0, "Bot ready for messages ...")
    app.run_polling()