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
        response.raise_for_status()  # Raise an error for bad responses
        # 保存响应内容到文件
        with open(f"album_{album_id}.json", 'w', encoding='utf-8') as f:
            f.write(response.text)
        if response.status_code == 200:
            data = response.json()
            album_info = data.get("data", {}).get("albumPageMainInfo", {})
            cover = album_info.get('cover', '')
            # 自动拼接完整封面地址
            if cover and cover.startswith('//'):
                cover = 'https:' + cover
            elif cover and not cover.startswith('http'):
                cover = 'https://imagev2.xmcdn.com/' + cover.lstrip('/')
            album = Album(albumId=album_id, albumTitle=album_info.get('albumTitle', ''), 
                          cover=cover,
                          createDate=album_info.get('createDate', ''),
                          updateDate=album_info.get('updateDate', ''), 
                          richIntro=album_info.get('richIntro', ''), 
                          tracks=[]
                          )
            return album
        else:
            print(f"Failed to fetch album info: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Exception fetching album info: {e}")
        return None
