import requests
import argparse
import json
from InquirerPy import inquirer
from links import ISOS

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
        print("no config file found, starting configurator")
        args.configure = True

    if args.configure:
        iso_choices = []
        if config:
            for iso in config:
                iso_choices.append(iso["name"])
        # add option to add new iso
        iso_choices.append("Add new ISO")
        for iso in ISOS:
            iso_choices.append(iso)
        iso_selected = inquirer.select(
            message="Choose an ISO to add",
            choices=iso_choices,
            multiselect=False,
        ).execute()
        if iso_selected == "Add new ISO":
            iso_selected = inquirer.select(
                message="Choose an ISO to add",
                choices=ISOS.keys(),
                multiselect=False,
            ).execute()
            # ask which architecture to add
            arch_choices = []
            for arch in ISOS[iso_selected]["links"]:
                arch_choices.append(arch)
            arch_selected = inquirer.select(
                message="Choose which architectures to add",
                choices=arch_choices,
                multiselect=True,
            ).execute()
            # add selected iso to config
            config.append(
                {
                    "name": iso_selected,
                    "arch": arch_selected,
                }
            )
            
        # configured iso selected
        else:
            
            
            
        for iso in iso_selected:
            print(f"Downloading {iso}")
            download_iso(ISOS[iso]["links"]["amd64"])


def download_iso(url):
    local_filename = url.split("/")[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


def write_config(config, path):
    with open(f"{path}/.{CONFIG_FILENAME}", "w") as f:
        f.write(json.dumps(config))


if __name__ == "__main__":
    main()
