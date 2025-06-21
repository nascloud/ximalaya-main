import requests
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()
XIMALAYA_COOKIES = os.getenv("XIMALAYA_COOKIES", "")

def fetch_track_info(track_id: int) -> dict:
    """
    获取单个音频(track)的详细信息，返回字典
    """
    url = f"https://www.ximalaya.com/revision/track/simple?trackId={track_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Cookie": XIMALAYA_COOKIES,
        "Referer": f"https://www.ximalaya.com/sound/{track_id}",
        "x-kl-kfa-ajax-request": "Ajax_Request",
        "Connection": "keep-alive",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            return response.json()
        except Exception as e:
            print(f"解析track info失败: {e}")
            return {}
    else:
        print(f"Failed to fetch track info: {response.status_code}, {response.text}")
        return {}

def parse_track_info(resp: dict) -> dict:
    """
    解析track_info_fetcher返回的原始数据，提取常用字段，返回更友好的结构
    """
    if not resp or 'data' not in resp:
        return {}
    data = resp['data']
    track = data.get('trackInfo', {})
    album = data.get('albumInfo', {})
    return {
        'trackId': track.get('trackId'),
        'title': track.get('title'),
        'cover': track.get('coverPath'),
        'duration': track.get('duration'),
        'playCount': track.get('playCount'),
        'isPaid': track.get('isPaid'),
        'price': track.get('price'),
        'vipType': track.get('vipType'),
        'isVipFree': track.get('isVipFree'),
        'likeCount': track.get('likeCount'),
        'commentCount': track.get('commentCount'),
        'updatedAt': track.get('updatedAt'),
        'albumId': album.get('albumId'),
        'albumTitle': album.get('title'),
        'albumCover': album.get('coverPath'),
        'albumPlayCount': album.get('playCount'),
        'albumTrackCount': album.get('trackCount'),
        'albumDescription': album.get('description'),
        'albumCategory': album.get('categoryTitle'),
        'hasBuy': data.get('hasBuy'),
        'vipPermission': data.get('vipPermission'),
    }

@dataclass
class TrackInfo:
    trackId: int
    title: str
    cover: str
    duration: int

def get_track_info(track_id: int) -> TrackInfo:
    """
    一步获取 TrackInfo 数据类对象，简化调用
    自动处理cover为完整URL
    """
    raw = fetch_track_info(track_id)
    info = parse_track_info(raw)
    cover = info.get('cover', '')
    if cover and cover.startswith('//'):
        cover = 'https:' + cover
    return TrackInfo(
        trackId=info.get('trackId', 0),
        title=info.get('title', ''),
        cover=cover,
        duration=info.get('duration', 0)
    )

# Example usage:
if __name__ == "__main__":
    track_id = 329280743  # 示例 trackId
    track_info = get_track_info(track_id)
    print(f"Track ID: {track_info.trackId}")
    print(f"Title: {track_info.title}")
    print(f"Cover: {track_info.cover}")
    print(f"Duration: {track_info.duration} seconds")
