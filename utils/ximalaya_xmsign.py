import requests
import time
import hashlib
import random
import json
import urllib3
import os
from dotenv import load_dotenv

# 禁用 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 加载环境变量
load_dotenv()

# 从环境变量获取配置
SERVER_TIME_URL = os.getenv("XIMALAYA_SERVER_TIME_URL")
USER_AGENT = os.getenv("XIMALAYA_USER_AGENT")

# 獲取sign簽名

def get_sign(headers):
    serverTimeUrl = SERVER_TIME_URL
    response = requests.get(serverTimeUrl, headers=headers, verify=False)
    serverTime = response.text
    nowTime = str(round(time.time() * 1000))

    sign = str(hashlib.md5("himalaya-{}".format(serverTime).encode()).hexdigest()) + "({})".format(
        str(round(random.random() * 100))) + serverTime + "({})".format(str(round(random.random() * 100))) + nowTime
    headers["xm-sign"] = sign
    return headers


def get_header():
    headers = {
        "User-Agent": USER_AGENT
    }
    headers = get_sign(headers)
    return headers


# 如需在其他模块调用 get_sign/get_header，请使用：
# from utils.ximalaya_xmsign import get_sign, get_header

if __name__ == '__main__':
    # 這是一個搜索接口
    url = "https://www.ximalaya.com/revision/search/main?core=all&spellchecker=true&device=iPhone&kw=%E9%9B%AA%E4%B8%AD%E6%82%8D%E5%88%80%E8%A1%8C&page=1&rows=20&condition=relation&fq=&paidFilter=false"
    s = requests.get(url, headers=get_header(), verify=False)
    print(s.json())
