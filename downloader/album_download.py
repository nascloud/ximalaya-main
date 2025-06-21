import os
import re
import time
from fetcher.album_fetcher import fetch_album
from fetcher.track_fetcher import fetch_album_tracks
from downloader.downloader import M4ADownloader
from utils.utils import decrypt_url


class AlbumDownloader:
    def __init__(self, album_id, log_func=print, delay=0, save_dir=None):
        self.album_id = int(album_id)
        self.log = log_func
        self.album = None
        self.tracks = []
        self.save_dir = save_dir  # 支持外部传递下载目录
        self.downloader = M4ADownloader()
        self.delay = delay  # 下载延迟（秒）

    def fetch_album_info(self):
        self.album = fetch_album(self.album_id)
        if not self.album:
            self.log('获取专辑信息失败')
            return False
        # 过滤专辑名中的非法字符
        safe_album_title = re.sub(r'[\\/:*?"<>|]', '_', self.album.albumTitle)
        if self.save_dir:
            self.save_dir = os.path.join(self.save_dir, safe_album_title)
        else:
            self.save_dir = os.path.join('downloads', safe_album_title)
        os.makedirs(self.save_dir, exist_ok=True)
        self.log(f'专辑：{self.album.albumTitle}，准备下载...')
        return True

    def save_album_info(self):
        """保存专辑封面和专辑信息到下载目录，并生成可读的 markdown 文件"""
        import json
        import requests
        import re
        from html import unescape
        # 只保存 Album 数据类已有字段
        album_info = {
            'albumId': getattr(self.album, 'albumId', None),
            'albumTitle': getattr(self.album, 'albumTitle', ''),
            'cover': getattr(self.album, 'cover', ''),
            'createDate': getattr(self.album, 'createDate', ''),
            'updateDate': getattr(self.album, 'updateDate', ''),
            'richIntro': getattr(self.album, 'richIntro', ''),
            'tracks': getattr(self.album, 'tracks', []),
        }
        info_path = os.path.join(self.save_dir, 'album_info.json')
        try:
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(album_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f'保存专辑信息失败: {e}')
        # 美化 richIntro 内容，转换为 Markdown
        def html_to_markdown(html):
            html = unescape(html)
            html = re.sub(r'<p[^>]*>', '\n', html)  # 段落换行
            html = re.sub(r'</p>', '\n', html)
            html = re.sub(r'<br\s*/?>', '\n', html)
            html = re.sub(r'<span[^>]*>', '', html)
            html = re.sub(r'</span>', '', html)
            html = re.sub(r'<b[^>]*>', '**', html)
            html = re.sub(r'</b>', '**', html)
            html = re.sub(r'<strong[^>]*>', '**', html)
            html = re.sub(r'</strong>', '**', html)
            html = re.sub(r'<i[^>]*>', '*', html)
            html = re.sub(r'</i>', '*', html)
            html = re.sub(r'<[^>]+>', '', html)  # 去除其他标签
            html = re.sub(r'\n+', '\n', html)  # 合并多余换行
            return html.strip()
        rich_intro_md = html_to_markdown(album_info['richIntro'])
        # 保存专辑信息（markdown）
        md_path = os.path.join(self.save_dir, 'album_info.md')
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {album_info['albumTitle']}\n\n")
                if album_info['cover']:
                    f.write(f"![cover]({album_info['cover']})\n\n")
                f.write(f"**专辑ID**: {album_info['albumId']}  \n")
                f.write(f"**创建时间**: {album_info['createDate']}  \n")
                f.write(f"**更新时间**: {album_info['updateDate']}  \n\n")
                f.write(f"## 简介\n{rich_intro_md}\n")
        except Exception as e:
            self.log(f'保存专辑markdown信息失败: {e}')
        # 下载封面图片
        cover_url = getattr(self.album, 'cover', None)
        if cover_url:
            try:
                resp = requests.get(cover_url, timeout=10)
                if resp.status_code == 200:
                    with open(os.path.join(self.save_dir, 'cover.jpg'), 'wb') as f:
                        f.write(resp.content)
                else:
                    self.log(f'封面下载失败，状态码: {resp.status_code}')
            except Exception as e:
                self.log(f'下载封面失败: {e}')

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
        import tempfile
        progress_file = self._get_progress_file()
        try:
            # 使用临时文件+fsync确保写入磁盘
            dir_name = os.path.dirname(progress_file)
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=dir_name, delete=False) as tf:
                json.dump(progress, tf, ensure_ascii=False, indent=2)
                tf.flush()
                os.fsync(tf.fileno())
                tmp_file = tf.name
            os.replace(tmp_file, progress_file)
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
                # 直接传递track_id、album_id、filename给downloader
                for attempt in range(3):
                    try:
                        self.log(f'[{idx}/{total_count or "?"}] 下载: {filename} (第{attempt+1}次尝试)')
                        self.downloader.download_track_by_id(getattr(track, 'trackId', None), self.album_id, filepath, log_func=self.log)
                        self.log(f'[{idx}] 下载完成: {filename}')
                        page_progress['tracks'][track_id] = {'url': '', 'done': True, 'filename': filename}
                        self.save_progress(progress)
                        break
                    except Exception as e:
                        self.log(f'[{idx}] 下载失败: {e}')
                        page_progress['tracks'][track_id] = {'url': '', 'done': False, 'error': str(e), 'filename': filename}
                        self.save_progress(progress)
                        if attempt == 2:
                            self.log(f'[{idx}] 多次失败，跳过: {filename}')
                idx += 1
                if self.delay > 0:
                    time.sleep(self.delay)
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
        self.save_album_info()
        self.log('开始下载专辑音频...')
        self.fetch_and_download_tracks()


# 兼容原有函数式调用
def album_download(album_id, log_func=print):
    AlbumDownloader(album_id, log_func).download_album()
