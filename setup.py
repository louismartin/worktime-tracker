#!/usr/bin/env python
from pathlib import Path
import subprocess
import sys

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def setup_macos():
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "install_launchagent.py"), "install"],
        check=True,
    )


def custom_setup():
    if sys.platform == "darwin":
        setup_macos()


def get_requirements():
    with open("requirements.txt", "r", encoding="utf8") as f:
        requirements = f.read().strip().split("\n")
    if sys.platform == "darwin":
        with open("requirements_macos.txt", "r", encoding="utf8") as f:
            requirements += f.read().strip().split("\n")
    else:
        raise NotImplementedError(f"OS {sys.platform} is not supported")
    return requirements


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        custom_setup()
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        custom_setup()
        install.run(self)


setup(
    name="worktime_tracker",
    version="0.1",
    description="Worktime Tracker",
    author="Louis Martin",
    author_email="louisrtm@gmail.com",
    packages=["worktime_tracker"],
    cmdclass={
        "develop": PostDevelopCommand,
        "install": PostInstallCommand,
    },
    install_requires=get_requirements(),
)
