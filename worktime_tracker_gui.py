from datetime import datetime, timedelta
import time

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QDesktopWidget

from worktime_tracker import WorktimeTracker


def seconds_to_human_readable(seconds):
    sign = (lambda x: ('', '-')[x < 0])(seconds)
    seconds = int(abs(seconds))
    sec = timedelta(seconds=seconds)
    d = datetime(1, 1, 1) + sec
    return f'{sign}{d.hour}h{d.minute:02d}m'


class WorktimeTrackerThread(QThread, WorktimeTracker):

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
        self.set_geometry(n_lines=2, max_characters=20)
        self.move_upper_right()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.start_thread()
        self.update_ui()

    def move_upper_right(self):
        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = screen.width() - widget.width()
        y = 100
        self.move(x, y)

    def set_geometry(self, n_lines, max_characters):
        self.setGeometry(0, 0, 70 * n_lines + 20, 2 * max_characters + 5)
        self.setContentsMargins(5, 5, 5, 5)

    def start_thread(self):
        self.worktime_tracker_thread = WorktimeTrackerThread()
        self.worktime_tracker_thread.state_changed.connect(self.update_ui)
        self.worktime_tracker_thread.start()

    def lines(self):
        day_work = self.worktime_tracker_thread.todays_work_seconds
        week_overtime = self.worktime_tracker_thread.week_overtime
        target = WorktimeTracker.todays_target()
        day_ratio = day_work / target if target != 0 else 1
        week_ratio = (day_work + week_overtime) / target if target != 0 else 1
        lines = [
            f'Day: {int(100 * day_ratio)}% ({seconds_to_human_readable(day_work)})',
            f'Week: {int(100 * week_ratio)}% ({seconds_to_human_readable(day_work + week_overtime)})',
        ]
        return lines

    @pyqtSlot()
    def update_ui(self):
        self.setText('\n'.join(self.lines()))


if __name__ == '__main__':
    # TODO: Use rumps instead https://github.com/jaredks/rumps (status bar)
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()
