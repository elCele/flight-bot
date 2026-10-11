import time
import inspect
import os
import json
from typing import Any
from datetime import date
import calendar

data_path = os.path.join(os.getcwd(), 'src', 'flight_bot', 'data.json')
log_path = os.path.join(os.getcwd(), 'src', 'flight_bot', 'log.txt')

def check_id(id: int, chat_id: str) -> bool:
    return id == int(chat_id)

def log(code: int, info: str = "") -> None:
    msg = ""
    timestamp = f"[{time.strftime("%Y-%m-%d %H:%M:%S")}]"

    if code == 0:   # success
        msg = f"Function {inspect.stack()[1].function} operated as expected"
    elif code == 1: # error
        msg = f"Error in {inspect.stack()[1].function} function"

    if info != "":
        msg += f" | {info}"

    text = f"[{code}]-{timestamp} > {msg}\n"

    if inspect.stack()[1].function == "run":
        text = "\n" + text

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(text)

    print(text, end="")

def update_data(key: str, data: list[Any]) -> None:
    stored_data = {}

    with open(data_path, 'r', encoding='utf-8') as f:
        stored_data = json.load(f)

    stored_data[key] = data

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(stored_data, f, indent=4)

def next_month_dates(today=None):
    today = today or date.today()
    year = today.year + (today.month == 12)
    month = today.month % 12 + 1
    days = calendar.monthrange(year, month)[1]
    return [f"{year}-{month:02d}-{d:02d}" for d in range(1, days + 1)]

def get_flights_by(by: str) -> dict:
    if by not in ('date', 'departure_id', 'arrival_id', 'airline'):
        raise ValueError(f"Ordine non valido: {by}")

    with open(data_path, 'r', encoding='utf-8') as f:
        flights = json.load(f).get('flights', {})

    groups = {}

    for date, day in flights.items():
        for fl in day:
            key = date if by == 'date' else fl[by]
            groups.setdefault(key, []).append({**fl, 'date': date})

    for lst in groups.values():
        lst.sort(key=lambda x: (x['price'], x['date'], x['departure_time']))

    return dict(sorted(groups.items()))
