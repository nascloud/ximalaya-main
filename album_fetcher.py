import requests
import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()
XIMALAYA_COOKIES = os.getenv("XIMALAYA_COOKIES", "")

@dataclass
class Album:
    albumId: int
    albumTitle: str
    cover: str
    createDate: str
    updateDate: str
    richIntro: str
    tracks: list

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
