import requests
import os
import time

# 如需用到 decrypt_url，可这样导入：
# from utils.utils import decrypt_url

class M4ADownloader:
    def __init__(self, max_retries=3, retry_delay=3):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def download_m4a(self, url, output_file):
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(url, stream=True, timeout=20)
                response.raise_for_status()
                total = int(response.headers.get('content-length', 0))
                downloaded = 0
                with open(output_file, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                percent = downloaded * 100 // total
                                print(f"\r下载进度: {percent}% ({downloaded // 1024}KB/{total // 1024}KB)", end="")
                print(f"\n文件已成功下载并保存为: {output_file}")
                return True
            except requests.exceptions.RequestException as e:
                print(f"\n下载失败({attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    print(f"等待{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"多次重试失败，跳过该文件: {output_file}")
        return False

    def batch_download(self, tracks, album_title, download_dir=None):
        # 默认下载目录为 ./downloads/专辑名/
        if not download_dir:
            safe_album = ''.join(c for c in album_title if c not in ':/\\*?"<>|')
            download_dir = os.path.join(os.getcwd(), 'downloads', safe_album)
        os.makedirs(download_dir, exist_ok=True)
        total = tracks[0].totalCount if tracks and hasattr(tracks[0], 'totalCount') and tracks[0].totalCount else len(tracks)
        page = tracks[0].page if tracks and hasattr(tracks[0], 'page') else None
        page_size = tracks[0].pageSize if tracks and hasattr(tracks[0], 'pageSize') else None
        cover = tracks[0].cover if tracks and hasattr(tracks[0], 'cover') else None
        if cover:
            print(f"专辑封面: {cover}")
        print(f"总音频数: {total}, 当前页: {page}, 每页: {page_size}")
        for idx, track in enumerate(tracks, 1):
            safe_title = ''.join(c for c in track.title if c not in ':/\\*?"<>|')
            filename = f"{idx:03d}_{safe_title}.m4a"
            filepath = os.path.join(download_dir, filename)
            print(f"正在下载({idx}/{len(tracks)}): {track.title}")
            if track.url:
                self.download_m4a(track.url, filepath)
            else:
                print(f"跳过: {track.title}，无有效播放链接")
