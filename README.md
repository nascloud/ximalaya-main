# **喜马拉雅项目文档**

## **1\. 项目概述**

"ximalaya" 项目是一个基于 Python 的工具集合，旨在帮助用户与喜马拉雅音频平台进行交互。它的主要功能包括获取用户的收听历史、获取专辑和曲目信息、解密加密的音频 URL 以及下载音频文件。该项目还包含了处理喜马拉雅 API 签名和从 CSV 文件读取曲目信息的功能。

## **2\. 功能特性**

* **收听历史获取：** 通过模拟网页请求，获取用户在喜马拉雅的收听历史记录。  
* **专辑与曲目信息检索：** 获取指定专辑的详细信息（如标题、封面、介绍）以及专辑内所有曲目的元数据（如ID、标题、时长、创建/更新时间）。  
* **音频 URL 解密：** 喜马拉雅部分音频 URL 是加密的，本项目提供了 AES 解密功能，可以将加密 URL 转换为可直接访问的音频文件链接。  
* **音频文件下载：** 支持将解密后的音频文件（通常是 .m4a 格式）下载并保存到本地。  
* **CSV 数据导入：** 能够从 CSV 文件读取曲目 ID 和标题，方便批量处理或下载。  
* **API 签名生成：** 包含用于生成喜马拉雅 API 请求所需 xm-sign 头的逻辑。
* **专辑批量下载与管理：** 通过 `album_fetcher.py` 可批量获取专辑下所有音频并下载，支持断点续传。
* **多线程下载加速：** `downloader.py` 支持多线程下载，显著提升大批量音频的下载速度。
* **曲目信息独立抓取：** `track_fetcher.py` 可单独抓取指定 trackId 的音频信息，便于灵活扩展。

## **3. 文件结构**

ximalaya/  
├── .gitignore  
├── .idea/                 # IDE 配置文件  
├── album_fetcher.py       # 专辑批量下载与管理脚本  
├── downloader.py          # 多线程下载工具  
├── history_fetch.py       # 获取收听历史的脚本  
├── main.py                # 主要功能脚本，包括专辑/曲目信息获取和下载  
├── read_from_csv.py       # 从 CSV 读取并处理曲目信息的脚本  
├── requirements.txt       # 项目依赖库列表  
├── test.js                # JavaScript 测试文件（可能与喜马拉雅的JS SDK相关）  
├── track_fetcher.py       # 单独抓取曲目信息的脚本  
├── utils.py               # 包含 URL 解密功能的工具函数  
├── ximalaya_xmsign.py     # 喜马拉雅 API 签名生成（旧版本）  
├── xm-demo.py             # 喜马拉雅 API 签名生成（新版本或示例）  
└── README.md

## **4\. 环境配置与安装**

### **4.1. 前提条件**

* Python 3.x  
* pip (Python 包管理器)

### **4.2. 安装依赖**

在项目根目录下，打开终端或命令行，运行以下命令安装所需的 Python 库：

pip install \-r requirements.txt

### **4.3. 配置喜马拉雅 Cookie**

history\_fetch.py 脚本需要您的喜马拉雅登录 Cookie 才能获取收听历史。请按照以下步骤操作：

1. 登录喜马拉雅网页版。  
2. 打开浏览器的开发者工具（通常按 F12）。  
3. 切换到 "Network"（网络）标签页。  
4. 刷新页面（例如：[https://www.ximalaya.com/my/listened](https://www.ximalaya.com/my/listened)）。  
5. 找到一个对 https://www.ximalaya.com/revision/track/history/listen 的请求。  
6. 在请求的 Headers 中找到 Cookie 字段，并复制其完整内容。  
7. 在项目根目录下创建一个 .env 文件（如果不存在），并在其中添加一行：  
   XIMALAYA\_COOKIES="\<您复制的Cookie内容\>"

   **请确保将 \<您复制的Cookie内容\> 替换为实际的 Cookie 字符串。**

## **5\. 使用方法**

### **5.1. 获取收听历史**

修改 history\_fetch.py 脚本，然后运行：

python history\_fetch.py

脚本将尝试打印您的收听历史，并解密出音频的播放链接。

### **5.2. 获取专辑和曲目信息并下载**

您可以通过 main.py 或 album_fetcher.py 获取专辑曲目信息并下载：

1. 修改 main.py 脚本中的 album\_id、page 和 page\_size 变量，然后运行：

    python main.py

   脚本将获取指定专辑的曲目列表，并打印出详细信息，包括解密后的播放 URL。如果您需要下载，可以调用 download\_m4a 函数。

2. 使用 album\_fetcher.py 进行批量下载：

    python album_fetcher.py --album_id <专辑ID> [--start_page 1] [--end_page N] [--threads 4]

   支持断点续传和多线程下载，适合大专辑批量下载。

### **5.3. 多线程下载用法**

如果需要加速下载，可直接调用 downloader.py：

    python downloader.py --url <音频URL> --output <保存文件名> [--threads 8]

也可在 main.py、album_fetcher.py 等脚本中导入 downloader.py 的 download\_m4a\_multithread 函数进行自定义调用。

### **5.4. 单独抓取曲目信息**

track\_fetcher.py 支持通过 trackId 获取单个音频的详细信息：

    python track_fetcher.py --track_id <音频ID> [--album_id <专辑ID>]

### **5.5. 从 CSV 文件下载**

如果您有一个包含 trackId 和 title 列的 CSV 文件，可以使用 read\_from\_csv.py 脚本。

修改 read\_from\_csv.py 中 CSV 文件的路径和 album\_id，然后取消注释下载相关的代码行：

# if __name__ == '__main__':  
#     album_list = read_csv_and_extract_trackid_title('your_csv_path.csv')  
#     for track_id, title in album_list:  
#         url = decrypt_url(fetch_track_crypted_url(track_id, 34588643)) # 这里的 34588643 应该替换为您的 album_id  
#         print(track_id, title, url)  
#         download_m4a(url, title.replace("/", "") + ".m4a")

然后运行：

python read\_from\_csv.py

### **5.6. API 签名测试**

ximalaya\_xmsign.py 和 xm-demo.py 提供了生成 xm-sign 的示例。您可以直接运行它们来观察签名的生成过程：

python ximalaya\_xmsign.py  
# 或  
python xm-demo.py

## **6\. 注意事项**

* **Cookie 有效期：** 喜马拉雅的 Cookie 可能会过期，如果脚本无法正常工作，请尝试更新 .env 文件中的 XIMALAYA\_COOKIES。  
* **反爬机制：** 喜马拉雅可能会更新其反爬机制，导致部分功能失效。如果遇到问题，可能需要检查并更新代码中的请求头、参数或签名逻辑。  
* **VIP 内容：** 对于部分 VIP 专属内容，未登录或非 VIP 用户可能无法获取加密 URL。  
* **法律合规：** 请确保您的使用符合喜马拉雅的服务条款和相关法律法规。本项目仅供学习和研究目的，请勿用于非法用途。