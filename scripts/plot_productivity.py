import time
from worktime_tracker.tools import plot_productivity
from worktime_tracker.config import Config

if __name__ == "__main__":
    if Config().show_day_worktime:
        print("Waiting 30s before plotting to prevent using the script as a way to check worktime when disabled...")
        time.sleep(30)
    plot_productivity()
