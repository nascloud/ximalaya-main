import requests
import time

class M4ADownloader:
    def __init__(self, max_retries=3, retry_delay=3):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _download_once(self, url, output_file, log_func=print):
        """
        单次下载，不做重试，由外部处理异常
        """
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
                        log_func(f"\r下载进度: {percent}% ({downloaded // 1024}KB/{total // 1024}KB)", level='info')
        log_func(f"\n文件已成功下载并保存为: {output_file}", level='info')
        return True

    def download_m4a(self, url, output_file, log_func=print):
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._download_once(url, output_file, log_func=log_func)
            except requests.exceptions.RequestException as e:
                log_func(f"\n下载失败({attempt}/{self.max_retries}): {e}", level='warning')
                if attempt < self.max_retries:
                    log_func(f"等待{self.retry_delay}秒后重试...", level='info')
                    time.sleep(self.retry_delay)
                else:
                    log_func(f"多次重试失败，跳过该文件: {output_file}", level='error')
        return False

    def get_track_download_url(self, track_id, album_id=None):
        """
        统一获取track的真实下载url，外部只需传track_id和可选album_id
        """
        from fetcher.track_fetcher import fetch_track_crypted_url
        from utils.utils import decrypt_url
        try:
            crypted_url = fetch_track_crypted_url(int(track_id), album_id)
        except TypeError:
            crypted_url = fetch_track_crypted_url(int(track_id), 0)
        if not crypted_url:
            return None
        return decrypt_url(crypted_url)

    def download_from_url(self, url, output_file, log_func=print):
        """
        直接下载指定url到本地文件，带重试和日志
        """
        log_func(f'正在下载: {output_file}', level='info')
        self.download_m4a(url, output_file, log_func=log_func)
        log_func('下载完成', level='info')
        return True

    def download_track_by_id(self, track_id, album_id=None, output_file=None, log_func=print):
        """
        通过track_id和album_id直接下载音频到指定文件
        """
        url = self.get_track_download_url(track_id, album_id)
        if not url:
            log_func(f'未获取到下载URL: track_id={track_id}', level='error')
            raise Exception('未获取到下载URL')
        self.download_from_url(url, output_file, log_func=log_func)

# 兼容旧接口，统一对外调用
Downloader = M4ADownloader

