import time
import inspect
import os
import json
from typing import Any

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

    text = f"[{code}]-{timestamp} > {msg}"

    if inspect.stack()[1].function == "run":
        text = "\n" + text

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(text)

    print(text)

def update_data(key: str, data: list[Any]) -> None:
    stored_data = {}

    with open(data_path, 'r', encoding='utf-8') as f:
        stored_data = json.load(f)

    stored_data[key] = data

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(stored_data, f, indent=4)
