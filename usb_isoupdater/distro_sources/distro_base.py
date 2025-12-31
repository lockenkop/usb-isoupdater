import hashlib
import logging
import os

import requests

from usb_isoupdater.progressbar import DownloadWithProgress

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
    architectures: list[str]

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
        r = requests.get(self.checksum_url, timeout=10)
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
        if self.filename in self.checksums:
            """Calculate the checksum of a file."""
            hash_func = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):  # Read file in chunks of 4096 bytes
                    hash_func.update(chunk)

            calculated_checksum = hash_func.hexdigest()
            logger.info(f"comparing {calculated_checksum} with {self.checksums[self.filename]}")
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
