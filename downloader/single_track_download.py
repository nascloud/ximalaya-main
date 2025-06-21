import os
from fetcher.track_fetcher import fetch_track_crypted_url
from downloader.downloader import M4ADownloader
from utils.utils import decrypt_url

def download_single_track(track_id, album_id=None, filename=None, log_func=print, save_dir=None):
    """
    下载单个音频文件
    :param track_id: 音频ID
    :param album_id: 可选，部分接口需要
    :param filename: 保存文件名，默认<track_id>.m4a
    :param log_func: 日志输出函数
    :param save_dir: 保存目录
    """
    try:
        crypted_url = fetch_track_crypted_url(int(track_id), album_id)
    except TypeError:
        crypted_url = fetch_track_crypted_url(int(track_id), 0)
    if not crypted_url:
        log_func('未获取到加密URL')
        return False
    url = decrypt_url(crypted_url)
    if not filename:
        filename = f'{track_id}.m4a'
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
    else:
        filepath = filename
    downloader = M4ADownloader()
    log_func(f'正在下载: {filename}')
    downloader.download_m4a(url, filepath)
    log_func('下载完成')
    return True
