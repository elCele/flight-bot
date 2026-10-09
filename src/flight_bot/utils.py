import time
import inspect
import os
import json
from typing import Any

data_path = os.path.join(os.getcwd(), 'src', 'flight_bot', 'data.json')

def check_id(id: int, chat_id: str) -> bool:
    return id == int(chat_id)

def log_function() -> None:
    print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] > Function {inspect.stack()[1].function} executed")

def update_data(key: str, data: list[Any]) -> None:
    stored_data = {}

    with open(data_path, 'r', encoding='utf-8') as f:
        stored_data = json.load(f)

    stored_data[key] = data

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(stored_data, f, indent=4)
