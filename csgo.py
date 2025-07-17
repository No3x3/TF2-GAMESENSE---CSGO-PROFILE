import os
import requests
import threading
from pystray import Icon, MenuItem, Menu
from PIL import Image

GAMESENSE_ADDRESS = "http://localhost:51234"
GAME_NAME = "CSGO"
TF2_LOG_PATH = os.path.expanduser("~/tf2_gamelog.txt")

def create_image():
    img = Image.new('RGB', (16, 16), (0, 0, 0))
    return img

def register_gamesense():
    requests.post(f"{GAMESENSE_ADDRESS}/game_metadata", json={
        "game": GAME_NAME,
        "game_display_name": "Team Fortress 2 (via CSGO)",
        "developer": "No3x3"
    })
    requests.post(f"{GAMESENSE_ADDRESS}/register_game", json={"game": GAME_NAME})

def send_event(event_name, value):
    data = {"game": GAME_NAME, "event": event_name, "data": {"value": value}}
    requests.post(f"{GAMESENSE_ADDRESS}/game_event", json=data)

def parse_log_line(line):
    if "Player hurt" in line and "health" in line:
        try:
            hp = int(line.split("health =")[1].strip())
            send_event("HEALTH", hp)
        except:
            pass

def watch_logfile():
    if not os.path.exists(TF2_LOG_PATH):
        print("Brak pliku logu TF2:", TF2_LOG_PATH)
        return
    with open(TF2_LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                continue
            parse_log_line(line.strip())

def run_systray():
    icon = Icon("csgo", create_image(),
                menu=Menu(MenuItem("Wyjdź", lambda ic, it: ic.stop())))
    threading.Thread(target=watch_logfile, daemon=True).start()
    register_gamesense()
    icon.run()

if __name__ == "__main__":
    run_systray()
