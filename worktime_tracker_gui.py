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
        self.set_geometry(n_lines=WorktimeTracker.current_weekday() + 1, max_characters=20)
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
        def weekday_text(weekday_idx):
            weekday = WorktimeTracker.weekdays[weekday_idx]
            work_time = self.worktime_tracker_thread.get_work_time_from_weekday(weekday_idx)
            target = WorktimeTracker.targets[weekday_idx]
            ratio = work_time / target if target != 0 else 1
            return f'{weekday[:3]}: {int(100 * ratio)}% ({seconds_to_human_readable(work_time)})'

        return [weekday_text(weekday_idx) for weekday_idx in range(WorktimeTracker.current_weekday() + 1)][::-1]

    @pyqtSlot()
    def update_text(self):
        lines = self.lines()
        self.setText('\n'.join(lines))
        self.set_geometry(n_lines=len(lines), max_characters=max([len(line) for line in lines]))


if __name__ == '__main__':
    # TODO: Use rumps instead https://github.com/jaredks/rumps (status bar)
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()
