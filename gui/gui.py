import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import re
from PIL import Image, ImageTk
import requests
from io import BytesIO
from fetcher.album_fetcher import fetch_album
from fetcher.track_fetcher import fetch_album_tracks
from downloader.album_download import AlbumDownloader
from downloader.single_track_download import download_single_track

class XimalayaGUI:
    def __init__(self, root, default_download_dir=None):
        self.root = root
        self.default_download_dir = default_download_dir
        self.root.title('喜马拉雅批量下载工具')
        self.root.geometry('900x600')
        self._init_widgets()
        self.setup_log_tags()

    def _init_widgets(self):
        # 专辑ID输入
        tk.Label(self.root, text='专辑ID:').grid(row=0, column=0, sticky='e')
        self.album_id_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.album_id_var, width=20).grid(row=0, column=1, sticky='w')
        # trackID输入
        tk.Label(self.root, text='音频ID:').grid(row=1, column=0, sticky='e')
        self.track_id_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.track_id_var, width=20).grid(row=1, column=1, sticky='w')
        # 操作按钮
        btn_frame = tk.Frame(self.root)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky='w', pady=10)
        tk.Button(btn_frame, text='获取专辑信息', command=self.run_album_info).pack(side='left', padx=5)
        tk.Button(btn_frame, text='下载专辑', command=self.run_album_download).pack(side='left', padx=5)
        tk.Button(btn_frame, text='下载单曲', command=self.run_track_download).pack(side='left', padx=5)
        # 专辑信息展示区
        info_frame = tk.LabelFrame(self.root, text='专辑信息', padx=10, pady=5)
        info_frame.grid(row=4, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        self.album_title_var = tk.StringVar()
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
        track_frame = tk.LabelFrame(self.root, text='音频信息', padx=10, pady=5)
        track_frame.grid(row=5, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        self.track_title_var = tk.StringVar()
        self.track_url_var = tk.StringVar()
        tk.Label(track_frame, text='标题:').grid(row=0, column=0, sticky='e')
        tk.Label(track_frame, textvariable=self.track_title_var, wraplength=200, anchor='w', justify='left').grid(row=0, column=1, sticky='w')
        tk.Label(track_frame, text='播放地址:').grid(row=1, column=0, sticky='e')
        tk.Entry(track_frame, textvariable=self.track_url_var, width=28, state='readonly').grid(row=1, column=1, sticky='w')
        # 日志输出区
        tk.Label(self.root, text='日志输出:').grid(row=0, column=2, sticky='nw', pady=5)
        self.log_text = scrolledtext.ScrolledText(self.root, width=60, height=28, state='disabled')
        self.log_text.grid(row=1, column=2, rowspan=6, padx=10, sticky='nsew')
        # 下载延迟输入
        tk.Label(self.root, text='下载延迟(秒):').grid(row=3, column=0, sticky='e')
        self.delay_var = tk.StringVar(value='3')
        tk.Entry(self.root, textvariable=self.delay_var, width=8).grid(row=3, column=1, sticky='w')
        # 自适应拉伸
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(6, weight=1)

    def log(self, msg, level='info'):
        if callable(getattr(msg, '__call__', None)):
            msg = str(msg)
        def append():
            self.log_text.config(state='normal')
            tag = level if level in ('info', 'warning', 'error') else 'info'
            self.log_text.insert(tk.END, msg + '\n', tag)
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        self.log_text.after(0, append)

    def log_info(self, msg):
        self.log(msg, level='info')
    def log_warning(self, msg):
        self.log(msg, level='warning')
    def log_error(self, msg):
        self.log(msg, level='error')

    def setup_log_tags(self):
        self.log_text.tag_config('info', foreground='black')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('error', foreground='red')

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
        except Exception:
            self.cover_label.config(image='', text='加载失败')

    def run_album_info(self):
        album_id = self.album_id_var.get().strip()
        if not album_id:
            self.log_warning('请输入专辑ID')
            messagebox.showwarning('提示', '请输入专辑ID')
            return
        self.log_info(f'获取专辑信息: {album_id}')
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
                self.log_info(f'获取专辑成功: {album.albumTitle}')
            else:
                self.album_title_var.set('')
                self.intro_text.config(state='normal')
                self.intro_text.delete('1.0', tk.END)
                self.intro_text.config(state='disabled')
                self.album_create_var.set('')
                self.album_update_var.set('')
                self.album_count_var.set('')
                self.show_cover_image('')
                self.log_error('获取专辑信息失败')
        self.run_in_thread(task)

    def run_album_download(self):
        album_id = self.album_id_var.get().strip()
        if not album_id:
            self.log_warning('请输入专辑ID')
            messagebox.showwarning('提示', '请输入专辑ID')
            return
        try:
            delay = float(self.delay_var.get())
            if delay < 0:
                delay = 0
        except Exception:
            delay = 1
        self.download_delay = delay
        self.log_info(f'下载专辑: {album_id} (延迟: {delay}s)')
        def task():
            AlbumDownloader(album_id, log_func=self.log, delay=delay, save_dir=self.default_download_dir).download_album()
        self.run_in_thread(task)

    def run_track_download(self):
        track_id = self.track_id_var.get().strip()
        if not track_id:
            self.log_warning('请输入音频ID')
            messagebox.showwarning('提示', '请输入音频ID')
            return
        self.log_info(f'下载单曲: track_id={track_id}')
        def task():
            download_single_track(track_id, log_func=self.log, save_dir=self.default_download_dir)
        self.run_in_thread(task)

if __name__ == '__main__':
    root = tk.Tk()
    app = XimalayaGUI(root)
    root.mainloop()
