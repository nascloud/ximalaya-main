import os
import re
from album_fetcher import fetch_album
from track_fetcher import fetch_album_tracks, fetch_track_crypted_url
from downloader import M4ADownloader
from utils import decrypt_url


class AlbumDownloader:
    def __init__(self, album_id, log_func=print):
        self.album_id = int(album_id)
        self.log = log_func
        self.album = None
        self.tracks = []
        self.save_dir = None
        self.downloader = M4ADownloader()

    def fetch_album_info(self):
        self.album = fetch_album(self.album_id)
        if not self.album:
            self.log('获取专辑信息失败')
            return False
        self.save_dir = os.path.join('downloads', self.album.albumTitle)
        os.makedirs(self.save_dir, exist_ok=True)
        self.log(f'专辑：{self.album.albumTitle}，准备下载...')
        return True

    def fetch_tracks(self):
        self.tracks = []
        page = 1
        page_size = 20
        total_count = None
        while True:
            page_tracks = fetch_album_tracks(self.album_id, page, page_size)
            if not page_tracks:
                break
            if total_count is None and hasattr(page_tracks[0], 'totalCount'):
                total_count = page_tracks[0].totalCount
            self.tracks.extend(page_tracks)
            self.log(f'已获取第{page}页曲目，共{len(self.tracks)}/{total_count or "?"}条')
            if len(page_tracks) < page_size:
                break
            page += 1
        if not self.tracks:
            self.log('未获取到曲目')
            return False
        return True

    def download_tracks(self):
        downloaded_files = set(os.listdir(self.save_dir))
        for idx, track in enumerate(self.tracks, 1):
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', getattr(track, 'title', str(getattr(track, 'trackId', idx))))
            filename = f'{idx:03d}_{safe_title}.m4a'
            filepath = os.path.join(self.save_dir, filename)
            if filename in downloaded_files and os.path.getsize(filepath) > 1024 * 10:
                self.log(f'[{idx}/{len(self.tracks)}] 已存在，跳过: {filename}')
                continue
            try:
                crypted_url = fetch_track_crypted_url(getattr(track, 'trackId', None), self.album_id)
            except Exception as e:
                self.log(f'[{idx}] 获取加密URL失败: {e}')
                continue
            if not crypted_url:
                self.log(f'[{idx}] 无可用下载地址，跳过')
                continue
            url = decrypt_url(crypted_url)
            for attempt in range(3):
                try:
                    self.log(f'[{idx}/{len(self.tracks)}] 下载: {filename} (第{attempt+1}次尝试)')
                    self.downloader.download_m4a(url, filepath)
                    self.log(f'[{idx}] 下载完成: {filename}')
                    break
                except Exception as e:
                    self.log(f'[{idx}] 下载失败: {e}')
                    if attempt == 2:
                        self.log(f'[{idx}] 多次失败，跳过: {filename}')
        self.log('专辑下载完成')

    def download_album(self):
        if not self.fetch_album_info():
            return
        if not self.fetch_tracks():
            return
        self.log(f'共{len(self.tracks)}条曲目，开始下载...')
        self.download_tracks()


# 兼容原有函数式调用
def album_download(album_id, log_func=print):
    AlbumDownloader(album_id, log_func).download_album()
