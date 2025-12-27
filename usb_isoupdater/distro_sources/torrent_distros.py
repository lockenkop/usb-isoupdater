import feedparser
import requests
from bs4 import BeautifulSoup
from distro_base import Distro


class TorrentDistro(Distro):
    def __init__(self, name: str, torrent_url: str, arch):
        self.name = name
        self.torrent_url = torrent_url
        self.filename = torrent_url.split("/")[-1].split(".torrent")[0]
        self.architecture = arch

    def download(self):
        # Implement download logic here
        pass


def get_distros_from_distrowatch() -> list[TorrentDistro]:
    """
    Fetches the list of Linux distributions from Distrowatch and returns a list of TorrentDistro objects.
    """
    url = "https://distrowatch.com/dwres.php?resource=bittorrent"
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0"},
    )
    response.raise_for_status()  # Raise an error for bad responses
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"style": "width:100%; padding: 5px"})
    rows = table.find_all("tr")[1:]  # Skip the header row

    distros = [
        TorrentDistro(
            row.contents[0].contents[0].contents[2],
            row.contents[1].contents[0].attrs["href"],
        )
        for row in rows
    ]

    return distros


def get_distros_from_fosstorrents() -> list[TorrentDistro]:
    """
    Fetches the list of Linux distributions from Fosstorrents and returns a list of TorrentDistro objects.
    """
    url = "https://fosstorrents.com/feed/torrents.xml"
    feed = feedparser.parse(url)
    distros = []
    for entry in feed.entries:
        name = entry.title
        torrent_url = entry.link
        arch = entry.title.split("(")[-1][:-1]
        distros.append(TorrentDistro(name, torrent_url, arch))
    return distros


def main():
    distros = []
    distros = get_distros_from_fosstorrents()
    for distro in distros:
        print(f"Name: {distro.name}, Link: {distro.torrent_url}")


if __name__ == "__main__":
    main()
