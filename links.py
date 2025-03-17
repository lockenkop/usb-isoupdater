# Template
NAME_VARIANT = {
    "name": "",
    "os": "",
    "links": {
        "amd64": "",
        "arm64": "",
        "armel": "",
        "i386": "",
        "mips64el": "",
        "mipsel": "",
    },
    "mirrorlist": "",
}


ISOS = {
    "debian": {
        "name": "Debian",
        "os": "linux",
        "links": {
            "amd64": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/",
            "arm64": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/",
            "armel": "https://cdimage.debian.org/debian-cd/current/armel/iso-cd/",
            "i386": "https://cdimage.debian.org/debian-cd/current/i386/iso-cd/",
            "mips64el": "https://cdimage.debian.org/debian-cd/current/mips64el/iso-cd/",
            "mipsel": "https://cdimage.debian.org/debian-cd/current/mipsel/iso-cd/",
        },
        "mirrorlist": "https://www.debian.org/CD/http-ftp/#mirror",
    },
    "ubuntu_desktop": {
        "name": "Ubuntu",
        "variant": "Desktop",
        "os": "linux",
        "links": {
            "amd64": "https://www.ubuntu.com/download",
            # TODO Fixed-Release distros need other handling than rolling release distros
        },
        "mirrorlist": "",
    },
    # UBUNTU_SERVER = {
    #     "name": "Ubuntu",
    #     "os": "linux",
    #     "links": {
    #         "amd64": "https://ubuntu.com/download/desktop/thank-you?version=24.04.2&architecture=amd64&lts=true",
    #     },
    #     "mirrorlist": "",
    # }
    "manjaro": {
        "name": "",
        "os": "linux",
        "link": "https://manjaro.org/download/",
        "mirrorlist": "",
    },
    "mint": {
        "name": "",
        "os": "linux",
        "link": "https://linuxmint.com/download.php",
        "mirrorlist": "",
    },
    "arch": {
        "name": "",
        "os": "linux",
        "link": "https://www.archlinux.org/download/",
        "mirrorlist": "",
    },
    "fedora_workstation": {
        "name": "",
        "os": "linux",
        "link": "https://getfedora.org/en/workstation/download",
        "mirrorlist": "",
    },
    "fedora_server": {
        "name": "",
        "os": "linux",
        "link": "https://getfedora.org/en/server/download",
        "mirrorlist": "",
    },
    "centos": {
        "name": "",
        "os": "linux",
        "link": "https://www.centos.org/download/",
        "mirrorlist": "",
    },
    "opensuse": {
        "name": "",
        "os": "linux",
        "link": "https://software.opensuse.org/",
        "mirrorlist": "",
    },
    "redhat": {
        "name": "",
        "os": "linux",
        "link": "https://www.redhat.com/en/store",
        "mirrorlist": "",
    },
    "gentoo": {
        "name": "",
        "os": "linux",
        "link": "https://www.gentoo.org/downloads/",
        "mirrorlist": "",
    },
    "raspbian": {
        "name": "",
        "os": "linux",
        "link": "https://www.raspberrypi.org/downloads/raspbian/",
        "mirrorlist": "",
    },
    # "https://admin.fedoraproject.org/mirrorlistmanager/">Fedora ISO Mirrorlist
    # "https://www.centos.org/download/mirrorlists/">CentOS Mirrorlist
    # "https://www.archlinux.org/releng/releases/">Arch Linux Mirrorlist
}
