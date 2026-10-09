import serpapi
import os
import json
from dotenv import load_dotenv
from flight_bot.utils import data_path

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')

client = serpapi.Client(api_key=API_TOKEN)

with open(data_path, 'r', encoding='utf-8') as f:
  data = json.load(f)

results = client.search({
    "engine": "google_flights",
    "departure_id": data['departure_id'],
    "arrival_id": data['arrival_id'],
    "outbound_date": "2026-11-15",
    "type": 2,
    "currency": data['currency'],
    "sort_by": 2,
    "max_price": data['max_price']
}).as_dict()

flights = results['other_flights']

for f in flights:
  flight_data = f['flights'][0]

  data['flights'].append({
    'flight_number': flight_data['flight_number'],
    'airline': flight_data['airline'],
    'price': f['price'],
    'departure_airport': flight_data['departure_airport']['name'],
    'arrival_airport': flight_data['arrival_airport']['name'],
    'date': '2026-11-15',
    'departure_time': flight_data['departure_airport']['time'].split(' ')[1],
    'arrival_time': flight_data['arrival_airport']['time'].split(' ')[1],
    'duration': flight_data['duration']
  })

with open(data_path, 'w', encoding='utf-8') as f:
  json.dump(data, f, indent=4)
