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

if not isinstance(data.get('flights'), dict):
    data['flights'] = {}

today = dt.today().isoformat()
data['flights'] = {d: fl for d, fl in data['flights'].items() if d >= today}

for i, date in enumerate(month_date, 1):
    print(f"[{i}/{len(month_date)}] {date}...", end=" ", flush=True)

    results = client.search({
        "engine": "google_flights",
        "departure_id": data['departure_id'],
        "arrival_id": data['arrival_id'],
        "outbound_date": date,
        "type": 2,
        "currency": data['currency'],
        "sort_by": 2,
        "max_price": data['max_price']
    }).as_dict()

    found = results.get('best_flights', []) + results.get('other_flights', [])
    print(f"{len(found)} voli")

    day_flights = []
    for fl in found:
        flight_data = fl['flights'][0]
        day_flights.append({
            'flight_number': flight_data['flight_number'],
            'airline': flight_data['airline'],
            'price': fl['price'],
            'departure_airport': flight_data['departure_airport']['name'],
            'arrival_airport': flight_data['arrival_airport']['name'],
            'departure_time': flight_data['departure_airport']['time'].split(' ')[1],
            'arrival_time': flight_data['arrival_airport']['time'].split(' ')[1],
            'duration': flight_data['duration']
        })

    data['flights'][date] = day_flights

    with open(data_path, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, indent=4)