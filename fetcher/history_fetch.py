import json
import requests
from fetcher.track_fetcher import fetch_track_crypted_url
from utils.utils import decrypt_url
from dotenv import load_dotenv
import os


# Track 类定义
class Track:
    def __init__(self, item_title, child_title, item_id, child_id):
        self.item_title = item_title
        self.child_title = child_title
        self.item_id = item_id
        self.child_id = child_id

    def __str__(self):
        return f"{self.item_title} - {self.child_title} , (ItemID:{self.item_id} - childID: {self.child_id})"

load_dotenv()

# 从环境变量读取 cookie 字符串，并转为字典
def parse_cookies(cookie_string):
    cookies = {}
    for kv in cookie_string.split(';'):
        if '=' in kv:
            k, v = kv.strip().split('=', 1)
            cookies[k] = v
    return cookies



# 模拟请求头和 Cookies（从你的 curl 命令中提取）
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en,zh;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,ja;q=0.6',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    'DNT': '1',
    'Referer': 'https://www.ximalaya.com/my/listened',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

cookie_string = os.getenv("XIMALAYA_COOKIES")
cookies = parse_cookies(cookie_string)

# cookies = {
#     '_xmLog': 'h5&b12e781c-7288-41ba-aecb-0dba6f70ee01&2.4.24',
#     'Hm_lvt_4a7d8ec50cfd6af753c4f8aee3425070': '1742965419',
#     'HWWAFSESID': '89cad1c0e9991fce034',
#     'HWWAFSESTIME': '1748065418963',
#     'DATE': '1736333658056',
#     'crystal': 'U2FsdGVkX1+513dBr1CaTub0yzK+54KTIR+D9PWRYisDMIyaS8gqw46GFzZdmQmZAgi+uSb8qjkuoEED00WkdXpevDS0AQokX5/2ZWGuYtqJqAbSc2bDdBRKMXNDNQTDf/WpVso9feUEV1olX+LnBQrk9GN/FMuaeisLi3l2NQdlyn2VwiwlLGALO7seJKIMqqiqYSH1X8DyELImOWTsN46uuySAQcBow+bXvqWej5q8uXRni5PCkQlOYqJC6irn',
#     'impl': 'www.ximalaya.com.login',
#     '1&remember_me': 'y',
#     '1&_token': '544301838&222952B0340N4E5BA4A27488967141386252714A1DF2B3F87672EEF4E8FAE417941DED5DACB516M7C556747717A6F2_',
#     '1_l_flag': '544301838&222952B0340N4E5BA4A27488967141386252714A1DF2B3F87672EEF4E8FAE417941DED5DACB516M7C556747717A6F2__2025-05-2413:49:36',
#     'xm-page-viewid': 'ximalaya-web',
#     'wfp': 'ACM2NDUxMGI0NDFlMzNjMWRhIcJ7ir85-VJ4bXdlYl93d3c',
#     'vmce9xdq': 'U2FsdGVkX1+g2ndyrF2HWwYI/K0P8pfUik77TbphQ0Q=',
#     'web_login': '1748741923046',
#     'cmci9xde': 'U2FsdGVkX1/BUuG/y5bBCmVDas4tej4d8+lC88jBKdXQs480fdZtilY807FVfs0WvOcI7Iq6sywrlv/tbOrYEg==',
#     'pmck9xge': 'U2FsdGVkX19Wybgijz7emajrdQCxlIEvgNV5r1GpaA0=',
#     'assva6': 'U2FsdGVkX19IOM3audtqJpEWDBy2DHvSGIwmdY1rrAs=',
#     'assva5': 'U2FsdGVkX19xCwcmUH/3Dte+8hs9+z64eEfZa0o23FsdEoTRBqkQSxZ9I4mDSA7WTyB5PqhP/DeWgeWugIGXsg==',
# }

url = 'https://www.ximalaya.com/revision/track/history/listen?includeChannel=false&includeRadio=false'

# 请求数据
response = requests.get(url, headers=headers, cookies=cookies)

# 解析返回的 JSON
data = response.json()
print(data)

# 提取信息
result = []
tracks = []

for section in ['today', 'yesterday', 'earlier']:
    for item in data.get('data', {}).get(section, []):
        track = Track(
            item_title=item.get('itemTitle'),
            child_title=item.get('childTitle'),
            item_id=item.get('itemId'),
            child_id=item.get('childId')
        )
        tracks.append(track)

# 打印结果
print("result:")
for track in tracks:
    print(f"{track.item_title}:" + decrypt_url(fetch_track_crypted_url(track.child_id, track.item_id)))
