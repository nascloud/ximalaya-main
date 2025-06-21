# 喜马拉雅音频批量下载工具文档

## 1. 项目简介

本项目为喜马拉雅音频平台的批量下载与管理工具，基于 Python 实现，支持专辑音频的批量获取、解密与下载，适合个人备份、学习与研究用途。

## 2. 主要功能

- **专辑批量下载**：支持通过专辑 ID 批量获取并下载全部音频，支持断点续传。
- **多线程下载**：可配置线程数，大幅提升下载速度。
- **音频 URL 解密**：自动解密加密的音频播放链接。
- **收听历史获取**：可获取个人账号的收听历史（需配置 Cookie）。
- **单曲信息抓取**：支持通过 trackId 获取单个音频的详细信息。
- **API 签名生成**：内置 xm-sign 生成逻辑，适配新版接口。
- **图形界面支持**：集成简单 GUI，便于操作。

## 3. 目录结构

```
ximalaya-main/
├── downloader/           # 下载核心模块
│   ├── album_download.py
│   └── downloader.py
├── fetcher/              # 数据抓取与解析
│   ├── album_fetcher.py
│   ├── history_fetch.py
│   └── track_fetcher.py
├── gui/                  # 图形界面
│   └── gui.py
├── utils/                # 工具函数与签名生成
│   ├── utils.py
│   └── ximalaya_xmsign.py
├── main.py               # 启动入口（含 GUI）
├── xm-demo.py            # xm-sign 生成示例
├── requirements.txt      # 依赖库
└── README.md             # 项目说明
```

## 4. 环境准备

- Python 3.8 及以上
- pip

安装依赖：

```shell
pip install -r requirements.txt
```

## 5. Cookie 配置（如需获取收听历史或下载 VIP 内容）

1. 登录喜马拉雅网页版。
2. 打开开发者工具（F12），切换到 Network。
3. 刷新页面，找到对 https://www.ximalaya.com/revision/track/history/listen 的请求。
4. 复制请求 Headers 里的 Cookie 字段。
5. 在项目根目录新建 .env 文件，内容如下：
   ```
   XIMALAYA_COOKIES="<你的Cookie内容>"
   ```

## 6. 使用方法

### 6.1 图形界面启动

推荐使用 GUI 操作，支持专辑批量下载、路径选择等：

```shell
python main.py
```

### 6.2 命令行批量下载专辑

```shell
python fetcher/album_fetcher.py --album_id <专辑ID> [--start_page 1] [--end_page N] [--threads 4]
```
- 支持断点续传和多线程。

### 6.3 单曲信息抓取

```shell
python fetcher/track_fetcher.py --track_id <音频ID> [--album_id <专辑ID>]
```

### 6.4 多线程下载单个音频

```shell
python downloader/downloader.py --url <音频URL> --output <保存文件名> [--threads 8]
```

### 6.5 获取收听历史

```shell
python fetcher/history_fetch.py
```
- 需先配置 Cookie。

### 6.6 API 签名测试

```shell
python utils/ximalaya_xmsign.py
# 或
python xm-demo.py
```

## 7. 注意事项

- **Cookie 有效期有限，失效请重新获取。**
- **部分 VIP 内容需账号权限。**
- **请勿用于商业或非法用途，仅供学习交流。**
- **如遇接口变动或反爬升级，请关注项目更新。**

## 8. 常见问题

- 下载速度慢？请尝试增加线程数。
- 下载失败？请检查 Cookie、专辑 ID 是否正确，或接口是否变动。
- 其他问题请提交 issue 或自行调试。