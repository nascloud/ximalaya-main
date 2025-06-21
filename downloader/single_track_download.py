import os
from downloader.downloader import Downloader

def download_single_track(track_id, album_id=None, filename=None, log_func=print, save_dir=None):
    """
    下载单个音频文件
    :param track_id: 音频ID
    :param album_id: 可选，部分接口需要
    :param filename: 保存文件名，默认使用音频标题.m4a
    :param log_func: 日志输出函数，支持level参数
    :param save_dir: 保存目录
    """
    from fetcher.track_info_fetcher import get_track_info
    # 获取音频信息用于文件名
    track_info = get_track_info(int(track_id))
    if not track_info or not track_info.title:
        log_func('未获取到音频信息', level='error')
        return False
    if not filename:
        safe_title = track_info.title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        filename = f'{safe_title or track_id}.m4a'
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
    else:
        filepath = filename
    downloader = Downloader()
    try:
        downloader.download_track_by_id(track_id, album_id, filepath, log_func=log_func)
        log_func(f'单曲下载完成: {filename}', level='info')
        return True
    except Exception as e:
        log_func(f'单曲下载失败: {e}', level='error')
        return False
