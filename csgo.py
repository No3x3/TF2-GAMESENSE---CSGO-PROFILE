import os
import requests
import threading
import time
from pystray import Icon, MenuItem, Menu
from PIL import Image

GAMESENSE_ADDRESS = "http://localhost:51234"
GAME_NAME = "CSGO"
TF2_LOG_PATH = os.path.expanduser("~/tf2_gamelog.txt")

def create_image():
    return Image.new('RGB', (16, 16), color=(0, 0, 0))

def is_gamesense_available():
    try:
        r = requests.get(f"{GAMESENSE_ADDRESS}/", timeout=1)
        return True
    except requests.exceptions.RequestException:
        return False

def register_gamesense():
    try:
        requests.post(f"{GAMESENSE_ADDRESS}/game_metadata", json={
            "game": GAME_NAME,
            "game_display_name": "Team Fortress 2 (via CSGO)",
            "developer": "No3x3"
        })
        requests.post(f"{GAMESENSE_ADDRESS}/register_game", json={"game": GAME_NAME})
        print("[INFO] GameSense zarejestrowany jako CSGO.")
    except requests.exceptions.RequestException as e:
        print("[BŁĄD] Rejestracja GameSense nie powiodła się:", e)

def send_event(event_name, value):
    data = {
        "game": GAME_NAME,
        "event": event_name,
        "data": {"value": value}
    }
    try:
        requests.post(f"{GAMESENSE_ADDRESS}/game_event", json=data)
    except requests.exceptions.RequestException:
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
                time.sleep(0.05)
                continue
            parse_log_line(line.strip())

def parse_log_line(line):
    if "Player hurt" in line and "health" in line:
        try:
            parts = line.split("health =")
            hp = int(parts[1].strip())
            send_event("HEALTH", hp)
        except Exception:
            pass

def wait_for_gamesense():
    print("[INFO] Oczekiwanie na uruchomienie GameSense Engine...")
    while not is_gamesense_available():
        time.sleep(2)
    print("[OK] GameSense Engine dostępny.")

def run_systray():
    wait_for_gamesense()
    register_gamesense()
    threading.Thread(target=watch_logfile, daemon=True).start()
    icon = Icon("csgo", create_image(),
                menu=Menu(MenuItem("Wyjdź", lambda icon, item: icon.stop())))
    icon.run()

if __name__ == "__main__":
    run_systray()
