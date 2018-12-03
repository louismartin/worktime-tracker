from datetime import datetime, timedelta
import time

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QDesktopWidget

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
        super().__init__(*args, **kwargs)
        self.setWindowTitle('State Tracker')
        self.setGeometry(0, 0, 120, 55)
        self.setContentsMargins(5, 0, 0, 0)
        self.move_upper_right()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.state_tracker_thread = StateTrackerThread()
        self.state_tracker_thread.state_changed.connect(self.update_ui)
        self.state_tracker_thread.start()
        self.update_ui()

    def move_upper_right(self):
        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = screen.width() - widget.width()
        y = 100
        self.move(x, y)

    @pyqtSlot()
    def update_ui(self):
        cum_times = self.state_tracker_thread.cum_times
        total_work_seconds = cum_times['work'] + cum_times['email']
        total_work_time = seconds_to_human_readable(total_work_seconds)
        email_time = seconds_to_human_readable(cum_times['email'])
        leisure_time = seconds_to_human_readable(cum_times['leisure'])
        target_work_seconds = 6 * 3600
        ratio = total_work_seconds / target_work_seconds
        text = f'{int(100 * ratio)}% ({total_work_time})\n'
        states_to_print = ['email', 'leisure']
        text += '\n'.join([f'- {state.capitalize():8} {seconds_to_human_readable(cum_times[state])}'
                           for state in states_to_print])
        self.setText(text)

if __name__ == '__main__':
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()
