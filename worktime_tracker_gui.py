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
        self.setGeometry(0, 0, 158, 45)
        self.setContentsMargins(5, 5, 5, 5)
        self.move_upper_right()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.worktime_tracker_thread = WorktimeTrackerThread()
        self.worktime_tracker_thread.state_changed.connect(self.update_ui)
        self.worktime_tracker_thread.start()
        self.update_ui()

    def move_upper_right(self):
        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = screen.width() - widget.width()
        y = 100
        self.move(x, y)

    @pyqtSlot()
    def update_ui(self):
        weekday = WorktimeTracker.get_timestamp_weekday(time.time())
        cum_times = self.worktime_tracker_thread.cum_times
        week_overtime = self.worktime_tracker_thread.week_overtime
        day_work = self.worktime_tracker_thread.todays_work_seconds
        target = WorktimeTracker.todays_target()
        ratio = day_work / target if target != 0 else 1
        text = f'Day: {int(100 * ratio)}% ({seconds_to_human_readable(day_work)})\n'
        ratio = (day_work + week_overtime) / target if target != 0 else 1
        text += f'Week: {int(100 * ratio)}% ({seconds_to_human_readable(day_work + week_overtime)})\n'
        states_to_print = []  # ['email', 'leisure']
        text += '\n'.join([f'{state.capitalize():8} {seconds_to_human_readable(cum_times[weekday, state])}'
                           for state in states_to_print])
        self.setText(text.strip('\n'))


if __name__ == '__main__':
    # TODO: Use rumps instead https://github.com/jaredks/rumps (status bar)
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()
