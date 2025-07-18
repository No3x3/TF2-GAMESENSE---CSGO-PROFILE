import sys
import os
import json
import requests
from PyQt5 import QtWidgets, QtGui, QtCore

DEFAULT_LOG_PATH = os.path.expanduser("~/tf2_gamelog.txt")
GAMESENSE_ADDRESS = "http://localhost:51234"
GAME_NAME = "CS2"

# Kategorie i eventy TF2 (bez zmian)
TF2_EVENT_CATEGORIES = {
    "Zdrowie i amunicja": [
        ("tf2_health", "Pokazuje aktualny poziom zdrowia gracza po otrzymaniu obrażeń lub leczeniu."),
        ("tf2_overheal", "Pokazuje nadwyżkę zdrowia (overheal) po uzyskaniu leczenia powyżej bazowego poziomu."),
        ("tf2_ammo", "Pokazuje aktualny stan amunicji po oddaniu strzału, przeładowaniu lub zmianie broni."),
        ("tf2_armor", "Pokazuje poziom pancerza (jeśli dotyczy klasy/modyfikacji)."),
    ],
    "Zabójstwa i śmierć": [
        ("tf2_kill", "Aktywowany po zabiciu przeciwnika przez gracza."),
        ("tf2_death", "Aktywowany po śmierci gracza."),
        ("tf2_assist", "Aktywowany, gdy gracz asystuje w eliminacji przeciwnika."),
        ("tf2_domination", "Aktywowany po uzyskaniu dominacji nad przeciwnikiem."),
        ("tf2_revenged", "Aktywowany, gdy gracz mści się na przeciwniku, który nad nim dominował."),
        ("tf2_headshot", "Aktywowany po trafieniu przeciwnika w głowę."),
        ("tf2_backstab", "Aktywowany po zadaniu śmiertelnego ciosu z pleców jako szpieg."),
        ("tf2_first_blood", "Aktywowany przy pierwszym zabójstwie w rundzie."),
    ],
    "Budowle i inżynier": [
        ("tf2_build", "Aktywowany po zbudowaniu budowli inżyniera."),
        ("tf2_destroy", "Aktywowany po zniszczeniu budowli inżyniera przez gracza."),
    ],
    "Leczenie i Uber": [
        ("tf2_heal", "Aktywowany po wyleczeniu innego gracza."),
        ("tf2_ubercharge", "Aktywowany po użyciu ubercharge przez medyka."),
    ],
    "Flag/Point": [
        ("tf2_flag_pickup", "Aktywowany po podniesieniu walizki (CTF) przez gracza."),
        ("tf2_flag_capture", "Aktywowany po zdobyciu walizki przez gracza."),
        ("tf2_flag_drop", "Aktywowany po upuszczeniu walizki przez gracza."),
        ("tf2_point_capture", "Aktywowany po przejęciu punktu kontrolnego przez gracza."),
    ],
    "Pozostałe": [
        ("tf2_bonus", "Aktywowany po zdobyciu bonusu za rundę (np. MVP)."),
        ("tf2_taunt", "Aktywowany po wykonaniu gestu (taunt) przez gracza."),
        ("tf2_vote_cast", "Aktywowany po oddaniu głosu w głosowaniu."),
        ("tf2_vote_pass", "Aktywowany po pozytywnym zakończeniu głosowania."),
        ("tf2_respawn", "Aktywowany po odrodzeniu gracza."),
        ("tf2_incoming", "Aktywowany po dołączeniu gracza do serwera lub drużyny."),
    ],
}

# Oficjalne eventy GameSense dla CS2
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

class LogMonitorThread(QtCore.QThread):
    new_event = QtCore.pyqtSignal(str, object)

    def __init__(self, log_path, event_map):
        super().__init__()
        self.log_path = log_path
        self.event_map = event_map
        self.running = True
        self.last_position = 0
        self.last_health = None
        self.last_ammo = None

    def run(self):
        while self.running:
            if not os.path.isfile(self.log_path):
                self.msleep(500)
                continue
            with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self.last_position)
                lines = f.readlines()
                self.last_position = f.tell()
            for line in lines:
                self.process_line(line.strip())
            self.msleep(100)

    def stop(self):
        self.running = False

    def process_line(self, line):
        # Przykładowe reguły (dopasuj do formatu loga TF2 z con_logfile)
        # HEALTH
        if "Health:" in line:
            try:
                health_str = line.split("Health:")[1].split("/")[0].strip()
                health_val = int(health_str)
                if health_val != self.last_health:
                    self.last_health = health_val
                    self.emit_event('tf2_health', health_val)
            except Exception:
                pass
        # AMMO
        elif "Ammo:" in line:
            try:
                ammo_str = line.split("Ammo:")[1].split()[0].strip()
                ammo_val = int(ammo_str)
                if ammo_val != self.last_ammo:
                    self.last_ammo = ammo_val
                    self.emit_event('tf2_ammo', ammo_val)
            except Exception:
                pass
        # KILL
        elif "killed" in line and "with" in line:
            self.emit_event('tf2_kill')
        # DEATH
        elif "You died" in line or "died" in line:
            self.emit_event('tf2_death')
        # HEADSHOT
        elif "headshot" in line:
            self.emit_event('tf2_headshot')
        # BACKSTAB
        elif "backstab" in line:
            self.emit_event('tf2_backstab')
        # RESPAWN
        elif "respawned" in line or "has respawned" in line:
            self.emit_event('tf2_respawn')

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
        self.event_map = {}

        for row, (gs_name, gs_desc) in enumerate(GAMESENSE_EVENTS):
            item = QtWidgets.QTableWidgetItem(f"{gs_name}")
            item.setToolTip(gs_desc)
            self.table.setItem(row, 0, item)

            combo = QtWidgets.QComboBox()
            combo.addItem("Nie przypisuj", None)
            for category, events in TF2_EVENT_CATEGORIES.items():
                combo.insertSeparator(combo.count())
                for code, desc in events:
                    combo.addItem(f"{category}: {code}", code)
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
        found = None
        for events in TF2_EVENT_CATEGORIES.values():
            for tf2code, desc in events:
                if code == tf2code:
                    found = desc
        desc = found or "–"
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
        self.resize(700, 500)

        # Zakładka 1 — ustawienia loga
        self.settings_tab = QtWidgets.QWidget()
        settings_layout = QtWidgets.QVBoxLayout()
        self.settings_tab.setLayout(settings_layout)

        form = QtWidgets.QFormLayout()
        self.log_path_edit = QtWidgets.QLineEdit(DEFAULT_LOG_PATH)
        self.browse_btn = QtWidgets.QPushButton("Wybierz...")
        self.browse_btn.clicked.connect(self.choose_log_path)
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.log_path_edit)
        path_layout.addWidget(self.browse_btn)
        form.addRow("Plik logu TF2:", path_layout)

        self.cmd_edit = QtWidgets.QLineEdit(self.gen_console_cmd())
        self.cmd_edit.setReadOnly(True)
        self.copy_btn = QtWidgets.QPushButton("Kopiuj")
        self.copy_btn.clicked.connect(self.copy_cmd)
        cmd_layout = QtWidgets.QHBoxLayout()
        cmd_layout.addWidget(self.cmd_edit)
        cmd_layout.addWidget(self.copy_btn)
        form.addRow("Kod do konsoli TF2:", cmd_layout)

        self.status_label = QtWidgets.QLabel("Niepołączony")
        self.status_dot = QtWidgets.QLabel("●")
        self.status_dot.setStyleSheet("color: red; font-size: 20px")
        status_layout = QtWidgets.QHBoxLayout()
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_label)
        form.addRow("Status GameSense:", status_layout)

        self.monitor_btn = QtWidgets.QPushButton("Start monitoring")
        self.monitor_btn.clicked.connect(self.toggle_monitor)
        self.monitoring = False

        settings_layout.addLayout(form)
        settings_layout.addWidget(self.monitor_btn)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_gamesense)
        self.timer.start(2000)
        self.check_gamesense()

        self.log_path_edit.textChanged.connect(self.update_console_cmd)

        # Zakładka 2 — mapowanie eventów
        self.event_map_tab = EventMapWidget()

        self.addTab(self.settings_tab, "Ustawienia logów")
        self.addTab(self.event_map_tab, "Mapowanie eventów")

        QtCore.QTimer.singleShot(1000, register_gamesense)

        self.monitor_thread = None

    def choose_log_path(self):
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Wybierz plik logu", self.log_path_edit.text(), "Text Files (*.txt);;All Files (*)")
        if fname:
            self.log_path_edit.setText(fname)

    def gen_console_cmd(self):
        path = self.log_path_edit.text().replace("\\", "\\\\")
        return f'con_logfile "{path}"'

    def update_console_cmd(self):
        self.cmd_edit.setText(self.gen_console_cmd())

    def copy_cmd(self):
        QtWidgets.QApplication.clipboard().setText(self.cmd_edit.text())

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
        log_path = self.log_path_edit.text()
        event_map = self.event_map_tab.get_mapping()
        self.monitor_thread = LogMonitorThread(log_path, event_map)
        self.monitor_thread.new_event.connect(self.handle_new_event)
        self.monitor_thread.start()

    def handle_new_event(self, tf2_event, value):
        # Znajdź na co zmapowany jest ten event w event_map.json
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
