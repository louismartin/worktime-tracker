import time

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, Qt  # pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QLabel, QDesktopWidget  # pylint: disable=no-name-in-module

from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.date_utils import get_current_weekday


class WorktimeTrackerThread(QThread, WorktimeTracker):

    state_changed = pyqtSignal()

    def run(self):
        while True:
            state_changed = self.check_state()
            if state_changed:
                self.state_changed.emit()
            time.sleep(10)


class Window(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('State Tracker')
        self.set_geometry(n_lines=get_current_weekday() + 1, max_characters=20)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.start_thread()

    def move_upper_right(self):
        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = screen.width() - widget.width()
        y = 100
        self.move(x, y)

    def set_geometry(self, n_lines, max_characters):
        self.setGeometry(0, 0, max_characters * 7 + 20, n_lines * 17 + 5)
        self.setContentsMargins(5, 5, 5, 5)
        self.move_upper_right()

    def start_thread(self):
        self.worktime_tracker_thread = WorktimeTrackerThread()
        self.worktime_tracker_thread.state_changed.connect(self.update_text)
        self.worktime_tracker_thread.start()

    def lines(self):
        return self.worktime_tracker_thread.lines()

    @pyqtSlot()
    def update_text(self):
        lines = self.lines()
        self.setText('\n'.join(lines))
        self.set_geometry(n_lines=len(lines), max_characters=max([len(line) for line in lines]))


def start():
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()
