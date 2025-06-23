import os
import re
from fetcher.album_fetcher import fetch_album
from fetcher.track_fetcher import fetch_album_tracks
from downloader.downloader import M4ADownloader


class AlbumDownloader:
    def __init__(self, album_id, log_func=print, delay=0, save_dir=None, progress_func=None, album=None, total_count=None):
        self.album_id = int(album_id)
        self.log = log_func
        self.album = album if album is not None else None
        self.tracks = []
        self.save_dir = save_dir  # 支持外部传递下载目录
        self.downloader = M4ADownloader()
        self.delay = delay  # 下载延迟（秒）
        self.progress_func = progress_func
        self._total_count_override = total_count
        self._partial_files = set()  # 跟踪部分下载的文件

    def fetch_album_info(self):
        # 如果已传入album对象则直接用，无需重复获取
        if self.album is None:
            self.album = fetch_album(self.album_id)
        if not self.album:
            self.log('获取专辑信息失败', level='error')
            return False
        # 过滤专辑名中的非法字符
        safe_album_title = re.sub(r'[\\/:*?"<>|]', '_', self.album.albumTitle)
        if self.save_dir:
            self.save_dir = os.path.join(self.save_dir, safe_album_title)
        else:
            self.save_dir = os.path.join('downloads', safe_album_title)
        os.makedirs(self.save_dir, exist_ok=True)
        self.log(f'专辑：{self.album.albumTitle}，准备下载...', level='info')
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
            self.log(f'保存专辑信息失败: {e}', level='error')
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
            self.log(f'保存专辑markdown信息失败: {e}', level='error')
        # 下载封面图片
        cover_url = getattr(self.album, 'cover', None)
        if cover_url:
            try:
                resp = requests.get(cover_url, timeout=10)
                if resp.status_code == 200:
                    with open(os.path.join(self.save_dir, 'cover.jpg'), 'wb') as f:
                        f.write(resp.content)
                else:
                    self.log(f'封面下载失败，状态码: {resp.status_code}', level='warning')
            except Exception as e:
                self.log(f'下载封面失败: {e}', level='warning')

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
        import time
        progress_file = self._get_progress_file()
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(1, max_retries + 1):
            try:
                # Windows兼容的原子写入方式
                dir_name = os.path.dirname(progress_file)
                tmp_file = None
                try:
                    # 显式创建临时文件并确保关闭
                    tf = tempfile.NamedTemporaryFile(
                        'w', encoding='utf-8', 
                        dir=dir_name, 
                        delete=False
                    )
                    tmp_file = tf.name
                    json.dump(progress, tf, ensure_ascii=False, indent=2)
                    tf.flush()
                    os.fsync(tf.fileno())
                    tf.close()  # 显式关闭文件句柄
                    
                    # 尝试重命名
                    os.replace(tmp_file, progress_file)
                    return  # 成功则直接返回
                except Exception as e:
                    if tmp_file and os.path.exists(tmp_file):
                        try:
                            os.remove(tmp_file)
                        except:
                            pass
                    if attempt == max_retries:
                        raise
                    time.sleep(retry_delay * attempt)
            except Exception as e:
                if attempt == max_retries:
                    self.log(f'保存进度失败(尝试{attempt}次): {e}', level='error')
                    raise
                time.sleep(retry_delay * attempt)

    def fetch_and_download_tracks(self):
        import json
        import time
        page_size = 20
        progress = self.load_progress()
        downloaded_files = set(os.listdir(self.save_dir))
        failed_tracks = []  # [(page, track_id, filename, idx, error_log)]
        total_count = None
        idx_map = {}  # track_id -> idx
        # 先获取第一页，拿到总数
        # 风控检测标志
        self._blocked = False
        from fetcher.track_fetcher import BlockedException
        def fetch_album_tracks_with_block_check(album_id, page, page_size):
            try:
                if self._blocked:
                    raise BlockedException('操作因风控被阻止')
                tracks = fetch_album_tracks(album_id, page, page_size)
                return tracks
            except BlockedException as be:
                self.log(f'检测到风控，已暂停下载：{be}', level='error')
                progress = self.load_progress()
                progress['blocked'] = True
                self.save_progress(progress)
                self._blocked = True
                return None

        first_page_tracks = fetch_album_tracks_with_block_check(self.album_id, 1, page_size)
        if not first_page_tracks:
            self.log('未获取到专辑曲目，可能被风控，请稍后重试', level='error')
            # 记录风控状态
            progress = self.load_progress()
            progress['blocked'] = True
            self.save_progress(progress)
            self._blocked = True
            return
        # 优先使用传递的总数
        if self._total_count_override is not None and self._total_count_override > 0:
            total_count = self._total_count_override
        elif hasattr(first_page_tracks[0], 'totalCount'):
            total_count = first_page_tracks[0].totalCount
        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size if total_count else 1
        # 统计所有已完成的track数
        downloaded = 0
        # 统计所有未完成的track
        idx = 1
        # 优化：直接跳到未完成的最小页码
        min_unfinished_page = None
        for page in range(1, total_pages + 1):
            page_key = str(page)
            page_progress = progress.get(page_key, {})
            tracks_progress = page_progress.get('tracks', {})
            if not page_progress.get('done'):
                min_unfinished_page = page
                break
            idx += page_size
        if min_unfinished_page is None:
            self.log('所有音频已完成，无需下载', level='info')
            return
        # 从未完成的最小页码开始遍历
        page = min_unfinished_page
        while page <= total_pages:
            page_key = str(page)
            page_progress = progress.get(page_key, {})
            tracks_progress = page_progress.get('tracks', {})
            # 只请求未完成页
            if page == 1:
                page_tracks = first_page_tracks
            else:
                if page_progress.get('done'):
                    idx += page_size
                    page += 1
                    continue
                page_tracks = fetch_album_tracks_with_block_check(self.album_id, page, page_size)
            if not page_tracks:
                self.log('检测到风控或接口异常，已暂停下载。请稍后重启程序。', level='error')
                progress['blocked'] = True
                self.save_progress(progress)
                self._blocked = True
                break
            for i, track in enumerate(page_tracks):
                safe_title = re.sub(r'[\\/:*?"<>|]', '_', getattr(track, 'title', str(getattr(track, 'trackId', idx))))
                filename = f'{idx:03d}_{safe_title}.m4a'
                filepath = os.path.join(self.save_dir, filename)
                track_id = str(getattr(track, 'trackId', idx))
                idx_map[track_id] = idx
                track_status = tracks_progress.get(track_id, {})
                # 已完成
                if track_status.get('done'):
                    downloaded += 1
                    idx += 1
                    continue
                # 文件已存在且大于10KB，视为完成
                if filename in downloaded_files and os.path.getsize(filepath) > 1024 * 10:
                    tracks_progress[track_id] = {'url': '', 'done': True, 'filename': filename}
                    self.save_progress(progress)
                    downloaded += 1
                    idx += 1
                    continue
                # 未完成或失败
                failed_tracks.append((page, track_id, filename, idx, track_status.get('error', '')))
                idx += 1
            page += 1
        # 2. 优先补下所有未完成/失败的track，支持指数退避
        failed_log = []
        if self._blocked:
            self.log('下载已因风控暂停，未完成的音频请稍后重启程序继续。', level='error')
            progress = self.load_progress()
            progress['blocked'] = True
            self.save_progress(progress)
            return

        for page, track_id, filename, idx, last_error in failed_tracks:
            page_key = str(page)
            page_progress = progress.get(page_key, {})
            if 'tracks' not in page_progress:
                page_progress['tracks'] = {}
            error_detail = ''
            for attempt in range(5):
                try:
                    if self.progress_func and total_count:
                        self.progress_func(downloaded+1, total_count, filename)
                    self.log(f'[{idx}/{total_count or "?"}] 下载: {filename} (第{attempt+1}次尝试)', level='info')
                    self.downloader.download_track_by_id(int(track_id), self.album_id, os.path.join(self.save_dir, filename), log_func=self.log)
                    self.log(f'[{idx}] 下载完成: {filename}', level='info')
                    page_progress['tracks'][track_id] = {'url': '', 'done': True, 'filename': filename}
                    self.save_progress(progress)
                    downloaded += 1
                    if self.progress_func and total_count:
                        self.progress_func(downloaded, total_count, filename)
                    break
                except Exception as e:
                    error_detail = str(e)
                    self.log(f'[{idx}] 下载失败: {e}', level='warning')
                    if self.progress_func and total_count:
                        self.progress_func(downloaded, total_count, filename)
                    page_progress['tracks'][track_id] = {'url': '', 'done': False, 'error': error_detail, 'filename': filename}
                    self.save_progress(progress)
                    # 指数退避
                    sleep_time = min(2 ** attempt, 30)
                    time.sleep(sleep_time)
                    if attempt == 4:
                        self.log(f'[{idx}] 多次失败，跳过: {filename}', level='error')
                        failed_log.append({'page': page, 'track_id': track_id, 'filename': filename, 'idx': idx, 'error': error_detail})
            # 标记本页是否全部完成
            tracks_progress = page_progress['tracks']
            all_done = all(t.get('done') for t in tracks_progress.values()) and len(tracks_progress) >= 1
            if all_done:
                page_progress['done'] = True
            progress[page_key] = page_progress
            self.save_progress(progress)
        if failed_log:
            self.log('\n以下音频多次下载失败，请手动排查：', level='error')
            for item in failed_log:
                self.log(f"[页码:{item['page']}, idx:{item['idx']}, track_id:{item['track_id']}] {item['filename']}\n错误信息: {item['error']}", level='error')
        self.log('专辑下载完成', level='info')
        if self.progress_func and total_count:
            self.progress_func(total_count, total_count, '专辑下载完成')

    def download_album(self):
        if not self.fetch_album_info():
            return
        self.save_album_info()
        self.log('开始下载专辑音频...')
        try:
            self.fetch_and_download_tracks()
        except Exception as e:
            self.log(f'下载过程中发生错误: {e}', level='error')
            self.cleanup_partial_downloads()
            raise

    def cleanup_partial_downloads(self):
        """清理未完成的部分下载文件"""
        for filepath in self._partial_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self.log(f'已清理部分下载文件: {filepath}', level='info')
            except Exception as e:
                self.log(f'清理文件失败: {filepath}, 错误: {e}', level='warning')
        self._partial_files.clear()


# 兼容原有函数式调用
def album_download(album_id, log_func=print):
    AlbumDownloader(album_id, log_func).download_album()
