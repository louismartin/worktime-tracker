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

    def __post_init__(self):
        self.load_config()

    def load_config(self):
        if not self.config_path.exists():
            self.save_config()
        with self.config_path.open() as f:
            config = json.load(f)
            self.__dict__.update(config)

    def save_config(self):
        with self.config_path.open("w") as f:
            json.dump(self.__dict__, f, indent=4)
