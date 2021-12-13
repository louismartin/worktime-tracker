import time

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, Qt  # pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QLabel, QDesktopWidget  # pylint: disable=no-name-in-module

from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.date_utils import get_current_weekday
from worktime_tracker.constants import REFRESH_RATE


class WorktimeTrackerThread(QThread, WorktimeTracker):

    state_changed = pyqtSignal()
    has_run = False

    def run(self):
        while True:
            state_changed = self.check_state()
            if state_changed or not self.has_run:
                self.state_changed.emit()
                self.has_run = True
            time.sleep(REFRESH_RATE)


class Window(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("State Tracker")
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

    @pyqtSlot()
    def update_text(self):
        summaries = self.worktime_tracker_thread.get_week_summaries()
        self.setText("\n".join(summaries))
        self.set_geometry(n_lines=len(summaries), max_characters=max([len(summary) for summary in summaries]))


def start():
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()
