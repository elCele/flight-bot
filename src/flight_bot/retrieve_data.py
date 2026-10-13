import os
import sys
from datetime import date as dt

import requests
import serpapi
from dotenv import load_dotenv

from flight_bot.utils import log, next_month_dates, read_data, split_ids, update_data

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

TEST = False

CHUNK_SIZE = 10
MAX_CONSECUTIVE_FAILURES = 3
TOP_N = 5


def notify(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        return

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=15
        )
        response.raise_for_status()
    except requests.RequestException as e:
        log(1, e)


def load_dict(data: dict, key: str) -> dict:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def build_chunks(arrival_id: str) -> list[str]:
    ids = split_ids(arrival_id)

    if not ids:
        raise ValueError("arrival_id vuoto")

    airports = ids[1:]

    return [ids[0]] + [",".join(airports[i:i + CHUNK_SIZE]) for i in range(0, len(airports), CHUNK_SIZE)]


def search_day(client, data: dict, chunks: list[str], day: str) -> list[dict]:
    found = []

    for arr in chunks:
        results = client.search({
            "engine": "google_flights",
            "departure_id": data['departure_id'],
            "arrival_id": arr,
            "outbound_date": day,
            "type": 2,
            "currency": data['currency'],
            "sort_by": 2,
            "max_price": int(data['max_price']),
            "stops": 1
        }).as_dict()

        found += results.get('best_flights', []) + results.get('other_flights', [])

    seen = set()
    day_flights = []

    for fl in found:
        legs = fl.get('flights', [])

        if 'price' not in fl or len(legs) != 1:
            continue

        leg = legs[0]
        flight_number = leg.get('flight_number')

        if not flight_number:
            continue

        key = (flight_number, leg['departure_airport']['time'])
        if key in seen:
            continue
        seen.add(key)

        day_flights.append({
            'flight_number': flight_number,
            'airline': leg.get('airline'),
            'price': fl['price'],
            'departure_airport': leg['departure_airport']['name'],
            'departure_airport_id': leg['departure_airport']['id'],
            'arrival_airport': leg['arrival_airport']['name'],
            'arrival_airport_id': leg['arrival_airport']['id'],
            'departure_time': leg['departure_airport']['time'].split(' ')[1],
            'arrival_time': leg['arrival_airport']['time'].split(' ')[1],
            'duration': leg.get('duration')
        })

    day_flights.sort(key=lambda x: x['price'])

    return day_flights


def run_test(client, data: dict) -> None:
    airports = split_ids(data['arrival_id'])[1:]

    base = {
        "engine": "google_flights",
        "departure_id": data['departure_id'],
        "outbound_date": "2026-11-01",
        "type": 2,
        "currency": data['currency'],
        "sort_by": 2,
        "max_price": data['max_price'],
        "stops": 1
    }

    tests = {
        "10 aeroporti": ",".join(airports[:10]),
        "11 aeroporti": ",".join(airports),
        "LWN solo": "LWN",
        "10 senza LWN + ultimo": ",".join(airports[:9] + [airports[10]]),
    }

    for name, arr in tests.items():
        r = client.search({**base, "arrival_id": arr}).as_dict()
        found = r.get('best_flights', []) + r.get('other_flights', [])
        print(name, '->', len(found), [x['price'] for x in found], r.get('error', ''))


def build_report(data: dict, new_flights: list[dict], ok: int, total: int, failed: list[str], aborted: bool) -> str:
    currency = data['currency']

    lines = [
        "⚠️ Ricerca interrotta" if aborted else "✅ Ricerca completata",
        f"📅 Date aggiornate: {ok}/{total}",
        f"✈️ Voli trovati: {len(new_flights)}"
    ]

    if failed:
        lines.append(f"❌ Date fallite: {len(failed)}")

    cheapest = sorted(new_flights, key=lambda x: (x['price'], x['date']))[:TOP_N]

    if cheapest:
        lines += ["", "Più economici:"]
        lines += [
            f"✈️ {fl['date']} {fl['departure_airport_id']} -> {fl['arrival_airport_id']} a {fl['price']} {currency} - {fl['flight_number']}"
            for fl in cheapest
        ]

    return "\n".join(lines)


def main() -> int:
    data = read_data()
    client = serpapi.Client(api_key=API_TOKEN)

    if TEST:
        run_test(client, data)
        return 0

    today = dt.today().isoformat()
    month_date = next_month_dates()
    chunks = build_chunks(data['arrival_id'])

    flights = {d: fl for d, fl in load_dict(data, 'flights').items() if d >= today}
    updated_at = {d: u for d, u in load_dict(data, 'updated_at').items() if d in flights}

    new_flights = []
    failed = []
    ok = 0
    consecutive_failures = 0
    aborted = False

    for i, day in enumerate(month_date, 1):
        print(f"[{i}/{len(month_date)}] {day}...", end=" ", flush=True)

        try:
            day_flights = search_day(client, data, chunks, day)
        except Exception as e:
            print("errore")
            log(1, f"{day}: {e}")
            failed.append(day)
            consecutive_failures += 1

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                aborted = True
                break

            continue

        consecutive_failures = 0
        ok += 1

        flights[day] = day_flights
        updated_at[day] = today
        new_flights += [{**fl, 'date': day} for fl in day_flights]

        print(f"{len(day_flights)} voli")

        update_data('flights', flights)
        update_data('updated_at', updated_at)

    notify(build_report(data, new_flights, ok, len(month_date), failed, aborted))

    return 1 if aborted else 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as e:
        log(1, e)
        notify(f"⚠️ Ricerca fallita: {e}")
        exit_code = 1

    sys.exit(exit_code)