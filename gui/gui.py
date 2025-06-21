import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import os
import re

from fetcher.album_fetcher import fetch_album
from fetcher.track_fetcher import fetch_album_tracks, fetch_track_crypted_url
from downloader.downloader import M4ADownloader
from utils.utils import decrypt_url
from PIL import Image, ImageTk
import requests
from io import BytesIO
from downloader.album_download import AlbumDownloader

class XimalayaDownloader:
    """
    统一封装下载相关功能，便于后续扩展和调用。
    """
    def __init__(self, log_func=print, default_download_dir=None):
        self.log = log_func
        self.default_download_dir = default_download_dir

    def fetch_album_info(self, album_id):
        album = fetch_album(album_id)
        if not album:
            self.log('获取专辑信息失败')
            return None
        return album

    def fetch_tracks(self, album_id, page=1, page_size=20):
        return fetch_album_tracks(album_id, page, page_size)

    def fetch_all_tracks(self, album_id, page_size=20):
        all_tracks = []
        page = 1
        while True:
            tracks = fetch_album_tracks(album_id, page, page_size)
            if not tracks:
                break
            all_tracks.extend(tracks)
            if len(tracks) < page_size:
                break
            page += 1
        return all_tracks

    def download_album(self, album_id, delay=0):
        AlbumDownloader(album_id, log_func=self.log, delay=delay, save_dir=self.default_download_dir).download_album()

    def download_track(self, track_id, album_id=None, filename=None):
        try:
            crypted_url = fetch_track_crypted_url(int(track_id), album_id)
        except TypeError:
            crypted_url = fetch_track_crypted_url(int(track_id), 0)
        if not crypted_url:
            self.log('未获取到加密URL')
            return
        url = decrypt_url(crypted_url)
        if not filename:
            filename = f'{track_id}.m4a'
        downloader = M4ADownloader()
        self.log(f'正在下载: {filename}')
        downloader.download_m4a(url, filename)
        self.log('下载完成')

class XimalayaGUI:
    def __init__(self, root, default_download_dir=None):
        self.root = root
        if default_download_dir:
            self.default_download_dir = default_download_dir
        else:
            import sys
            if hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
            else:
                base_dir = os.getcwd()
            self.default_download_dir = os.path.join(base_dir, 'AudioBook')
        self.root.title('喜马拉雅批量下载工具')
        self.root.geometry('900x600')

        # 专辑ID输入
        tk.Label(root, text='专辑ID:').grid(row=0, column=0, sticky='e')
        self.album_id_var = tk.StringVar()
        tk.Entry(root, textvariable=self.album_id_var, width=20).grid(row=0, column=1, sticky='w')

        # trackID输入
        tk.Label(root, text='音频ID:').grid(row=1, column=0, sticky='e')
        self.track_id_var = tk.StringVar()
        tk.Entry(root, textvariable=self.track_id_var, width=20).grid(row=1, column=1, sticky='w')

        # 操作按钮（优化布局，全部放在一行，跨两列，居左对齐）
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky='w', pady=10)
        tk.Button(btn_frame, text='获取专辑信息', command=self.run_album_info).pack(side='left', padx=5)
        tk.Button(btn_frame, text='下载专辑', command=self.run_album_download).pack(side='left', padx=5)
        tk.Button(btn_frame, text='下载单曲', command=self.run_track_download).pack(side='left', padx=5)

        # 专辑信息展示区（放在左侧，输入区和按钮下方，日志区右侧）
        info_frame = tk.LabelFrame(root, text='专辑信息', padx=10, pady=5)
        info_frame.grid(row=4, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        self.album_title_var = tk.StringVar()
        self.album_intro_var = tk.StringVar()
        self.album_create_var = tk.StringVar()
        self.album_update_var = tk.StringVar()
        self.album_count_var = tk.StringVar()
        tk.Label(info_frame, text='标题:').grid(row=0, column=0, sticky='e')
        tk.Label(info_frame, textvariable=self.album_title_var, wraplength=200, anchor='w', justify='left').grid(row=0, column=1, sticky='w')
        tk.Label(info_frame, text='简介:').grid(row=1, column=0, sticky='ne')
        self.intro_text = tk.Text(info_frame, width=28, height=5, wrap='word')
        self.intro_text.grid(row=1, column=1, sticky='w')
        self.intro_text.config(state='disabled')
        tk.Label(info_frame, text='创建时间:').grid(row=2, column=0, sticky='e')
        tk.Label(info_frame, textvariable=self.album_create_var).grid(row=2, column=1, sticky='w')
        tk.Label(info_frame, text='更新时间:').grid(row=3, column=0, sticky='e')
        tk.Label(info_frame, textvariable=self.album_update_var).grid(row=3, column=1, sticky='w')
        tk.Label(info_frame, text='封面:').grid(row=4, column=0, sticky='e')
        self.cover_label = tk.Label(info_frame)
        self.cover_label.grid(row=4, column=1, rowspan=2, padx=5, pady=5)
        tk.Label(info_frame, text='曲目数量:').grid(row=5, column=0, sticky='e')
        tk.Label(info_frame, textvariable=self.album_count_var, anchor='w', justify='left').grid(row=5, column=1, sticky='w')

        # 音频信息展示区
        track_frame = tk.LabelFrame(root, text='音频信息', padx=10, pady=5)
        track_frame.grid(row=5, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        self.track_title_var = tk.StringVar()
        self.track_url_var = tk.StringVar()
        tk.Label(track_frame, text='标题:').grid(row=0, column=0, sticky='e')
        tk.Label(track_frame, textvariable=self.track_title_var, wraplength=200, anchor='w', justify='left').grid(row=0, column=1, sticky='w')
        tk.Label(track_frame, text='播放地址:').grid(row=1, column=0, sticky='e')
        tk.Entry(track_frame, textvariable=self.track_url_var, width=28, state='readonly').grid(row=1, column=1, sticky='w')

        # 日志输出区放在右侧，占据更多空间
        tk.Label(root, text='日志输出:').grid(row=0, column=2, sticky='nw', pady=5)
        self.log_text = scrolledtext.ScrolledText(root, width=60, height=28, state='normal')
        self.log_text.grid(row=1, column=2, rowspan=6, padx=10, sticky='nsew')

        # 下载延迟输入
        tk.Label(root, text='下载延迟(秒):').grid(row=3, column=0, sticky='e')
        self.delay_var = tk.StringVar(value='3')
        tk.Entry(root, textvariable=self.delay_var, width=8).grid(row=3, column=1, sticky='w')

        # 使日志区和专辑信息区自适应拉伸
        root.grid_columnconfigure(2, weight=1)
        root.grid_rowconfigure(6, weight=1)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)

    def run_in_thread(self, func):
        threading.Thread(target=func, daemon=True).start()

    def show_cover_image(self, url):
        if not url:
            self.cover_label.config(image='', text='无封面')
            return
        try:
            response = requests.get(url, timeout=10)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img = img.resize((100, 100))
            self.cover_imgtk = ImageTk.PhotoImage(img)
            self.cover_label.config(image=self.cover_imgtk, text='')
        except Exception as e:
            self.cover_label.config(image='', text='加载失败')

    def run_album_info(self):
        album_id = self.album_id_var.get().strip()
        if not album_id:
            messagebox.showwarning('提示', '请输入专辑ID')
            return
        self.log(f'获取专辑信息: {album_id}')
        def task():
            album = fetch_album(int(album_id))
            if album:
                self.album_title_var.set(album.albumTitle)
                intro = re.sub('<[^<]+?>', '', album.richIntro or '')
                self.intro_text.config(state='normal')
                self.intro_text.delete('1.0', tk.END)
                self.intro_text.insert(tk.END, intro)
                self.intro_text.config(state='disabled')
                self.album_create_var.set(album.createDate)
                self.album_update_var.set(album.updateDate)
                cover_url = album.cover if album.cover else ''
                try:
                    tracks = fetch_album_tracks(int(album_id), 1, 1)
                    total_count = tracks[0].totalCount if tracks and tracks[0].totalCount else ''
                except Exception:
                    total_count = ''
                self.album_count_var.set(str(total_count))
                self.show_cover_image(cover_url)
                self.log(f'获取专辑成功: {album.albumTitle}')
            else:
                self.album_title_var.set('')
                self.intro_text.config(state='normal')
                self.intro_text.delete('1.0', tk.END)
                self.intro_text.config(state='disabled')
                self.album_create_var.set('')
                self.album_update_var.set('')
                self.album_count_var.set('')
                self.show_cover_image('')
                self.log('获取专辑信息失败')
        self.run_in_thread(task)

    def run_album_download(self):
        album_id = self.album_id_var.get().strip()
        if not album_id:
            messagebox.showwarning('提示', '请输入专辑ID')
            return
        # 从UI获取延迟参数
        try:
            delay = float(self.delay_var.get())
            if delay < 0:
                delay = 0
        except Exception:
            delay = 1
        self.download_delay = delay
        self.log(f'下载专辑: {album_id} (延迟: {delay}s)')
        def task():
            # 使用默认下载目录
            AlbumDownloader(album_id, log_func=self.log, delay=delay, save_dir=self.default_download_dir).download_album()
        self.run_in_thread(task)

    def run_track_download(self):
        track_id = self.track_id_var.get().strip()
        if not track_id:
            messagebox.showwarning('提示', '请输入音频ID')
            return
        self.log(f'下载单曲: track_id={track_id}')
        def task():
            # 只用track_id下载，不再依赖album_id
            # 这里需要用户的track_fetcher.py的fetch_track_crypted_url支持只用track_id获取url
            # 若原函数需要album_id，可尝试用0或None等默认值
            try:
                crypted_url = fetch_track_crypted_url(int(track_id), None)
            except TypeError:
                crypted_url = fetch_track_crypted_url(int(track_id), 0)
            if not crypted_url:
                self.log('未获取到加密URL')
                self.track_title_var.set('')
                self.track_url_var.set('')
                return
            url = decrypt_url(crypted_url)
            # 获取音频标题
            title = ''
            try:
                tracks = fetch_album_tracks(0, 1, 1)  # 这里0仅为防止报错，实际不会用到
            except Exception:
                tracks = []
            # 尝试通过track_id获取标题（如有API可用）
            # 由于fetch_album_tracks需要album_id，无法直接查找标题，默认用ID
            self.track_title_var.set(title or f'ID:{track_id}')
            self.track_url_var.set(url)
            filename = f'{title or track_id}.m4a'
            downloader = M4ADownloader()
            self.log(f'正在下载: {filename}')
            downloader.download_m4a(url, filename)
            self.log('下载完成')
        self.run_in_thread(task)

if __name__ == '__main__':
    root = tk.Tk()
    app = XimalayaGUI(root)
    root.mainloop()
