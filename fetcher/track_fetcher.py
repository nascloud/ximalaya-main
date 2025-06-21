import requests
import os
from utils.utils import decrypt_url
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Optional
import urllib3
# 忽略 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
XIMALAYA_COOKIES = os.getenv("XIMALAYA_COOKIES", "")

@dataclass
class Track:
    trackId: int
    title: str
    createTime: str
    updateTime: str
    cryptedUrl: str
    url: str
    duration: int
    totalCount: Optional[int] = None  # 专辑下音频总数
    page: Optional[int] = None        # 当前页码
    pageSize: Optional[int] = None    # 每页音频数量
    cover: Optional[str] = None       # 专辑封面

def fetch_track_crypted_url(track_id: int, album_id: int) -> str:
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
            return play_url_list[0].get("url", "")
    print(f"Failed to fetch cryptedUrl for track {track_id}: {response.status_code}, {response.text}")
    return ""

def fetch_album_tracks(album_id: int, page: int, page_size: int) -> List[Track]:
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
            track_info = track['trackInfo']
            crypted_url = fetch_track_crypted_url(track_info["id"], album_id)
            if not crypted_url:
                print(f"跳过: {track_info['title']}，无有效播放链接")
                continue
            cover_path = track_info.get("cover")
            cover_url = f"https://imagev2.xmcdn.com/{cover_path}" if cover_path and not cover_path.startswith("http") else cover_path
            tracks.append(
                Track(
                    trackId=track_info["id"],
                    title=track_info["title"],
                    createTime=track_info["createdTime"],
                    updateTime=track_info["updatedTime"],
                    cryptedUrl=crypted_url,
                    url=decrypt_url(crypted_url),
                    duration=track_info.get("duration", 0),
                    totalCount=data.get("data", {}).get("totalCount"),  # 专辑音频总数
                    page=page,  # 当前页码
                    pageSize=page_size,  # 每页数量
                    cover=cover_url,  # 拼接后的专辑封面
                )
            )
        return tracks
    else:
        print(f"Failed to fetch tracks: {response.status_code}, {response.text}")
        return []
