import urllib.request
from tqdm import tqdm


class DownloadWithProgress:
    def __init__(self, url, filepath):
        self.url = url
        self.filepath = filepath
        self.progress_bar = None

    def download_progress_hook(self, block_num, block_size, total_size):
        """Custom reporthook for tracking download progress."""
        downloaded = block_num * block_size
        if total_size > 0:
            # Update progress bar based on the downloaded size
            self.progress_bar.update(downloaded - self.progress_bar.n)

        if downloaded >= total_size:
            self.progress_bar.close()

    def download(self):
        """Method to download a file with a progress bar."""
        with urllib.request.urlopen(self.url) as response:
            total_size = response.length
            self.progress_bar = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=self.filepath.split("/")[-1],
            )

            # Use urlretrieve with the custom progress hook
            urllib.request.urlretrieve(
                self.url, self.filepath, reporthook=self.download_progress_hook
            )
