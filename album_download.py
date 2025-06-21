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

    def _get_progress_file(self):
        return os.path.join(self.save_dir, 'download_progress.json')

    def load_progress(self):
        import json
        progress_file = self._get_progress_file()
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_progress(self, progress):
        import json
        progress_file = self._get_progress_file()
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f'保存进度失败: {e}')

    def fetch_and_download_tracks(self):
        import json
        page = 1
        page_size = 20
        total_count = None
        downloaded_files = set(os.listdir(self.save_dir))
        idx = 1
        progress = self.load_progress()
        finished = False
        while not finished:
            page_key = str(page)
            if progress.get(page_key, {}).get('done'):
                self.log(f'第{page}页已全部完成，跳过')
                idx += page_size
                page += 1
                continue
            page_tracks = fetch_album_tracks(self.album_id, page, page_size)
            if not page_tracks:
                break
            if total_count is None and hasattr(page_tracks[0], 'totalCount'):
                total_count = page_tracks[0].totalCount
            self.log(f'已获取第{page}页曲目，共{idx-1+len(page_tracks)}/{total_count or "?"}条，开始下载本页...')
            page_progress = progress.get(page_key, {})
            if 'tracks' not in page_progress:
                page_progress['tracks'] = {}
            for i, track in enumerate(page_tracks):
                safe_title = re.sub(r'[\\/:*?"<>|]', '_', getattr(track, 'title', str(getattr(track, 'trackId', idx))))
                filename = f'{idx:03d}_{safe_title}.m4a'
                filepath = os.path.join(self.save_dir, filename)
                track_id = str(getattr(track, 'trackId', idx))
                track_status = page_progress['tracks'].get(track_id, {})
                if track_status.get('done'):
                    self.log(f'[{idx}/{total_count or "?"}] 已完成，跳过: {filename}')
                    idx += 1
                    continue
                if filename in downloaded_files and os.path.getsize(filepath) > 1024 * 10:
                    self.log(f'[{idx}/{total_count or "?"}] 已存在，跳过: {filename}')
                    page_progress['tracks'][track_id] = {'url': '', 'done': True, 'filename': filename}
                    self.save_progress(progress)
                    idx += 1
                    continue
                try:
                    crypted_url = fetch_track_crypted_url(getattr(track, 'trackId', None), self.album_id)
                except Exception as e:
                    self.log(f'[{idx}] 获取加密URL失败: {e}')
                    page_progress['tracks'][track_id] = {'url': '', 'done': False, 'error': str(e), 'filename': filename}
                    self.save_progress(progress)
                    idx += 1
                    continue
                if not crypted_url:
                    self.log(f'[{idx}] 无可用下载地址，跳过')
                    page_progress['tracks'][track_id] = {'url': '', 'done': False, 'error': '无可用下载地址', 'filename': filename}
                    self.save_progress(progress)
                    idx += 1
                    continue
                url = decrypt_url(crypted_url)
                page_progress['tracks'][track_id] = {'url': url, 'done': False, 'filename': filename}
                self.save_progress(progress)
                for attempt in range(3):
                    try:
                        self.log(f'[{idx}/{total_count or "?"}] 下载: {filename} (第{attempt+1}次尝试)')
                        self.downloader.download_m4a(url, filepath)
                        self.log(f'[{idx}] 下载完成: {filename}')
                        page_progress['tracks'][track_id]['done'] = True
                        self.save_progress(progress)
                        break
                    except Exception as e:
                        self.log(f'[{idx}] 下载失败: {e}')
                        page_progress['tracks'][track_id]['error'] = str(e)
                        self.save_progress(progress)
                        if attempt == 2:
                            self.log(f'[{idx}] 多次失败，跳过: {filename}')
                idx += 1
            all_done = all(t.get('done') for t in page_progress['tracks'].values()) and len(page_progress['tracks']) == len(page_tracks)
            if all_done:
                page_progress['done'] = True
            progress[page_key] = page_progress
            self.save_progress(progress)
            # 判断是否达到总数
            if total_count and idx > total_count:
                finished = True
            elif not page_tracks or len(page_tracks) == 0:
                finished = True
            else:
                page += 1
        self.log('专辑下载完成')

    def download_album(self):
        if not self.fetch_album_info():
            return
        self.log('开始下载专辑音频...')
        self.fetch_and_download_tracks()


# 兼容原有函数式调用
def album_download(album_id, log_func=print):
    AlbumDownloader(album_id, log_func).download_album()
