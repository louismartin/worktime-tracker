import json
from dataclasses import dataclass

from worktime_tracker.constants import REPO_DIR

# TODO: Actually implement that

@dataclass
class Config:
    """
    Configuration class for the application.
    """
    config_path = REPO_DIR / "config.json"
    interface: str = "cli"
    show_day_worktime: bool = True

    def __init__(self) -> None:
        self.load_config()

    def load_config(self):
        if self.config_path.exists():
            with self.config_path.open() as f:
                config = json.load(f)
                self.__dict__.update(config)


