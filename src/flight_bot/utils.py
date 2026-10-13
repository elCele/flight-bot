import calendar
import html
import json
import math
import os
import sys
import time
from datetime import date
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

data_path = os.path.join(os.getcwd(), 'src', 'flight_bot', 'data.json')
log_path = os.path.join(os.getcwd(), 'src', 'flight_bot', 'log.txt')

PAGE_SIZE = 5
MAX_MESSAGE_LENGTH = 4000

FLIGHT_KEYS = {
    'date': None,
    'departure_id': 'departure_airport_id',
    'arrival_id': 'arrival_airport_id',
    'airline': 'airline'
}


class InvalidInput(Exception):
    pass


def check_id(id: int, chat_id: str) -> bool:
    try:
        return id == int(chat_id)
    except (TypeError, ValueError):
        return False


def log(code: int, info: Any = "") -> None:
    caller = sys._getframe(1).f_code.co_name
    timestamp = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}]"

    msg = ""
    if code == 0:
        msg = f"Function {caller} operated as expected"
    elif code == 1:
        msg = f"Error in {caller} function"

    info = str(info)
    if info:
        msg += f" | {info}"

    text = f"[{code}]-{timestamp} > {msg}\n"

    if caller == "run":
        text = "\n" + text

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(text)

    print(text, end="")


def read_data() -> dict:
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_data(key: str, data: Any) -> None:
    stored_data = read_data()
    stored_data[key] = data

    tmp_path = data_path + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(stored_data, f, indent=4)

    os.replace(tmp_path, data_path)


def get_flights_by(by: str) -> dict:
    if by not in FLIGHT_KEYS:
        raise ValueError(f"Ordine non valido: {by}")

    flights = read_data().get('flights', {})
    field = FLIGHT_KEYS[by]

    groups = {}

    for flight_date, day in flights.items():
        for fl in day:
            key = flight_date if field is None else fl[field]
            groups.setdefault(key, []).append({**fl, 'date': flight_date})

    for lst in groups.values():
        lst.sort(key=lambda x: (x['price'], x['date'], x['departure_time']))

    return dict(sorted(groups.items()))


def split_ids(value: str) -> list[str]:
    return [x.strip() for x in value.split(',') if x.strip()]


def parse_iata(text: str) -> str:
    code = text.strip().upper()

    if len(code) != 3 or not code.isascii() or not code.isalpha():
        raise InvalidInput("Codice IATA non valido: servono esattamente 3 lettere")

    return code


def add_iata(values: list[str], text: str) -> list[str]:
    code = parse_iata(text)

    if code in values:
        raise InvalidInput("Aeroporto già presente")

    return values + [code]


def remove_iata(values: list[str], text: str) -> list[str]:
    code = parse_iata(text)

    if code not in values:
        raise InvalidInput("Lo IATA indicato non è presente, controllare l'ortografia")

    if len(values) == 1:
        raise InvalidInput("Deve rimanere almeno un aeroporto")

    return [v for v in values if v != code]


def parse_price(text: str) -> int | float:
    try:
        price = float(text.strip().replace(',', '.'))
    except ValueError:
        raise InvalidInput("Prezzo non valido: scrivi un numero")

    if not math.isfinite(price) or price <= 0:
        raise InvalidInput("Il prezzo deve essere un numero maggiore di zero")

    return int(price) if price.is_integer() else price


def home_row() -> list:
    return [InlineKeyboardButton("🏠️ Torna al menù", callback_data="return_to_menu_search")]


def cancel_row() -> list:
    return [InlineKeyboardButton("❌ Annulla", callback_data="return_to_menu_filters")]


def build_keyboard(*rows) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([list(row) for row in rows if row])


def nav_row(prefix: str, page: int, max_page: int) -> list:
    row = []

    if page > 1:
        row.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}_{page - 1}"))
    if page < max_page:
        row.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}_{page + 1}"))

    return row


def flight_line(fl: dict, currency: str) -> str:
    return html.escape(
        f"✈️ {fl['departure_airport_id']} -> {fl['arrival_airport_id']} a {fl['price']} {currency} - {fl['flight_number']}"
    )


def join_lines(header: str, lines: list[str]) -> str:
    text = header

    for line in lines:
        if len(text) + len(line) + 1 > MAX_MESSAGE_LENGTH:
            text += "\n…"
            break
        text += "\n" + line

    return text


def search_menu_view() -> tuple:
    keyboard = [
        [InlineKeyboardButton("🗓️ Cerca per data", callback_data="search_by_date_1")],
        [InlineKeyboardButton("🛫 Cerca per partenza", callback_data="search_by_departure")],
        [InlineKeyboardButton("🛬 Cerca per destinazione", callback_data="search_by_arrival")]
    ]

    return "Scegli tra queste opzioni di ricerca", InlineKeyboardMarkup(keyboard)


def filters_view(data: dict) -> tuple:
    departures = html.escape(', '.join(split_ids(data['departure_id'])))
    arrivals = html.escape(', '.join(split_ids(data['arrival_id'])))

    text = (
        f"🛫 <b>Partenze:</b> {departures}\n\n"
        f"🛬 <b>Arrivi:</b> {arrivals}\n\n"
        f"💰 <b>Prezzo max:</b> {data['max_price']} {html.escape(str(data['currency']))}"
    )

    keyboard = [
        [InlineKeyboardButton("🛫 Modifica partenze", callback_data="update_departure_id")],
        [InlineKeyboardButton("🛬 Modifica arrivi", callback_data="update_arrival_id")],
        [InlineKeyboardButton("💰 Modifica prezzo", callback_data="update_max_price")]
    ]

    return text, InlineKeyboardMarkup(keyboard)


def dates_view(page: int) -> tuple:
    dates = list(get_flights_by('date'))

    if not dates:
        return "Nessun volo disponibile", build_keyboard(home_row())

    max_page = math.ceil(len(dates) / PAGE_SIZE)
    page = min(max(page, 1), max_page)

    start = (page - 1) * PAGE_SIZE
    date_rows = [
        [InlineKeyboardButton(f"🗓️ {d}", callback_data=f"date_{d}")]
        for d in dates[start:start + PAGE_SIZE]
    ]

    markup = build_keyboard(*date_rows, nav_row("search_by_date", page, max_page), home_row())

    return f"🗓️ Ecco a te le date disponibili - pagina {page}/{max_page}", markup


def date_view(selected_date: str) -> tuple:
    data = read_data()
    day_flights = data.get('flights', {}).get(selected_date)

    if not day_flights:
        return f"Nessun volo il {html.escape(selected_date)}", build_keyboard(home_row())

    header = f"🗓️ <b>{html.escape(selected_date)}</b>{updated_label(data, selected_date)}\n"
    lines = [flight_line(fl, data['currency']) for fl in day_flights]

    return join_lines(header, lines), build_keyboard(home_row())


def airport_picker_view(field: str) -> tuple:
    data = read_data()
    codes = split_ids(data[f"{field}_id"])

    icon = "🛫" if field == "departure" else "🛬"
    label = "partenza" if field == "departure" else "arrivo"

    buttons = [InlineKeyboardButton(f"{icon} {c}", callback_data=f"{field}_{c}_1") for c in codes]
    rows = [buttons[i:i + 4] for i in range(0, len(buttons), 4)]

    return f"{icon} Ecco a te gli aeroporti di {label} disponibili", build_keyboard(*rows, home_row())


def flights_page_view(field: str, code: str, page: int) -> tuple:
    data = read_data()
    key = f"{field}_airport_id"

    selected = {}
    for day, day_flights in data.get('flights', {}).items():
        filtered = [fl for fl in day_flights if fl[key] == code]
        if filtered:
            selected[day] = filtered

    days = sorted(selected)

    if not days:
        direction = "da" if field == "departure" else "verso"
        return f"Nessun volo {direction} {html.escape(code)}", build_keyboard(home_row())

    max_page = len(days)
    page = min(max(page, 1), max_page)
    day = days[page - 1]

    header = f"🗓️ <b>{html.escape(day)}</b> - pagina {page}/{max_page}{updated_label(data, day)}\n"
    lines = [flight_line(fl, data['currency']) for fl in selected[day]]

    markup = build_keyboard(nav_row(f"{field}_{code}", page, max_page), home_row())

    return join_lines(header, lines), markup

def updated_label(data: dict, day: str) -> str:
    updated = data.get('updated_at', {}).get(day)

    if not updated:
        return ""

    try:
        updated = date.fromisoformat(updated).strftime('%d/%m')
    except ValueError:
        pass

    return f" (agg. {html.escape(updated)})"