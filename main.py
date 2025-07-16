import sys
import time
import threading
from core.gamesense import GameSense
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

class TrayApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        self.tray_icon = QSystemTrayIcon(QIcon("icon.ico"), self)
        self.menu = QMenu()
        exit_action = QAction("Zamknij", self)
        exit_action.triggered.connect(self.quit)
        self.menu.addAction(exit_action)
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self.toggle_window)
        self.tray_icon.show()

    def toggle_window(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            print("Kliknięto ikonę. (GUI niezaimplementowane)")

def start_logic():
    gs = GameSense()
    EVENTS = {
        "TF2_HEALTH": 1,
        "TF2_KILLS": 2,
        "TF2_HEADSHOTS": 113,
        "TF2_STATS_DISPLAY": 8
    }
    for e, i in EVENTS.items():
        gs.register_event(e, icon_id=i)

    kills = 0
    headshots = 0

    def simulate_kill():
        nonlocal kills, headshots
        kills += 1
        if kills % 3 == 0:
            headshots += 1
        gs.send_event("TF2_KILLS", kills)
        gs.send_event("TF2_HEADSHOTS", headshots)
        gs.send_text([f"Kills: {kills}", f"Headshots: {headshots}"])

    timer = QTimer()
    timer.timeout.connect(simulate_kill)
    timer.start(3000)

    return timer

if __name__ == "__main__":
    app = TrayApp(sys.argv)
    logic_timer = start_logic()
    sys.exit(app.exec_())
