import requests
import os
from utils import decrypt_url
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List

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
