from track_fetcher import fetch_album_tracks, Track
from album_fetcher import fetch_album, Album
from downloader import M4ADownloader
from dataclasses import asdict
import json
import os

def input_int(prompt, default):
    try:
        value = input(f"{prompt}（默认: {default}）：").strip()
        return int(value) if value else default
    except ValueError:
        print("输入无效，使用默认值。")
        return default

if __name__ == '__main__':
    album_id = input_int("请输入专辑ID", 70278366)
    page = input_int("请输入起始页码", 1)
    page_size = 30

    tracks = fetch_album_tracks(album_id, page, page_size)
    if not tracks:
        print("未获取到曲目，请检查专辑ID或网络。")
        exit(1)

    album = fetch_album(album_id)
    album.tracks = tracks
    print(f"专辑：{album.albumTitle}，共{len(tracks)}条曲目")

    custom_dir = input("请输入下载目录（留空则默认 downloads/专辑名）：").strip()
    download_dir = custom_dir if custom_dir else None

    max_retries = input_int("最大重试次数", 3)
    retry_delay = input_int("重试间隔（秒）", 3)

    downloader = M4ADownloader(max_retries=max_retries, retry_delay=retry_delay)
    downloader.batch_download(tracks, album.albumTitle, download_dir)
