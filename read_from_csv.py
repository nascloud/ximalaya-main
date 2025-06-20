import csv
from utils import decrypt_url
import requests


def read_csv_and_extract_trackid_title(file_path):
    # 用于存储 trackId 和 title 的列表
    trackid_title_list = []
    try:
        # 打开 CSV 文件
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            # 创建 CSV 字典读取器
            reader = csv.DictReader(csvfile)
            # 遍历每一行
            for row in reader:
                # 提取 trackId 和 title
                trackid = row['trackId']
                title = row['title']
                # 将结果添加到列表中
                trackid_title_list.append((trackid, title))
    except FileNotFoundError:
        print(f"错误：文件 '{file_path}' 未找到。")
    except KeyError:
        print("错误：CSV 文件中缺少必要的字段（trackId 或 title）。")
    except Exception as e:
        print(f"发生未知错误：{e}")
    return trackid_title_list


def fetch_track_crypted_url(track_id: int, album_id: int) -> str:
    """Fetch the crypted URL for a specific track."""
    url = f"https://www.ximalaya.com/mobile-playpage/track/v3/baseInfo/{album_id}"
    params = {
        "device": "web",
        "trackId": track_id,
        "trackQualityLevel": 1
    }
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en,zh;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,ja;q=0.6",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "trackType=web; x_xmly_traffic=utm_source%3A%26utm_medium%3A%26utm_campaign%3A%26utm_content%3A%26utm_term%3A%26utm_from%3A; DATE=1729142436687; crystal=U2FsdGVkX1+dItHuY3DbtMWa2ceN6qxfhxLChgSTHXtgjIr3TYItoD2hhAue5ytt3Jnk8L3IyVI9fK6cdOX0WLPjU/mFg0oCeAMOOb9wzRnjW2i6OZ+5WyQdDcXC1XzgAMqDSNt7qWF3S/EFnuaFIMrE3JE5rJx6VmpAM98WNJfMnCurbRiZo92/Zlc4WhLtn3S0SNWsBNZniTly+84E6brbfrS+fNgh5yDEV3Dbns29yafBjw4jxUFNg2cLqly4; HMACCOUNT=217EC9B39B1E50CC; _xmLog=h5&6f4a8d7e-802b-4c5e-bb79-e185ee4b4496&2.4.24; HWWAFSESID=b1ddc11e0f071ca78e9; HWWAFSESTIME=1732539064152; xm-page-viewid=ximalaya-web; wfp=ACM1NDc4ZjEwMGQ2MTVjYzA42VW5kBm-9lp4bXdlYl93d3c; Hm_lvt_4a7d8ec50cfd6af753c4f8aee3425070=1735621341; impl=www.ximalaya.com.login; 1&remember_me=y; 1&_token=261537404&B1521A00340N3BABEC5C58B1CCF86F05E1FE1880AAE32F094748EF225F558E364F8AB755167E37M1B3E1B382E1F81C_; 1_l_flag=261537404&B1521A00340N3BABEC5C58B1CCF86F05E1FE1880AAE32F094748EF225F558E364F8AB755167E37M1B3E1B382E1F81C__2024-12-3113:02:43; Hm_lpvt_4a7d8ec50cfd6af753c4f8aee3425070=1736144573; vmce9xdq=U2FsdGVkX19CbSiiklsgB9dLMd0zfCjngZkuQGMRD7DdmXzmJYEbYCgFFnFHKJq9hDwR63O4FfnJVrcTOQrcKjuojqD+d+UCPqXwlocl2U/0HE4BXr2LabICW3iKuT6C9Bnp9mS5g0A9NoVK/IGN/gzqY4q0DUv1DfCjUA0Z/9w=; cmci9xde=U2FsdGVkX183q+wek0rs4kuUKylAdsShJcZZPgItp2CCcJ3OqFe5bBlKm2GfG4NZyduW3hJH5YLvxVAZEk8sgw==; pmck9xge=U2FsdGVkX1+kKHyBa5ulzd1qezGyDzfsrGAyHcEi5YE=; assva6=U2FsdGVkX1+rl/qqQFi3bt9+KcLGFTyQySXMLda+Nf0=; assva5=U2FsdGVkX1+z4Sm/ym/H47HC6jsyVxj1adEaSk4bD+dndcBq8AeHikjNCHQe1V7vMDVaWgEW+XMk5yI41Dm+dQ==; web_login=1736144983604",
        "DNT": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"'
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


# if __name__ == '__main__':
#     album_list = read_csv_and_extract_trackid_title('/Users/lynn/Documents/喜马拉雅vip列表/【白夜剧场】三国机密（全集）|马伯庸作品|马天宇、韩东君、万茜主演影视原著|历史悬疑有声剧.csv')
#
#     # print("url: "+fetch_track_crypted_url('837267790', 53369258))
#
#     for track_id, title in album_list:
#         url = decrypt_url(fetch_track_crypted_url(track_id, 34588643))
#         print(track_id, title, url)
#         download_m4a(url, title.replace("/", "") + ".m4a")
