from fetcher.track_fetcher import fetch_album_tracks, Track
from fetcher.album_fetcher import fetch_album, Album
from downloader.downloader import M4ADownloader
from dataclasses import asdict


def main():
    import tkinter as tk
    from gui.gui import XimalayaGUI
    root = tk.Tk()
    app = XimalayaGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()