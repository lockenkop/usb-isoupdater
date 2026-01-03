"""
[Distros]
Ubuntu = amd64, arm64, i386
Arch Linux = amd64, arm64
Fedora = x86_64, aarch64
Debian = amd64, arm64, armel, i386, mips64el, mipsel

"""

import configparser
from pathlib import Path

import pyudev

from distro_sources.distro_base import Distro
from distro_sources.http_distros import DISTROS

CONFIG_FILENAME = Path(".iso-usbupdater.ini")


class ConfigManager:
    def __init__(self, config_file: Path = CONFIG_FILENAME):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """Loads configuration from the iso-usbupdater.ini file."""
        self.config.read(self.config_file)

    def get_usb_device(self) -> dict[str, str] | None:
        """Returns the USB device path from the configuration, if set."""

        if "USB" in self.config and "DevicePath" in self.config["USB"]:
            usb_device = {
                "devicepath": self.config["USB"]["Devicepath"],
                "vendorid": self.config["USB"]["VendorID"],
                "modelid": self.config["USB"]["ModelID"],
            }
        else:
            usb_device = None
        return usb_device

    def update_usb_device(self, device: pyudev.Device):
        """Updates the USB device path in the configuration."""
        if "USB" not in self.config:
            self.config["USB"] = {}
        self.config["USB"]["devicepath"] = device.device_node if device.device_node else "unknown"
        self.config["USB"]["vendorid"] = device.get("ID_VENDOR_ID", "")
        self.config["USB"]["modelid"] = device.get("ID_MODEL_ID", "")
        self.save_config()

    def get_distros(self) -> list[Distro]:
        """
        Returns configured distros and their architectures.
        Example output: {'Ubuntu': ['amd64', 'arm64'], 'Arch Linux': ['amd64']}
        """
        distros = []
        for key in self.config.keys():
            if key == "USB":
                continue
            config_entry = self.config[key]
            if "name" in config_entry and "version" in config_entry and "architectures" in config_entry:
                # valid config found
                for architecture in config_entry["architectures"].split(","):
                    distro = DISTROS[config_entry["name"]](architecture, config_entry["version"])
                    distros.append(distro)

        return distros

    def update_distro(self, distro_config_key: str, architectures: list[str]):
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
