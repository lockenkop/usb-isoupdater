import argparse
import inspect
import logging
import os
import typing
from pathlib import Path

import psutil
import pyudev
from distro_sources import http_distros
from distro_sources.distro_base import Distro
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from usb_isoupdater.config import CONFIG_FILENAME, ConfigManager

if typing.TYPE_CHECKING:
    from psutil._common import sdiskpart

SAMPLECONFIG = {
    "Arch Linux": ["amd64", "arm64"],
    "Debian": ["amd64", "arm64", "armel", "i386", "mips64el", "mipsel"],
    "Fedora": ["x86_64", "aarch64"],
}

logging.basicConfig(
    filename="Isoupdater.log",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Manage and Update ISOs on removable Media")
    parser.add_argument("path", help="Path to your mounted media")
    parser.add_argument("-c", "--configure", help="Configure the updater", action="store_true")
    args = parser.parse_args()
    logging.info(f"starting with args: {args}")

    Isoupdater(args)


class Isoupdater:
    def __init__(self, args):
        self.path = Path(args.path)
        self.configure = args.configure
        self.config: ConfigManager
        self.last_message = ""
        self.usb_device: pyudev.Device | None = None
        self.configured_usb_device: dict[str, str] | None = None
        self.config_path = self.path.joinpath(CONFIG_FILENAME)
        self.distro_list = self._get_all_distros()
        # TODO add keybindings support for going back
        self.keybindings = {
            "Back": [{"key": "escape"}],
        }

        self.MAIN_MENU_CHOICES = {
            "Edit configured ISOs": self.prompt_edit_iso,
            "Add new ISO, HTTP": self.prompt_add_iso,
            "Add new ISO, Torrent": self.prompt_add_iso,
            "Download configured ISOs": self.action_download_isos,
            "Configure Storage Device": self.prompt_select_usb,
            "Exit and Save": self.action_exit_and_save,
        }

        # search the path for config file
        try:
            self.config = ConfigManager(self.config_path)
        except FileNotFoundError:
            logging.info(f"no config file found in {self.path}")
        self.configured_usb_device = self.config.get_usb_device()
        if self.configured_usb_device:
            self.connected_usb_device = self._find_configured_usb_device()
            if self.connected_usb_device:
                self.last_message = "configured USB device found"
            else:
                self.last_message = "configured USB device not connected"
        else:
            self.last_message = "no USB device configured"

        if self.configure:
            logging.info("configure flag found, starting configuration")
            self.configure_flow()
        else:
            logging.info("no configure flag found, updating")
            self.update()

    def configure_flow(self):
        while self.configure:
            self.configured_distros = self.config.get_distros()
            main_menu_choices = list(self.MAIN_MENU_CHOICES.keys())
            if not self.config.get_distros():
                main_menu_choices.remove("Edit configured ISOs")
            os.system("clear")
            main_menu_selection = inquirer.select(  # pyright: ignore[reportPrivateImportUsage]
                message="Main Menu",
                instruction=self.last_message,
                choices=main_menu_choices,
                multiselect=False,
            ).execute()
            self.MAIN_MENU_CHOICES[main_menu_selection]()

    def prompt_select_usb(self):
        os.system("clear")
        # select storage device
        usb_devices_psutil = self._get_usb_devices_psutil()
        usb_devices_udev = self._get_usb_devices_udev()
        usb_choices = []
        for device in usb_devices_psutil:
            usb_choices.append(Choice(value=device.device, name=f"{device.device}, mounted at: {device.mountpoint}"))
        usb_choices.append(Choice(value="Back", name="Back"))
        usb_device_choice = inquirer.select(  # pyright: ignore[reportPrivateImportUsage]
            message="Select your USB device",
            choices=usb_choices,
        ).execute()
        if usb_device_choice == "Back":
            return
        # find the udev device with the same device node
        for dev in usb_devices_udev:
            if dev.device_node == usb_device_choice:
                udev_device = dev
                break

        self.config.update_usb_device(udev_device)

    def prompt_add_iso(self):
        os.system("clear")
        # ask which distro to add
        distro_choices = []
        for distro in self.distro_list:
            if distro.config_key not in self.configured_distros:
                distro_choices.append(Choice(value=distro, name=distro.name))
        if not distro_choices:
            self.last_message = "All available ISOs are already configured"
            return
        distro_choices.append(Choice(value="Back", name="Back"))
        self.distro_selection: Distro = inquirer.select(  # pyright: ignore[reportPrivateImportUsage]
            message="Choose an ISO to add",
            # build a list of all available isos in distros.py
            choices=distro_choices,
            multiselect=False,
        ).execute()
        if self.distro_selection == "Back":
            return
        # ask which architectures to add
        archs_selected = self.prompt_architecture_selection(self.distro_selection)
        self.config.update_distro(self.distro_selection.config_key, archs_selected)

    def prompt_edit_iso(self):
        os.system("clear")
        edit_iso_choices = []
        for distro in self.config.get_distros():
            distro_object = self._get_distro_by_key(distro)
            edit_iso_choices.append(Choice(value=distro_object, name=distro_object.name))
        edit_iso_choices.append(Choice(value="Back", name="Back"))
        self.edit_iso_selection: Distro = inquirer.select(  # pyright: ignore[reportPrivateImportUsage]
            message="Choose an ISO to edit",
            choices=edit_iso_choices,
            multiselect=False,
        ).execute()
        if self.edit_iso_selection == "Back":
            return
        # ask what shall be done
        action_selected = inquirer.select(  # pyright: ignore[reportPrivateImportUsage]
            message="What shall be done?",
            choices=["Remove", "Edit Architectures", "Back"],
            multiselect=False,
        ).execute()
        if action_selected == "Remove":
            self.config.remove_distro(self.edit_iso_selection.config_key)
        elif action_selected == "Edit Architectures":
            archs_selected = self.prompt_architecture_selection(self.edit_iso_selection)
            self.config.update_distro(self.edit_iso_selection.config_key, archs_selected)
        elif action_selected == "Back":
            self.prompt_edit_iso()
        else:
            print("Invalid action")

    def action_exit_and_save(self):
        os.system("clear")
        self.config.save_config()
        logger.info("Exiting and saving configuration")
        exit(0)

    def prompt_architecture_selection(self, distro: Distro) -> list[str]:
        os.system("clear")
        choices = []
        archs_configured = []
        configured_distros = self.config.get_distros()
        arch_choices = distro.architectures

        if distro.config_key in configured_distros:
            archs_configured = configured_distros[distro.config_key]
        for arch in arch_choices:
            choices.append(Choice(value=arch, name=arch, enabled=arch in archs_configured))
        arch_selected = inquirer.select(  # pyright: ignore[reportPrivateImportUsage]
            message="Choose which architectures to add, spacebar to select multiple, enter to confirm",
            choices=choices,
            multiselect=True,
        ).execute()
        return arch_selected

    def action_download_isos(self) -> None:
        # download isos
        if not self.config:
            logger.info("Download called with empty config")
            self.last_message = "no configuration"
        configured_distros = self.config.get_distros()
        for distro_config_key, configured_architectures in configured_distros.items():
            distro = self._get_distro_by_key(distro_config_key)
            logger.info(f"Checking {distro.name}")
            for arch in configured_architectures:
                initialised_distro: Distro = distro(arch)
                if self._check_iso_present(initialised_distro):
                    if initialised_distro.verify_checksum(self.path):
                        logging.info(f"{initialised_distro.name} {arch} is up to date")
                        continue
                    else:
                        logging.info(f"{initialised_distro.name} {arch} is old, redownloading")
                logger.info(f"Downloading {initialised_distro.name} {arch}")
                initialised_distro.download(self.path)
                logger.info(f"Verifying {initialised_distro.name} {arch}")
                if initialised_distro.verify_checksum(self.path):
                    logger.info(f"{initialised_distro.name} {arch} downloaded successfully")
                    self.last_message = "download successfull"
                else:
                    logger.info(f"{distro.name} {arch} download failed")
                    self.last_message = "download failed"

    def update(self):
        pass

    def _get_usb_devices_udev(self) -> list[pyudev.Device]:
        """Returns a list of mounted USB devices"""
        usb_devices = []
        context = pyudev.Context()
        for device in context.list_devices(subsystem="block", DEVTYPE="partition"):
            if device.get("ID_BUS") == "usb" and device.get("ID_FS_TYPE") is not None:
                logging.info(f"Found USB device: {device.device_node}")
                usb_devices.append(device)
        return usb_devices

    def _get_usb_devices_psutil(self) -> list["sdiskpart"]:
        return psutil.disk_partitions()

    def _find_configured_usb_device(self) -> pyudev.Device | None:
        usb_devices = self._get_usb_devices_udev()
        for device in usb_devices:
            if (
                # devicepath can change, so we check only vendor and model id
                # device.device_node == self.configured_usb_device["devicepath"]
                device.get("ID_VENDOR_ID") == self.configured_usb_device["vendorid"]
                and device.get("ID_MODEL_ID") == self.configured_usb_device["modelid"]
            ):
                logging.info(f"Configured USB device found: {device.device_node}")
                return device

        logging.warning("Configured USB device not found")
        self.last_message = "Configured USB device not found"
        return None

    def _check_iso_present(self, distro: Distro) -> bool:
        if distro.filename in os.listdir(self.path):
            logging.info(f"{distro.filename} is present")
            return True
        else:
            return False

    def _get_all_distros(self) -> list[Distro]:
        """Returns a dictionary of all distro classes in distros.py."""
        return [
            cls
            for _, cls in inspect.getmembers(
                http_distros,
                lambda obj: inspect.isclass(obj) and issubclass(obj, Distro) and obj is not Distro,
            )
        ]

    def _get_distro_by_key(self, key) -> Distro:
        for distro in self.distro_list:
            if key == distro.config_key:
                return distro
        raise ModuleNotFoundError


if __name__ == "__main__":
    main()
