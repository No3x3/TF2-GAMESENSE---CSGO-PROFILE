
import sys
import os
import json
import glob
import requests
from PyQt5 import QtWidgets, QtGui, QtCore

GAMESENSE_ADDRESS = "http://localhost:51234"
GAME_NAME = "CS2"

# Oficjalne eventy GameSense – po lewej
GAMESENSE_EVENTS = [
    ("HEALTH", "Stan zdrowia gracza"),
    ("AMMO", "Stan amunicji gracza"),
    ("ARMOR", "Pancerz"),
    ("KILL", "Zabójstwo"),
    ("DEATH", "Śmierć gracza"),
    ("ASSIST", "Asysta"),
    ("HEADSHOT", "Trafienie w głowę"),
    ("MVP", "Nagroda MVP"),
    ("BOMB_PLANT", "Podłożenie bomby"),
    ("BOMB_DEFUSE", "Rozbrojenie bomby"),
    ("BONUS", "Bonus rundy"),
    ("TAUNT", "Wykonanie gestu"),
    ("RESPAWN", "Odrodzenie"),
    ("INCOMING", "Dołączenie do gry"),
]

# Eventy TF2 – po prawej
TF2_EVENTS = [
    ("tf2_health", "Aktualny poziom zdrowia"),
    ("tf2_armor", "Pancerz"),
    ("tf2_ammo", "Amunicja"),
    ("tf2_kill", "Zabójstwo"),
    ("tf2_death", "Śmierć"),
    ("tf2_assist", "Asysta"),
    ("tf2_headshot", "Headshot"),
    ("tf2_flag_pickup", "Podniesienie walizki"),
    ("tf2_flag_capture", "Zdobycie walizki"),
    ("tf2_flag_drop", "Upuszczenie walizki"),
    ("tf2_point_capture", "Przejęcie punktu"),
    ("tf2_backstab", "Backstab"),
    ("tf2_domination", "Dominacja"),
    ("tf2_revenged", "Revenge"),
    ("tf2_first_blood", "Pierwsza krew"),
    ("tf2_respawn", "Respawn"),
    ("tf2_taunt", "Gest"),
    ("tf2_incoming", "Dołączenie"),
    ("tf2_bonus", "Bonus"),
]

def register_gamesense():
    try:
        requests.post(f"{GAMESENSE_ADDRESS}/game_metadata", json={
            "game": GAME_NAME,
            "game_display_name": "Team Fortress 2 (via CS2)",
            "developer": "No3x3"
        })
        requests.post(f"{GAMESENSE_ADDRESS}/register_game", json={"game": GAME_NAME})
    except requests.exceptions.RequestException:
        pass

def send_gamesense_event(event, value=None):
    data = {"game": GAME_NAME, "event": event, "data": {}}
    if value is not None:
        data["data"]["value"] = value
    try:
        requests.post(f"{GAMESENSE_ADDRESS}/game_event", json=data, timeout=0.3)
    except requests.exceptions.RequestException:
        pass

def find_latest_log(logs_folder):
    log_files = glob.glob(os.path.join(logs_folder, "L*.log"))
    if not log_files:
        return None
    return max(log_files, key=os.path.getmtime)

class LogMonitorThread(QtCore.QThread):
    new_event = QtCore.pyqtSignal(str, object)
    def __init__(self, logs_folder, event_map, my_nick=""):
        super().__init__()
        self.logs_folder = logs_folder
        self.event_map = event_map
        self.running = True
        self.current_logfile = None
        self.last_position = 0
        self.my_nick = my_nick
        self.last_health = None
        self.last_armor = None
        self.last_ammo = None

    def run(self):
        while self.running:
            latest_log = find_latest_log(self.logs_folder)
            if not latest_log:
                self.msleep(500)
                continue
            if latest_log != self.current_logfile:
                self.current_logfile = latest_log
                self.last_position = 0
            try:
                with open(self.current_logfile, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(self.last_position)
                    lines = f.readlines()
                    self.last_position = f.tell()
                for line in lines:
                    self.process_line(line.strip())
            except Exception:
                pass
            self.msleep(100)

    def stop(self):
        self.running = False

    def process_line(self, line):
        lline = line.lower()
        nick = self.my_nick or "Dawid"  # zmień na swój nick z TF2

        # HEALTH
        if "health" in lline and any(s in lline for s in [nick.lower(), "changed", "+", "-", "="]):
            for word in line.split():
                if word.isdigit() and 0 < int(word) < 1000:
                    health = int(word)
                    if health != self.last_health:
                        self.last_health = health
                        self.emit_event('tf2_health', health)

        # ARMOR (w TF2 to rzadkość, do samodzielnego rozbudowania jeśli używasz modyfikacji)
        if "armor" in lline:
            for word in line.split():
                if word.isdigit():
                    armor = int(word)
                    if armor != self.last_armor:
                        self.last_armor = armor
                        self.emit_event('tf2_armor', armor)

        # AMMO
        if "ammo" in lline:
            for word in line.split():
                if word.isdigit() and int(word) < 9999:
                    ammo = int(word)
                    if ammo != self.last_ammo:
                        self.last_ammo = ammo
                        self.emit_event('tf2_ammo', ammo)

        # KILL
        if 'killed' in lline and '"' in lline:
            if f'"{nick}"' in lline:
                self.emit_event('tf2_kill')
            elif 'killed' in lline and f'"{nick}"' not in lline:
                self.emit_event('tf2_death')

        # HEADSHOT
        if 'headshot' in lline:
            self.emit_event('tf2_headshot')

        # FLAG_PICKUP
        if 'picked up the intelligence' in lline:
            self.emit_event('tf2_flag_pickup')

        # FLAG_CAPTURE
        if 'captured the intelligence' in lline:
            self.emit_event('tf2_flag_capture')

        # FLAG_DROP
        if 'dropped the intelligence' in lline:
            self.emit_event('tf2_flag_drop')

        # POINT_CAPTURE
        if 'captured point' in lline or 'captured control point' in lline:
            self.emit_event('tf2_point_capture')

        # BACKSTAB
        if 'backstab' in lline:
            self.emit_event('tf2_backstab')

        # DOMINATION
        if 'dominated' in lline:
            self.emit_event('tf2_domination')

        # REVENGE
        if 'got revenge' in lline or 'revenge' in lline:
            self.emit_event('tf2_revenged')

        # FIRST BLOOD
        if 'first blood' in lline:
            self.emit_event('tf2_first_blood')

        # RESPAWN
        if 'respawned' in lline or 'has respawned' in lline:
            self.emit_event('tf2_respawn')

        # TAUNT
        if 'taunt' in lline:
            self.emit_event('tf2_taunt')

        # INCOMING
        if 'joined team' in lline or 'connected' in lline:
            self.emit_event('tf2_incoming')

        # BONUS
        if 'bonus' in lline or 'mvp' in lline:
            self.emit_event('tf2_bonus')

        # ASSIST
        if 'assist' in lline:
            self.emit_event('tf2_assist')

    def emit_event(self, tf2_event, value=None):
        self.new_event.emit(tf2_event, value)

class EventMapWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.table = QtWidgets.QTableWidget(len(GAMESENSE_EVENTS), 3)
        self.table.setHorizontalHeaderLabels(["Event GameSense", "Przypisz event TF2", "Opis eventu TF2"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.combo_boxes = []

        for row, (gs_name, gs_desc) in enumerate(GAMESENSE_EVENTS):
            item = QtWidgets.QTableWidgetItem(f"{gs_name}")
            item.setToolTip(gs_desc)
            self.table.setItem(row, 0, item)

            combo = QtWidgets.QComboBox()
            combo.addItem("Nie przypisuj", None)
            for tf2_code, tf2_desc in TF2_EVENTS:
                combo.addItem(f"{tf2_code}", tf2_code)
            combo.setToolTip("Wybierz event TF2, który ma być przypisany.")
            combo.currentIndexChanged.connect(lambda idx, row=row, c=combo: self.update_desc(row, c))
            self.table.setCellWidget(row, 1, combo)
            self.combo_boxes.append(combo)

            desc_item = QtWidgets.QTableWidgetItem("–")
            self.table.setItem(row, 2, desc_item)

        layout.addWidget(self.table)

        save_btn = QtWidgets.QPushButton("Zapisz mapowanie do event_map.json")
        save_btn.clicked.connect(self.save_mapping)
        layout.addWidget(save_btn)

    def get_mapping(self):
        mapping = {}
        for row, (gs_name, gs_desc) in enumerate(GAMESENSE_EVENTS):
            tf2_code = self.combo_boxes[row].currentData()
            mapping[gs_name] = tf2_code or ""
        return mapping

    def load_mapping(self):
        if os.path.exists("event_map.json"):
            with open("event_map.json", encoding="utf-8") as f:
                mapping = json.load(f)
            for row, (gs_name, gs_desc) in enumerate(GAMESENSE_EVENTS):
                tf2_code = mapping.get(gs_name, "")
                combo = self.combo_boxes[row]
                for idx in range(combo.count()):
                    if combo.itemData(idx) == tf2_code:
                        combo.setCurrentIndex(idx)
                        break

    def update_desc(self, row, combo):
        code = combo.currentData()
        desc = "–"
        for tf2_code, tf2_desc in TF2_EVENTS:
            if code == tf2_code:
                desc = tf2_desc
        self.table.item(row, 2).setText(desc)

    def save_mapping(self):
        mapping = self.get_mapping()
        with open("event_map.json", "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        QtWidgets.QMessageBox.information(self, "Zapisano", "Mapowanie eventów zapisane do event_map.json.")

class MainWindow(QtWidgets.QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TF2 GameSense Bridge")
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        self.resize(750, 500)

        # Zakładka 1 — ustawienia loga
        self.settings_tab = QtWidgets.QWidget()
        settings_layout = QtWidgets.QVBoxLayout()
        self.settings_tab.setLayout(settings_layout)

        form = QtWidgets.QFormLayout()
        self.logs_folder_edit = QtWidgets.QLineEdit(self.default_logs_folder())
        self.browse_btn = QtWidgets.QPushButton("Wybierz folder...")
        self.browse_btn.clicked.connect(self.choose_logs_folder)
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.logs_folder_edit)
        path_layout.addWidget(self.browse_btn)
        form.addRow("Folder z logami TF2:", path_layout)

        self.status_label = QtWidgets.QLabel("Niepołączony")
        self.status_dot = QtWidgets.QLabel("●")
        self.status_dot.setStyleSheet("color: red; font-size: 20px")
        status_layout = QtWidgets.QHBoxLayout()
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_label)
        form.addRow("Status GameSense:", status_layout)

        self.nick_edit = QtWidgets.QLineEdit("")
        form.addRow("Twój nick w TF2:", self.nick_edit)

        self.monitor_btn = QtWidgets.QPushButton("Start monitoring")
        self.monitor_btn.clicked.connect(self.toggle_monitor)
        self.monitoring = False

        settings_layout.addLayout(form)
        settings_layout.addWidget(self.monitor_btn)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_gamesense)
        self.timer.start(2000)
        self.check_gamesense()

        # Zakładka 2 — mapowanie eventów
        self.event_map_tab = EventMapWidget()
        self.event_map_tab.load_mapping()

        self.addTab(self.settings_tab, "Ustawienia logów")
        self.addTab(self.event_map_tab, "Mapowanie eventów")

        QtCore.QTimer.singleShot(1000, register_gamesense)

        self.monitor_thread = None

    def default_logs_folder(self):
        possible_paths = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steamapps\common\Team Fortress 2\tf\logs"),
            os.path.expandvars(r"%ProgramFiles%\Steam\steamapps\common\Team Fortress 2\tf\logs"),
            os.path.expanduser(r"~/Steam/steamapps/common/Team Fortress 2/tf/logs"),
            r"d:\steamlibrary\steamapps\common\team fortress 2\tf\logs",
        ]
        for p in possible_paths:
            if os.path.isdir(p):
                return p
        return os.path.expanduser("~/tf2logs")

    def choose_logs_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz folder z logami TF2", self.logs_folder_edit.text())
        if folder:
            self.logs_folder_edit.setText(folder)

    def check_gamesense(self):
        try:
            requests.get(f"{GAMESENSE_ADDRESS}/", timeout=1)
            self.status_dot.setStyleSheet("color: green; font-size: 20px")
            self.status_label.setText("Połączony")
        except Exception:
            self.status_dot.setStyleSheet("color: red; font-size: 20px")
            self.status_label.setText("Niepołączony")

    def toggle_monitor(self):
        if not self.monitoring:
            self.monitor_btn.setText("Stop monitoring")
            self.monitoring = True
            self.start_monitoring()
        else:
            self.monitor_btn.setText("Start monitoring")
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.stop()
                self.monitor_thread.wait()
                self.monitor_thread = None

    def start_monitoring(self):
        logs_folder = self.logs_folder_edit.text()
        event_map = self.event_map_tab.get_mapping()
        nick = self.nick_edit.text() or "Dawid"
        self.monitor_thread = LogMonitorThread(logs_folder, event_map, nick)
        self.monitor_thread.new_event.connect(self.handle_new_event)
        self.monitor_thread.start()

    def handle_new_event(self, tf2_event, value):
        event_map = self.event_map_tab.get_mapping()
        for gs_event, tf2_code in event_map.items():
            if tf2_code == tf2_event:
                send_gamesense_event(gs_event, value)

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
