import sys
import os
import requests
from PyQt5 import QtWidgets, QtGui, QtCore

DEFAULT_LOG_PATH = os.path.expanduser("~/tf2_gamelog.txt")

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TF2 GameSense Bridge")
        self.setWindowIcon(QtGui.QIcon("icon.ico"))

        # Layouty
        layout = QtWidgets.QVBoxLayout()
        form = QtWidgets.QFormLayout()

        # Ścieżka loga
        self.log_path_edit = QtWidgets.QLineEdit(DEFAULT_LOG_PATH)
        self.browse_btn = QtWidgets.QPushButton("Wybierz...")
        self.browse_btn.clicked.connect(self.choose_log_path)
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.log_path_edit)
        path_layout.addWidget(self.browse_btn)
        form.addRow("Plik logu TF2:", path_layout)

        # Kod do konsoli TF2
        self.cmd_edit = QtWidgets.QLineEdit(self.gen_console_cmd())
        self.cmd_edit.setReadOnly(True)
        self.copy_btn = QtWidgets.QPushButton("Kopiuj")
        self.copy_btn.clicked.connect(self.copy_cmd)
        cmd_layout = QtWidgets.QHBoxLayout()
        cmd_layout.addWidget(self.cmd_edit)
        cmd_layout.addWidget(self.copy_btn)
        form.addRow("Kod do konsoli TF2:", cmd_layout)

        # Status GameSense
        self.status_label = QtWidgets.QLabel("Niepołączony")
        self.status_dot = QtWidgets.QLabel("●")
        self.status_dot.setStyleSheet("color: red; font-size: 20px")
        status_layout = QtWidgets.QHBoxLayout()
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_label)
        form.addRow("Status GameSense:", status_layout)

        # Start/Stop monitorowania
        self.monitor_btn = QtWidgets.QPushButton("Start monitoring")
        self.monitor_btn.clicked.connect(self.toggle_monitor)
        self.monitoring = False

        layout.addLayout(form)
        layout.addWidget(self.monitor_btn)
        self.setLayout(layout)

        # Timer do sprawdzania statusu GameSense
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_gamesense)
        self.timer.start(2000)
        self.check_gamesense()

        # Aktualizacja kodu konsoli przy zmianie ścieżki
        self.log_path_edit.textChanged.connect(self.update_console_cmd)

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
