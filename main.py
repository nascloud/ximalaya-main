from track_fetcher import fetch_album_tracks, Track
from album_fetcher import fetch_album, Album
from downloader import download_m4a, batch_download
from dataclasses import asdict
import json
import os

if __name__ == '__main__':
    album_id = 70278366
    page = 1
    page_size = 10
    tracks = fetch_album_tracks(album_id, page, page_size)
    track_dicts = [asdict(track) for track in tracks]
    # print(json.dumps(track_dicts))
    album = fetch_album(album_id)
    album.tracks = tracks
    print(album)

    # 下载目录可自定义，默认在 downloads/专辑名/
    # 你也可以自定义目录，例如：download_dir = r"D:\MyMusic\"
    download_dir = None  # 或自定义路径
    batch_download(tracks, album.albumTitle, download_dir)
