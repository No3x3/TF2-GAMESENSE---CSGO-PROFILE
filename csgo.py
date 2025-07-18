import sys
import os
import json
import requests
from PyQt5 import QtWidgets, QtGui, QtCore

DEFAULT_LOG_PATH = os.path.expanduser("~/tf2_gamelog.txt")

# Kategorie i eventy TF2
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

# Oficjalne eventy GameSense (CSGO)
GAMESENSE_EVENTS = [
    ("HEALTH", "Stan zdrowia gracza"),
    ("AMMO", "Stan amunicji gracza"),
    ("ARMOR", "Pancerz (jeśli dostępny)"),
    ("KILL", "Zabójstwo"),
    ("DEATH", "Śmierć gracza"),
    ("ASSIST", "Asysta"),
    ("DOMINATION", "Dominacja"),
    ("REVENGED", "Zemsta"),
    ("HEADSHOT", "Trafienie w głowę"),
    ("BACKSTAB", "Backstab (cios w plecy)"),
    ("FIRST_BLOOD", "Pierwsze zabójstwo rundy"),
    ("BUILD", "Budowa (inżynier)"),
    ("DESTROY", "Zniszczenie budowli (inżynier)"),
    ("HEAL", "Leczenie"),
    ("UBERCHARGE", "Ubercharge (medyk)"),
    ("FLAG_PICKUP", "Podniesienie flagi"),
    ("FLAG_CAPTURE", "Przejęcie flagi"),
    ("FLAG_DROP", "Upuszczenie flagi"),
    ("POINT_CAPTURE", "Przejęcie punktu kontrolnego"),
    ("BONUS", "Bonus rundy"),
    ("TAUNT", "Wykonanie gestu"),
    ("VOTE_CAST", "Oddanie głosu"),
    ("VOTE_PASS", "Wygrana głosowania"),
    ("RESPAWN", "Odrodzenie"),
    ("INCOMING", "Dołączenie do gry"),
]

def all_tf2_event_choices():
    """Lista (None, 'Nie przypisuj') + pogrupowane eventy"""
    choices = [(None, "Nie przypisuj")]
    for category, events in TF2_EVENT_CATEGORIES.items():
        for code, desc in events:
            choices.append((code, f"[{category}] {code}"))
    return choices

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
            # Nazwa eventu GS
            item = QtWidgets.QTableWidgetItem(f"{gs_name}")
            item.setToolTip(gs_desc)
            self.table.setItem(row, 0, item)

            # Rozwijana lista TF2
            combo = QtWidgets.QComboBox()
            # Dodaj pogrupowane eventy
            combo.addItem("Nie przypisuj", None)
            for category, events in TF2_EVENT_CATEGORIES.items():
                combo.insertSeparator(combo.count())
                for code, desc in events:
                    combo.addItem(f"{category}: {code}", code)
            combo.setToolTip("Wybierz event TF2, który ma być przypisany.")
            combo.currentIndexChanged.connect(lambda idx, row=row, c=combo: self.update_desc(row, c))
            self.table.setCellWidget(row, 1, combo)
            self.combo_boxes.append(combo)

            # Opis eventu (tooltip)
            desc_item = QtWidgets.QTableWidgetItem("–")
            self.table.setItem(row, 2, desc_item)

        layout.addWidget(self.table)

        save_btn = QtWidgets.QPushButton("Zapisz mapowanie do event_map.json")
        save_btn.clicked.connect(self.save_mapping)
        layout.addWidget(save_btn)

    def update_desc(self, row, combo):
        # Opis do wyświetlenia
        code = combo.currentData()
        found = None
        for events in TF2_EVENT_CATEGORIES.values():
            for tf2code, desc in events:
                if code == tf2code:
                    found = desc
        desc = found or "–"
        self.table.item(row, 2).setText(desc)

    def save_mapping(self):
        # Generowanie mapowania
        mapping = {}
        for row, (gs_name, gs_desc) in enumerate(GAMESENSE_EVENTS):
            tf2_code = self.combo_boxes[row].currentData()
            mapping[gs_name] = tf2_code or ""
        with open("event_map.json", "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        QtWidgets.QMessageBox.information(self, "Zapisano", "Mapowanie eventów zapisane do event_map.json.")

class MainWindow(QtWidgets.QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TF2 GameSense Bridge")
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        self.resize(650, 500)

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
            requests.get("http://localhost:51234/", timeout=1)
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

    def start_monitoring(self):
        # Tu możesz dodać funkcję monitorowania loga w tle!
        pass

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
