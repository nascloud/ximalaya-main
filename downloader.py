import requests
import os

def download_m4a(url, output_file):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"文件已成功下载并保存为: {output_file}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")

def batch_download(tracks, album_title, download_dir=None):
    # 默认下载目录为 ./downloads/专辑名/
    if not download_dir:
        safe_album = ''.join(c for c in album_title if c not in '\/:*?"<>|')
        download_dir = os.path.join(os.getcwd(), 'downloads', safe_album)
    os.makedirs(download_dir, exist_ok=True)
    for idx, track in enumerate(tracks, 1):
        safe_title = ''.join(c for c in track.title if c not in '\/:*?"<>|')
        filename = f"{idx:03d}_{safe_title}.m4a"
        filepath = os.path.join(download_dir, filename)
        print(f"正在下载({idx}/{len(tracks)}): {track.title}")
        if track.url:
            download_m4a(track.url, filepath)
        else:
            print(f"跳过: {track.title}，无有效播放链接")
