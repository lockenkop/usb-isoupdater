import requests
import re


class distros:
    class Arch:
        NAME = "Arch Linux"
        OS = "linux"
        ARCHS = [
            "amd64",
            "arm64",
        ]

        def get_release():
            url = "https://archlinux.org/download/"
            r = requests.get(url)
            # regex for this Current Release:
            match = re.match(r"Current Release: (\d{4}.\d{2}.\d{2})", r.text)
            if match:
                release = match.group(1)
                return release
            else:
                return "No release found"

        def get_checksums(release):
            r = requests.get(f"https://archlinux.org/iso/{release}/sha256sums.txt")
            return r.text

        # "arch": {
        #         "name": "",
        #         "os": "linux",
        #         "link": "https://www.archlinux.org/download/",
        #         "checksums": "https://archlinux.org/iso/RELEASE/sha256sums.txt",
        #         "mirrorlist": "",
        #         "get_release":
        #     },

    class Debian:
        NAME = "Debian"
        OS = "linux"
        ARCHS = [
            "amd64",
            "arm64",
            "armel",
            "i386",
            "mips64el",
            "mipsel",
        ]

        def get_checksums(release):
            r = requests.get(
                f"https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/{release}.sha256"
            )
            return r.text

        def build_download_link(arch):
            return f"https://cdimage.debian.org/debian-cd/current/{arch}/iso-cd/"

        # "debian": {
        #         "name": "",
        #         "os": "linux",
        #         "link": "https://www.debian.org/distrib/",
        #         "checksums": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/SHA256SUMS",
        #         "mirrorlist": "",
        #         "get_releases": ""
        #     },

    DISTROLIST = [Arch(), Debian()]  # TODO there has to be a better way for this
