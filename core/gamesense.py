import requests

GAMESENSE_ADDRESS = "http://localhost:51234"

class GameSense:
    def __init__(self, game="dota2"):
        self.game = game
        self.register_game()

    def register_game(self):
        data = {
            "game": self.game,
            "game_display_name": "TF2GameSenSNO3",
            "developer": "No3x3"
        }
        requests.post(f"{GAMESENSE_ADDRESS}/game_metadata", json=data)

    def register_event(self, event_name, icon_id=1):
        data = {
            "game": self.game,
            "event": event_name,
            "min_value": 0,
            "max_value": 100,
            "icon_id": icon_id,
            "value_optional": True
        }
        requests.post(f"{GAMESENSE_ADDRESS}/register_game_event", json=data)

    def send_event(self, event_name, value):
        data = {
            "game": self.game,
            "event": event_name,
            "data": {
                "value": value
            }
        }
        requests.post(f"{GAMESENSE_ADDRESS}/game_event", json=data)

    def send_text(self, lines):
        data = {
            "game": self.game,
            "event": "TF2_STATS_DISPLAY",
            "data": {
                "lines": [{"text": line, "has_text": True} for line in lines]
            }
        }
        requests.post(f"{GAMESENSE_ADDRESS}/game_event", json=data)
