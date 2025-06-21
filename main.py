from fetcher.track_fetcher import fetch_album_tracks, Track
from fetcher.album_fetcher import fetch_album, Album
from downloader.downloader import M4ADownloader
from dataclasses import asdict
import tkinter as tk
from gui.gui import XimalayaGUI
import os, sys

def main():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.getcwd()
    default_download_dir = os.path.join(base_dir, 'AudioBook')
    if not os.path.exists(default_download_dir):
        os.makedirs(default_download_dir, exist_ok=True)
    root = tk.Tk()
    app = XimalayaGUI(root, default_download_dir=default_download_dir)
    root.mainloop()

if __name__ == '__main__':
    main()