import requests
from dataclasses import dataclass, asdict
from typing import List
from utils import decrypt_url
import json
import os
from dotenv import load_dotenv


@dataclass
class Track:
    trackId: int
    title: str
    createTime: str
    updateTime: str
    cryptedUrl: str
    url: str
    duration: int


@dataclass
class Album:
    albumId: int
    albumTitle: str
    cover: str
    createDate: str
    updateDate: str
    richIntro: str
    tracks: List[Track]


# 加载 .env 文件
load_dotenv()
XIMALAYA_COOKIES = os.getenv("XIMALAYA_COOKIES", "")


def fetch_track_crypted_url(track_id: int, album_id: int) -> str:
    """Fetch the crypted URL for a specific track."""
    url = f"https://www.ximalaya.com/mobile-playpage/track/v3/baseInfo/{album_id}"
    params = {
        "device": "web",
        "trackId": track_id,
        "trackQualityLevel": 1
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Cookie": XIMALAYA_COOKIES
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        play_url_list = data.get("trackInfo", {}).get("playUrlList", [])
        if play_url_list:
            # Return the first URL in the playlist
            return play_url_list[0].get("url", "")
    print(f"Failed to fetch cryptedUrl for track {track_id}: {response.status_code}, {response.text}")
    return ""


def fetch_album_tracks(album_id: int, page: int, page_size: int) -> List[Track]:
    """Fetch the list of tracks for an album."""
    url = f"https://m.ximalaya.com/m-revision/common/album/queryAlbumTrackRecordsByPage"
    params = {
        "albumId": album_id,
        "page": page,
        "pageSize": page_size
    }
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": f"https://www.ximalaya.com/album/{album_id}",
        "Origin": "https://www.ximalaya.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Cookie": XIMALAYA_COOKIES,
        "X-Requested-With": "XMLHttpRequest"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        track_list = data.get("data", {}).get("trackDetailInfos", [])
        tracks = []
        for track in track_list:
            track = track['trackInfo']
            crypted_url = fetch_track_crypted_url(track["id"], album_id)
            tracks.append(
                Track(
                    trackId=track["id"],
                    title=track["title"],
                    createTime=track["createdTime"],
                    updateTime=track["updatedTime"],
                    cryptedUrl=crypted_url,
                    url=decrypt_url(crypted_url),
                    duration=track.get("duration", 0),
                )
            )
        return tracks
    else:
        print(f"Failed to fetch tracks: {response.status_code}, {response.text}")
        return []


def fetch_album(album_id):
    url = f"https://www.ximalaya.com/revision/album/v1/simple?albumId={album_id}"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Cookie": XIMALAYA_COOKIES
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            album_info = data.get("data", {}).get("albumPageMainInfo", {})
            album = Album(albumId=album_id, albumTitle=album_info.get('albumTitle', ''), cover=album_info.get('cover', ''),
                          createDate=album_info.get('createDate', ''),
                          updateDate=album_info.get('updateDate', ''), richIntro=album_info.get('richIntro', ''), tracks=[])
            return album
        else:
            print(f"Failed to fetch album info: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Exception fetching album info: {e}")
        return None


def download_m4a(url, output_file):
    try:
        # 发送 HTTP GET 请求
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 检查请求是否成功

        # 以二进制写入模式打开文件
        with open(output_file, 'wb') as file:
            # 分块写入文件
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"文件已成功下载并保存为: {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")



# todo: 目前有些专辑未登录用户无法取得加密的 url，比方说下面这个
# https://www.ximalaya.com/mobile-playpage/track/v3/baseInfo/54157194?device=web&trackId=491583482&trackQualityLevel=1
if __name__ == '__main__':
    # album_id = 34588643
    album_id = 70278366
    page = 1
    page_size = 10
    tracks = fetch_album_tracks(album_id, page, page_size)
    track_dicts = [asdict(track) for track in tracks]
    # print(json.dumps(track_dicts))
    album = fetch_album(album_id)
    album.tracks = tracks
    print(album)
    # fetch_track_crypted_url(267292575, 34588643)
