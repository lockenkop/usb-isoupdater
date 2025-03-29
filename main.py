import argparse
import json
import os
import inspect
from typing import List
import logging
from config import CONFIG_FILENAME
from pathlib import Path
from config import ConfigManager
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import distros
from distros import Distro


SAMPLECONFIG = {
    "Arch Linux": ["amd64", "arm64"],
    "Debian": ["amd64", "arm64", "armel", "i386", "mips64el", "mipsel"],
    "Fedora": ["x86_64", "aarch64"],
}

MAIN_MENU_CHOICES = [
    "Add new ISO",
    "Download configured ISOs",
    "Exit and Save",
]
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Manage and Update ISOs on removable Media"
    )
    parser.add_argument("path", help="Path to your mounted media")
    parser.add_argument(
        "-c", "--configure", help="Configure the updater", action="store_true"
    )
    args = parser.parse_args()
    logging.basicConfig(filename="Isoupdater.log", level=logging.INFO)
    logging.info(f"starting with args: {args}")

    Isoupdater(args)


class Isoupdater:
    def __init__(self, args):
        self.path = Path(args.path)
        self.configure = args.configure
        self.config: ConfigManager = {}
        self.last_message = ""
        self.config_path = self.path.joinpath(CONFIG_FILENAME)
        self.distro_list = self.get_all_distros()

        # search the path for config file
        try:
            self.config = ConfigManager(self.config_path)
        except FileNotFoundError:
            logging.info(f"no config file found in {self.path}")

        if self.configure:
            logging.info("configure flag found, starting configuration")
            self.configure_flow()
        else:
            logging.info("no configure flag found, updating")
            self.update()

    def configure_flow(self):
        while self.configure:
            configured_distros = self.config.get_distros()
            main_menu_choices = MAIN_MENU_CHOICES.copy()
            if (
                self.config.get_distros()
                and "Edit configured ISOs" not in main_menu_choices
            ):
                main_menu_choices.insert(0, "Edit configured ISOs")
            os.system("clear")
            main_menu_selection = inquirer.select(
                message="Main Menu",
                instruction=self.last_message,
                choices=main_menu_choices,
                multiselect=False,
            ).execute()
            if main_menu_selection == "Add new ISO":
                os.system("clear")
                # ask which distro to add
                distro_choices = []
                for distro in self.distro_list:
                    if distro not in configured_distros:
                        distro_choices.append(Choice(value=distro, name=distro.name))
                self.distro_selection: Distro = inquirer.select(
                    message="Choose an ISO to add",
                    # build a list of all available isos in distros.py
                    choices=distro_choices,
                    multiselect=False,
                ).execute()
                # ask which architectures to add
                archs_selected = self.prompt_architecture_selection(
                    self.distro_selection
                )
                self.config.update_distro(
                    self.distro_selection.config_key, archs_selected
                )
            # configured iso selected
            elif main_menu_selection == "Edit configured ISOs":
                os.system("clear")
                edit_iso_choices = []
                for distro in self.config.get_distros():
                    distro_object = self.get_distro_by_key(distro)
                    edit_iso_choices.append(
                        Choice(value=distro_object, name=distro_object.name)
                    )
                self.edit_iso_selection: Distro = inquirer.select(
                    message="Choose an ISO to edit",
                    choices=edit_iso_choices,
                    multiselect=False,
                ).execute()

                # ask what shall be done
                action_selected = inquirer.select(
                    message="What shall be done?",
                    choices=["Remove", "Edit Architectures"],
                    multiselect=False,
                ).execute()
                if action_selected == "Remove":
                    self.config.remove_distro(self.edit_iso_selection.config_key)
                elif action_selected == "Edit Architectures":
                    archs_selected = self.prompt_architecture_selection(
                        self.edit_iso_selection
                    )
                    self.config.update_distro(
                        self.edit_iso_selection.config_key, archs_selected
                    )
                else:
                    print("Invalid action")

            elif main_menu_selection == "Download configured ISOs":
                self.download_isos()
            elif main_menu_selection == "Exit and Save":
                if self.config:
                    self.config.save_config()
                self.configure = False

            else:
                print("Invalid Option")

    def prompt_architecture_selection(self, distro: Distro) -> List[str]:
        os.system("clear")
        choices = []
        archs_configured = []
        configured_distros = self.config.get_distros()
        arch_choices = distro.architectures

        if distro.config_key in configured_distros:
            archs_configured = configured_distros[distro.config_key]
        for arch in arch_choices:
            choices.append(
                Choice(value=arch, name=arch, enabled=arch in archs_configured)
            )
        arch_selected = inquirer.select(
            message="Choose which architectures to add, spacebar to select multiple",
            choices=choices,
            multiselect=True,
        ).execute()
        return arch_selected

    def download_isos(self) -> None:
        # download isos
        if not self.config:
            logger.info("Download called with empty config")
            self.last_message = "no configuration"
        configured_distros = self.config.get_distros()
        for distro_config_key, configured_archs in configured_distros.items():
            distro = self.get_distro_by_key(distro_config_key)
            logger.info(f"checking {distro.name}")
            for arch in configured_archs:
                initialised_distro: Distro = distro(arch)
                if self.check_iso_present(initialised_distro):
                    if initialised_distro.verify_checksum(self.path):
                        logging.info(f"{initialised_distro.name} {arch} is up to date")
                        continue
                    else:
                        logging.info(
                            f"{initialised_distro.name} {arch} is old, redownloading"
                        )
                logger.info(f"Downloading {initialised_distro.name} {arch}")
                initialised_distro.download(self.path)
                logger.info(f"Verifying {initialised_distro.name} {arch}")
                if initialised_distro.verify_checksum(self.path):
                    logger.info(
                        f"{initialised_distro.name} {arch} downloaded successfully"
                    )
                    self.last_message = "download successfull"
                else:
                    logger.info(f"{distro.name} {arch} download failed")
                    self.last_message = "download failed"

    def check_iso_present(self, distro: Distro) -> bool:
        if distro.filename in os.listdir(self.path):
            logging.info(f"{distro.filename} is present")
            return True
        else:
            return False

    def get_all_distros(self) -> List[Distro]:
        """Returns a dictionary of all distro classes in distros.py."""
        return [
            cls
            for _, cls in inspect.getmembers(
                distros,
                lambda obj: inspect.isclass(obj)
                and issubclass(obj, Distro)
                and obj is not Distro,
            )
        ]

    def get_distro_by_key(self, key) -> Distro:
        for distro in self.distro_list:
            if key == distro.config_key:
                return distro
        raise ModuleNotFoundError

    def write_config(self) -> None:
        with open(self.config_path, "w") as f:
            f.write(json.dumps(self.config))


if __name__ == "__main__":
    main()
