import requests
import hashlib
from typing import List, Dict
from tqdm import tqdm
import re
import os
import json
from urllib.request import urlretrieve
from custom_progressbar import DownloadWithProgress

import logging

logger = logging.getLogger(__name__)

VALID_ARCHITECTURES = [
    "amd64",
    "arm64",
    "i386",
    "x86_64",
    "aarch64",
    "armel",
    "mips64el",
    "mipsel",
    "ppc64el",
    "s390x",
]


class Distro:
    """Base class for a Linux distribution."""

    name = ""
    config_key = name.lower().replace(" ", "_")
    download_url = ""
    checksum_url = ""
    filename = ""
    architectures: List[str] = []

    def __init__(self, architecture):
        if architecture not in self.architectures:
            raise NotImplementedError
        self.arch = architecture
        self.checksums = {}

    def download(self, path):
        """Download the ISO file."""
        filepath = os.path.join(path, self.filename)
        downloader = DownloadWithProgress(self.download_url, filepath)
        downloader.download()

    def get_checksums(self):
        r = requests.get(self.checksum_url)
        lines = r.text.strip().split("\n")
        for line in lines:
            checksum, checksum_filename = line.split()
            self.checksums[checksum_filename.replace("*", "")] = checksum
            # Ubuntu has a * prefix in their SHA256SUMS file

    def verify_checksum(self, path):
        """Calculate and verify the checksum of the downloaded ISO."""
        if not self.checksums:
            logger.info("getting checksums")
            self.get_checksums()
        logger.info(f"verifying checksum for {self.filename}")
        filepath = os.path.join(path, self.filename)
        if self.filename in self.checksums.keys():
            """Calculate the checksum of a file."""
            hash_func = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(
                    lambda: f.read(4096), b""
                ):  # Read file in chunks of 4096 bytes
                    hash_func.update(chunk)

            calculated_checksum = hash_func.hexdigest()
            logger.info(
                f"comparing {calculated_checksum} with {self.checksums[self.filename]}"
            )
            expected_checksum = self.checksums[self.filename]
            if calculated_checksum == expected_checksum:
                logger.info("checksum correct")
                return True
            else:
                logger.info("checksum incorrect")
                return False
        logger.info(f"{self.filename} not found in checksums")
        logger.info(self.checksums)
        raise FileNotFoundError


DISTROS: Dict[str, Distro] = {}


def distro_subclass(name):
    """Decorator to register a distro subclass dynamically."""

    def wrapper(cls):
        DISTROS[name] = cls
        return cls

    return wrapper


@distro_subclass("Ubuntu")
class Ubuntu(Distro):
    name = "Ubuntu"
    config_key = name.lower().replace(" ", "_")
    download_url = "https://releases.ubuntu.com/{}/ubuntu-{}-desktop-{}.iso"
    checksum_url = "https://releases.ubuntu.com/{}/SHA256SUMS"
    filename = "ubuntu-{}-desktop-{}.iso"
    architectures = ["amd64", "arm64", "armel", "i386", "mips64el", "mipsel"]

    def __init__(self, architecture):
        super().__init__(architecture)
        self.version = self.get_release()
        self.filename = self.filename.format(self.version, architecture)
        self.download_url = self.download_url.format(
            self.version, self.version, architecture
        )
        self.checksum_url = self.checksum_url.format(self.version)

    def get_release(self):
        """Get the latest release version of Ubuntu."""
        response = requests.get("https://api.launchpad.net/devel/ubuntu/series")
        ubuntu_series = json.loads(response.text)
        for entry in ubuntu_series["entries"]:
            if entry["status"] == "Current Stable Release":
                return entry["version"]


@distro_subclass("Arch Linux")
class Arch(Distro):
    name = "Arch Linux"
    config_key = name.lower().replace(" ", "_")
    download_url = "https://geo.mirror.pkgbuild.com/iso/latest/archlinux-x86_64.iso"
    checksum_url = "https://geo.mirror.pkgbuild.com/iso/latest/sha256sums.txt"
    filename = "archlinux-{}.iso"
    architectures = ["x86_64"]

    def __init__(self, architecture):
        super().__init__(architecture)
        self.filename = self.filename.format(architecture)


@distro_subclass("Arch Linux Test")
class ArchTest(Distro):
    name = "Arch Linux Test"
    config_key = name.lower().replace(" ", "_")
    download_url = "https://geo.mirror.pkgbuild.com/iso/latest/archlinux-x86_64.iso"
    checksum_url = "https://geo.mirror.pkgbuild.com/iso/latest/sha256sums.txt"
    filename = "archlinux-{}.iso"
    architectures = ["x86_64"]

    def __init__(self, architecture):
        super().__init__(architecture)
        self.filename = self.filename.format(architecture)

    def download(self, path="."):
        print("Testing Class, skipping download using present file")
        return f"archlinux-{self.arch}.iso"


@distro_subclass("Debian")
class Debian(Distro):
    name = "Debian"
    config_key = name.lower().replace(" ", "_")
    download_url = "https://cdimage.debian.org/debian-cd/current/{}/iso-cd/debian-{}-{}-netinst.iso"
    checksum_url = "https://cdimage.debian.org/debian-cd/current/{}/iso-cd/SHA256SUMS"
    filename = "debian-{}-{}-netinst.iso"
    architectures = [
        "amd64",
        "arm64",
        "armel",
        "armhf",
        "i386",
        "mips64el",
        "mipsel",
        "ppc64el",
        "s390x",
    ]

    def __init__(self, architecture):
        super().__init__(architecture)
        self.version = self.get_release()
        self.filename = self.filename.format(self.version, architecture)
        self.download_url = self.download_url.format(
            architecture, self.version, architecture
        )
        self.checksum_url = self.checksum_url.format(architecture)

    def get_release(self):
        """Get the latest release version of Debian."""
        realese_page = "/".join(self.download_url.split("/")[:-1]).format(self.arch)
        response = requests.get(realese_page)
        version_pattern = r"debian-(\d+\.\d+\.\d+)-"
        version_matches = re.findall(version_pattern, response.text)
        if len(set(version_matches)) == 1:
            return version_matches[0]
        else:
            raise ValueError("Multiple versions found")


class PopOS(Distro):
    name = "PopOS"
    config_key = name.lower().replace(" ", "_")
    download_url = "https://system76.com/pop/download/"
    checksum_url = "https://system76.com/pop/download/"
    filename = ""
    architectures = ["amd64"]

    def __init__(self, architecture):
        super().__init__(architecture)
        self.download_url, checksum = self.get_download_url_and_checksum()
        self.filename = self.download_url.split("/")[-1]
        self.checksums = {self.filename: checksum}

    def get_download_url_and_checksum(self):
        from bs4 import BeautifulSoup

        response = requests.get(self.download_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            download_button = soup.find(
                "a", id="pop-download-0001c28b-4111-4add-b736-62d4797a12ce"
            )
            sha256sum_textfield = soup.find(
                "input", id="pop-hash-0001c28b-4111-4add-b736-62d4797a12ce"
            )
            if sha256sum_textfield:
                sha256sum = sha256sum_textfield.get("value")
            else:
                logger.error(f"Failed to get sha256sum for {self.name}")
            if download_button:
                download_link = download_button.get("href")
            else:
                logger.error(f"Failed to get download link for {self.name}")
            if download_link and sha256sum:
                return download_link, sha256sum
            else:
                return False
