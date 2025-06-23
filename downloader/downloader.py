import requests
import time
import hashlib
import os
from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException
from fetcher.track_fetcher import BlockedException

class M4ADownloader:
    def __init__(self, max_retries=3, retry_delay=3, connect_timeout=10):
        self.max_retries = max_retries
        self.retry_delay = retry_delay  # 延迟时间由上层(GUI)控制
        self.connect_timeout = connect_timeout
        self._partial_files = set()  # 跟踪部分下载的文件
        self._last_request_time = 0  # 记录上次请求时间

    def _download_once(self, url, output_file, log_func=print):
        """
        单次下载，不做重试，由外部处理异常
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.ximalaya.com/',
            'Accept': 'audio/webm,audio/ogg,audio/wav,audio/*;q=0.9,application/ogg;q=0.7,video/*;q=0.6,*/*;q=0.5',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'audio',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            # 'Cookie': '',  # 如有需要可在此处补充
        }
        self._partial_files.add(output_file)
        
        # 自定义SSL上下文
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        for attempt in range(3):
            try:
                response = requests.get(
                    url,
                    stream=True,
                    timeout=(self.connect_timeout, 20),
                    verify=False,
                    headers=headers,
                    cert=None,
                    proxies=None,
                    allow_redirects=True
                )
                break
            except requests.exceptions.SSLError as e:
                if attempt == 2:
                    raise
                log_func(f"SSL连接错误(尝试{attempt+1}/3): {e}", level='warning')
                time.sleep(1 * (attempt + 1))
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    raise
                log_func(f"请求错误(尝试{attempt+1}/3): {e}", level='warning')
                time.sleep(1 * (attempt + 1))
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(output_file, 'wb') as file:
            md5 = hashlib.md5()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    md5.update(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = downloaded * 100 // total
                        log_func(f"\r下载进度: {percent}% ({downloaded // 1024}KB/{total // 1024}KB)", level='info')
        
        # 验证文件完整性
        file_size = os.path.getsize(output_file)
        if total > 0 and file_size != total:
            raise Exception(f"文件大小不匹配: 预期 {total} 字节, 实际 {file_size} 字节")
            
        log_func(f"\n文件已成功下载并保存为: {output_file} (MD5: {md5.hexdigest()})", level='info')
        self._partial_files.discard(output_file)
        return True

    def download_m4a(self, url, output_file, log_func=print):
        for attempt in range(1, self.max_retries + 1):
            try:
                # 控制请求频率
                now = time.time()
                if now - self._last_request_time < self.retry_delay:  # 使用统一延迟设置
                    wait_time = self.retry_delay - (now - self._last_request_time)
                    log_func(f"等待{wait_time:.1f}秒避免风控...", level='info')
                    time.sleep(wait_time)
                
                self._last_request_time = time.time()
                return self._download_once(url, output_file, log_func=log_func)
            except BlockedException as e:
                log_func(f"\n风控触发: {e}", level='error')
                raise  # 向上抛出风控异常
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if hasattr(e, 'response') and e.response:
                    try:
                        error_data = e.response.json()
                        if error_data.get('ret') == 1001:  # 风控错误码
                            log_func(f"\n风控触发({attempt}/{self.max_retries}): {error_data.get('msg')}", level='warning')
                            if attempt < self.max_retries:
                                wait_time = self.retry_delay * attempt  # 指数退避
                                log_func(f"等待{wait_time}秒后重试...", level='info')
                                time.sleep(wait_time)
                                continue
                    except ValueError:
                        pass
                
                log_func(f"\n下载失败({attempt}/{self.max_retries}): {error_msg}", level='warning')
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * attempt  # 指数退避
                    log_func(f"等待{wait_time}秒后重试...", level='info')
                    time.sleep(wait_time)
                else:
                    log_func(f"多次重试失败，跳过该文件: {output_file}", level='error')
                    # 保存进度以便断点续传
                    if os.path.exists(output_file):
                        log_func(f"保留部分下载文件以便续传: {output_file}", level='info')
        return False

    def get_track_download_url(self, track_id, album_id=None):
        """
        统一获取track的真实下载url，外部只需传track_id和可选album_id
        """
        from fetcher.track_fetcher import fetch_track_crypted_url
        from utils.utils import decrypt_url
        from requests.exceptions import SSLError
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                crypted_url = fetch_track_crypted_url(int(track_id), album_id)
                if not crypted_url and album_id is not None:
                    crypted_url = fetch_track_crypted_url(int(track_id), 0)
                if crypted_url:
                    return decrypt_url(crypted_url)
                return None
            except SSLError as e:
                if attempt == max_retries:
                    raise
                time.sleep(1 * attempt)  # 指数退避
            except TypeError:
                if attempt == max_retries:
                    crypted_url = fetch_track_crypted_url(int(track_id), 0)
                    if crypted_url:
                        return decrypt_url(crypted_url)
                    return None
                time.sleep(1 * attempt)

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
        try:
            url = self.get_track_download_url(track_id, album_id)
            if not url:
                log_func(f'未获取到下载URL: track_id={track_id}', level='error')
                raise Exception('未获取到下载URL')
            self.download_from_url(url, output_file, log_func=log_func)
        except Exception as e:
            if output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                    log_func(f'已清理失败下载文件: {output_file}', level='info')
                except Exception as cleanup_err:
                    log_func(f'清理失败文件出错: {cleanup_err}', level='warning')
            raise

# 兼容旧接口，统一对外调用
Downloader = M4ADownloader
