import json
import logging
import re
from typing import ClassVar

import requests
from distro_sources.distro_base import Distro

logger = logging.getLogger(__name__)


DISTROS: dict[str, Distro] = {}


def distro_subclass(name):
    """Decorator to register a distro subclass dynamically."""

    def wrapper(cls):
        DISTROS[name] = cls
        return cls

    return wrapper


@distro_subclass("Ubuntu")
class Ubuntu(Distro):
    name: ClassVar[str] = "Ubuntu"
    config_key: ClassVar[str] = name.lower().replace(" ", "_")
    architecture: ClassVar[list[str]] = ["amd64", "arm64", "armel", "i386", "mips64el", "mipsel"]

    def __init__(self, architecture):
        super().__init__(architecture)
        self.version = self.get_release()
        download_url = "https://releases.ubuntu.com/{}/ubuntu-{}-desktop-{}.iso"
        checksum_url = "https://releases.ubuntu.com/{}/SHA256SUMS"
        filename = "ubuntu-{}-desktop-{}.iso"
        self.filename = filename.format(self.version, architecture)
        self.download_url = download_url.format(self.version, self.version, architecture)
        self.checksum_url = checksum_url.format(self.version)

    def get_release(self):
        """Get the latest release version of Ubuntu."""
        response = requests.get("https://api.launchpad.net/devel/ubuntu/series", timeout=10)
        ubuntu_series = json.loads(response.text)
        for entry in ubuntu_series["entries"]:
            if entry["status"] == "Current Stable Release":
                return entry["version"]


@distro_subclass("Arch Linux")
class Arch(Distro):
    name: ClassVar[str] = "Arch Linux"
    config_key: ClassVar[str] = name.lower().replace(" ", "_")
    download_url: ClassVar[str] = "https://geo.mirror.pkgbuild.com/iso/latest/archlinux-x86_64.iso"
    checksum_url: ClassVar[str] = "https://geo.mirror.pkgbuild.com/iso/latest/sha256sums.txt"
    architectures: ClassVar[list[str]] = ["x86_64"]

    def __init__(self, architecture):
        super().__init__(architecture)
        filename = "archlinux-{}.iso"
        self.filename = filename.format(architecture)


@distro_subclass("Arch Linux Test")
class ArchTest(Distro):
    name: ClassVar[str] = "Arch Linux Test"
    config_key: ClassVar[str] = name.lower().replace(" ", "_")
    download_url: ClassVar[str] = "https://geo.mirror.pkgbuild.com/iso/latest/archlinux-x86_64.iso"
    checksum_url: ClassVar[str] = "https://geo.mirror.pkgbuild.com/iso/latest/sha256sums.txt"
    architectures: ClassVar[list[str]] = ["x86_64"]

    def __init__(self, architecture):
        super().__init__(architecture)
        filename = "archlinux-{}.iso"
        self.filename = filename.format(architecture)

    def download(self, path="."):
        print("Testing Class, skipping download using present file")
        return f"archlinux-{self.arch}.iso"


@distro_subclass("Debian")
class Debian(Distro):
    name: ClassVar[str] = "Debian"
    config_key: ClassVar[str] = name.lower().replace(" ", "_")

    architectures: ClassVar[list[str]] = [
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

    def __init__(self, architecture, version):
        super().__init__(architecture, version)

        self.download_url = "https://cdimage.debian.org/debian-cd/current/{}/iso-cd/debian-{}-{}-netinst.iso"
        self.checksum_url = "https://cdimage.debian.org/debian-cd/current/{}/iso-cd/SHA256SUMS"
        filename = "debian-{}-{}-netinst.iso"

        if version == "latest":
            self.version = self.get_latest()
        else:
            self.version = version
        self.download_url = self.download_url.format(architecture, self.version, architecture)
        self.checksum_url = self.checksum_url.format(architecture)
        self.filename = filename.format(self.version, architecture)

    def get_latest(self) -> str:
        """Get the latest release version of Debian."""
        release_page = "/".join(self.download_url.split("/")[:-1]).format(self.arch)
        response = requests.get(release_page, timeout=10)
        version_pattern = r"debian-(\d+\.\d+\.\d+)-"
        version_matches = re.findall(version_pattern, response.text)
        if len(set(version_matches)) == 1:
            return version_matches[0]
        else:
            raise ValueError("Multiple versions found")


class PopOS(Distro):
    name = "PopOS"
    config_key = name.lower().replace(" ", "_")

    architectures = ["amd64"]

    def __init__(self, architecture):
        super().__init__(architecture)
        self.download_url = "https://system76.com/pop/download/"
        self.checksum_url = "https://system76.com/pop/download/"
        self.filename = ""
        self.download_url, checksum = self.get_download_url_and_checksum()
        self.filename = self.download_url.split("/")[-1]
        self.checksums = {self.filename: checksum}

    def get_download_url_and_checksum(self) -> tuple[str, str]:
        from bs4 import BeautifulSoup

        response = requests.get(self.download_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            download_button = soup.find("a", id="pop-download-0001c28b-4111-4add-b736-62d4797a12ce")
            sha256sum_textfield = soup.find("input", id="pop-hash-0001c28b-4111-4add-b736-62d4797a12ce")
            if sha256sum_textfield:
                sha256sum = sha256sum_textfield.get("value")
            else:
                logger.error(f"Failed to get sha256sum for {self.name}")
            if download_button:
                download_link = download_button.get("href")
            else:
                logger.error(f"Failed to get download link for {self.name}")
            if download_link and sha256sum:
                return str(download_link), str(sha256sum)
        raise ValueError(f"Failed to get download URL and checksum for {self.name}")
