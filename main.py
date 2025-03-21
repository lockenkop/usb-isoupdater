import requests
import argparse
import json
import re
import os
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from distros import distros

CONFIG_FILENAME = ".iso-usbupdater.config"


def main():
    parser = argparse.ArgumentParser(
        description="Manage and Update ISOs on removable Media"
    )
    parser.add_argument("path", help="Path to your mounted media")
    parser.add_argument(
        "-c", "--configure", help="Configure the updater", action="store_true"
    )
    args = parser.parse_args()
    config = {}
    # search the path for config file
    try:
        with open(f"{args.path}/{CONFIG_FILENAME}") as f:
            config = json.loads(f.read())
    except FileNotFoundError:
        print("no config file found")

    while args.configure:
        iso_choices = []
        if config:
            configured_isos = []
            iso_choices.append("Edit configured ISOs")
            for iso in config:
                configured_isos.append(iso)
        iso_choices.append("Add new ISO")
        iso_choices.append("Exit and Save")
        main_menu_selection = inquirer.select(
            message="Main Menu",
            choices=iso_choices,
            multiselect=False,
        ).execute()
        if main_menu_selection == "Add new ISO":
            os.system("clear")
            # ask which distro to add
            distro_selection = inquirer.select(
                message="Choose an ISO to add",
                # build a list of all available isos in distros.py
                choices=[
                    Choice(value=iso, name=iso.NAME) for iso in distros.DISTROLIST
                ],
                multiselect=False,
            ).execute()
            # ask which architecture to add
            arch_choices = [arch for arch in distro_selection.ARCHS]
            os.system("clear")
            arch_selected = inquirer.select(
                message="Choose which architectures to add",
                choices=arch_choices,
                multiselect=True,
            ).execute()
            # add selected iso to config
            config[distro_selection.NAME] = {
                "name": main_menu_selection,
                "archs": arch_selected,
            }
        # configured iso selected
        elif main_menu_selection == "Edit configured ISOs":
            os.system("clear")
            edit_iso_selection = inquirer.select(
                message="Choose an ISO to edit",
                choices=[iso for iso in config],
                multiselect=False,
            ).execute()
            if edit_iso_selection in ISOS:
                # ask what shall be done
                action_selected = inquirer.select(
                    message="What shall be done?",
                    choices=["Remove", "Edit Architectures"],
                    multiselect=False,
                ).execute()
                if action_selected == "Remove":
                    config.pop(edit_iso_selection)
                elif action_selected == "Edit Architectures":
                    arch_choices = []
                    for arch in ISOS[edit_iso_selection]["links"]:
                        arch_choices.append(arch)
                    os.system("clear")
                    arch_selected = inquirer.select(
                        message="Choose which architectures to add",
                        choices=arch_choices,
                        multiselect=True,
                    ).execute()
                    # add selected iso to config
                    config.update(
                        {
                            "name": edit_iso_selection,
                            "arch": arch_selected,
                        }
                    )

                else:
                    print("Invalid action")
            else:
                print("Invalid Option, ISO is not configured")
        elif main_menu_selection == "Exit and Save":
            write_config(config, args.path)
            args.configure = False
        else:
            print("Invalid Option")

    # download isos
    for iso in config:
        print(f"Downloading {iso}")
        for arch in config[iso]["archs"]:
            print(f"Downloading {iso} {arch}")
            download_iso(ISOS[iso]["links"][arch])


def download_checksums(sha256_url):
    r = requests.get(sha256_url)
    return r.text


def download_iso(url):
    local_filename = url.split("/")[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


def write_config(config, path):
    with open(f"{path}/{CONFIG_FILENAME}", "w") as f:
        f.write(json.dumps(config))


if __name__ == "__main__":
    main()
