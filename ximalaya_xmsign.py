import requests
import time
import hashlib
import random
import json
import urllib3
# 禁用 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 獲取sign簽名

def get_sign(headers):
    serverTimeUrl = "https://www.ximalaya.com/revision/time"
    response = requests.get(serverTimeUrl, headers=headers, verify=False)
    serverTime = response.text
    nowTime = str(round(time.time() * 1000))

    sign = str(hashlib.md5("himalaya-{}".format(serverTime).encode()).hexdigest()) + "({})".format(
        str(round(random.random() * 100))) + serverTime + "({})".format(str(round(random.random() * 100))) + nowTime
    headers["xm-sign"] = sign
    return headers


def get_header():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36"
    }
    headers = get_sign(headers)
    return headers


if __name__ == '__main__':
    # 這是一個搜索接口
    url = "https://www.ximalaya.com/revision/search/main?core=all&spellchecker=true&device=iPhone&kw=%E9%9B%AA%E4%B8%AD%E6%82%8D%E5%88%80%E8%A1%8C&page=1&rows=20&condition=relation&fq=&paidFilter=false"
    s = requests.get(url, headers=get_header(), verify=False)
    print(s.json())
