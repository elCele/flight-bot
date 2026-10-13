import serpapi
import os
import json
from datetime import date as dt
from dotenv import load_dotenv
from flight_bot.utils import data_path, next_month_dates

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')

client = serpapi.Client(api_key=API_TOKEN)

month_date = next_month_dates()

with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

TEST = False

if TEST:
    ids = data['arrival_id'].split(',')
    airports = ids[1:]

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

    raise SystemExit

if not isinstance(data.get('flights'), dict):
    data['flights'] = {}

today = dt.today().isoformat()
data['flights'] = {d: fl for d, fl in data['flights'].items() if d >= today}

ids = data['arrival_id'].split(',')
airports = ids[1:]
chunks = [ids[0]] + [",".join(airports[i:i + 10]) for i in range(0, len(airports), 10)]

for i, date in enumerate(month_date, 1):
    print(f"[{i}/{len(month_date)}] {date}...", end=" ", flush=True)

    found = []
    for arr in chunks:
        results = client.search({
            "engine": "google_flights",
            "departure_id": data['departure_id'],
            "arrival_id": arr,
            "outbound_date": date,
            "type": 2,
            "currency": data['currency'],
            "sort_by": 2,
            "max_price": int(data['max_price'])
        }).as_dict()
        found += results.get('best_flights', []) + results.get('other_flights', [])

    seen = set()
    day_flights = []
    for fl in found:
        if 'price' not in fl:
            continue

        flight_data = fl['flights'][0]
        key = (flight_data['flight_number'], flight_data['departure_airport']['time'])
        if key in seen:
            continue
        seen.add(key)
        day_flights.append({
            'flight_number': flight_data['flight_number'],
            'airline': flight_data['airline'],
            'price': fl['price'],
            'departure_airport': flight_data['departure_airport']['name'],
            'departure_airport_id': flight_data['departure_airport']['id'],
            'arrival_airport': flight_data['arrival_airport']['name'],
            'arrival_airport_id': flight_data['arrival_airport']['id'],
            'departure_time': flight_data['departure_airport']['time'].split(' ')[1],
            'arrival_time': flight_data['arrival_airport']['time'].split(' ')[1],
            'duration': flight_data['duration']
        })

    day_flights.sort(key=lambda x: x['price'])
    data['flights'][date] = day_flights
    print(f"{len(day_flights)} voli")

    with open(data_path, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, indent=4)