"""
[Distros]
Ubuntu = amd64, arm64, i386
Arch Linux = amd64, arm64
Fedora = x86_64, aarch64
Debian = amd64, arm64, armel, i386, mips64el, mipsel

"""

import configparser
from typing import Dict, List

CONFIG_FILENAME = ".iso-usbupdater.ini"


class ConfigManager:
    def __init__(self, config_file: str = CONFIG_FILENAME):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """Loads configuration from the iso-usbupdater.ini file."""
        self.config.read(self.config_file)

    def get_distros(self) -> Dict[str, List[str]]:
        """
        Returns available distros and their architectures.
        Example output: {'Ubuntu': ['amd64', 'arm64'], 'Arch Linux': ['amd64']}
        """
        distros = {}
        if "Distros" in self.config:
            for distro, archs in self.config["Distros"].items():
                distros[distro] = [arch.strip() for arch in archs.split(",")]
        return distros

    def update_distro(self, distro_config_key: str, architectures: List[str]):
        """Updates or adds a new distro with its architectures."""
        if "Distros" not in self.config:
            self.config["Distros"] = {}
        self.config["Distros"][distro_config_key] = ", ".join(architectures)
        self.save_config()

    def remove_distro(self, distro_config_key: str):
        """Removes a distro from the configuration."""
        if "Distros" in self.config and distro_config_key in self.config["Distros"]:
            del self.config["Distros"][distro_config_key]
            self.save_config()

    def save_config(self):
        """Writes changes back to the config file."""
        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)
