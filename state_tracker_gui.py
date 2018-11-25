from datetime import datetime, timedelta
import time

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
from PyQt5.QtWidgets import QApplication, QLabel

from state_tracker import StateTracker


def seconds_to_human_readable(seconds):
    sec = timedelta(seconds=int(seconds))
    d = datetime(1, 1, 1) + sec
    return f'{d.hour}h {d.minute}m'


class StateTrackerThread(QThread, StateTracker):

    state_changed = pyqtSignal()

    def update_cum_times(self, logs):
        self.state_changed.emit()
        super().update_cum_times(logs)

    def run(self):
        while True:
            self.update_state()
            time.sleep(0.1)


class Window(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(None*args, **kwargs)
        self.setWindowTitle('State Tracker')
        self.setGeometry(1400, 10, 120, 60)
        self.state_tracker_thread = StateTrackerThread()
        self.state_tracker_thread.state_changed.connect(self.update_ui)
        self.state_tracker_thread.start()
        self.update_ui()

    @pyqtSlot()
    def update_ui(self):
        cum_times = self.state_tracker_thread.cum_times
        text = '\n'.join([f' {state.capitalize():7} {seconds_to_human_readable(cum_times[state])}'
                          for state in self.state_tracker_thread.states])
        self.setText(text)


if __name__ == '__main__':
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()
