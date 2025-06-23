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
import tkinter.ttk as ttk

class XimalayaGUI:
    def __init__(self, root, default_download_dir=None):
        self.root = root
        self.default_download_dir = default_download_dir
        self.root.title('喜马拉雅批量下载工具')
        self.root.geometry('800x600')
        self._init_widgets()
        self.setup_log_tags()

    def _init_widgets(self):
        # 统一宽度
        label_width = 10
        entry_width = 32
        frame_width = 520
        # 专辑ID输入
        tk.Label(self.root, text='专辑ID:', width=label_width, anchor='w').grid(row=0, column=0, sticky='w')
        self.album_id_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.album_id_var, width=entry_width).grid(row=0, column=1, sticky='w')
        # trackID输入
        tk.Label(self.root, text='音频ID:', width=label_width, anchor='w').grid(row=1, column=0, sticky='w')
        self.track_id_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.track_id_var, width=entry_width).grid(row=1, column=1, sticky='w')
        # 操作按钮
        btn_frame = tk.Frame(self.root, width=frame_width)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky='w', pady=10)
        tk.Button(btn_frame, text='获取专辑信息', width=14, command=self.run_album_info).pack(side='left', padx=5)
        tk.Button(btn_frame, text='下载专辑', width=14, command=self.run_album_download).pack(side='left', padx=5)
        tk.Button(btn_frame, text='下载单曲', width=14, command=self.run_track_download).pack(side='left', padx=5)
        # 专辑信息展示区
        info_frame = tk.LabelFrame(self.root, text='专辑信息', padx=10, pady=5, width=frame_width)
        info_frame.grid(row=4, column=0, columnspan=2, sticky='nw', padx=10, pady=5)
        self.album_title_var = tk.StringVar()
        self.album_create_var = tk.StringVar()
        self.album_update_var = tk.StringVar()
        self.album_count_var = tk.StringVar()
        # 封面最上，固定像素区域，居中
        self.cover_frame = tk.Frame(info_frame, width=150, height=150, bg='#f0f0f0')
        self.cover_frame.grid_propagate(False)  # 禁止frame随内容缩放
        self.cover_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky='n')
        self.cover_label = tk.Label(self.cover_frame, anchor='center', bg='#f0f0f0', relief='groove')
        self.cover_label.place(relx=0.5, rely=0.5, anchor='center')
        # 标题
        tk.Label(info_frame, text='标题:', width=label_width, anchor='w').grid(row=1, column=0, sticky='w')
        tk.Label(info_frame, textvariable=self.album_title_var, wraplength=300, anchor='w', justify='left', width=entry_width).grid(row=1, column=1, sticky='w')
        # 创建时间
        tk.Label(info_frame, text='创建时间:', width=label_width, anchor='w').grid(row=2, column=0, sticky='w')
        tk.Label(info_frame, textvariable=self.album_create_var, width=entry_width, anchor='w').grid(row=2, column=1, sticky='w')
        # 更新时间
        tk.Label(info_frame, text='更新时间:', width=label_width, anchor='w').grid(row=3, column=0, sticky='w')
        tk.Label(info_frame, textvariable=self.album_update_var, width=entry_width, anchor='w').grid(row=3, column=1, sticky='w')
        # 曲目数量
        tk.Label(info_frame, text='曲目数量:', width=label_width, anchor='w').grid(row=4, column=0, sticky='w')
        tk.Label(info_frame, textvariable=self.album_count_var, anchor='w', justify='left', width=entry_width).grid(row=4, column=1, sticky='w')
        # 简介移到最下
        tk.Label(info_frame, text='简介:', width=label_width, anchor='nw').grid(row=5, column=0, sticky='nw')
        self.intro_text = tk.Text(info_frame, width=entry_width, height=5, wrap='word')
        self.intro_text.grid(row=5, column=1, sticky='w')
        self.intro_text.config(state='disabled')
        # 下载进度区（进度条）
        progress_frame = tk.LabelFrame(self.root, text='下载进度', padx=10, pady=5, width=frame_width)
        progress_frame.grid(row=5, column=0, columnspan=2, sticky='nw', padx=10, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=frame_width-213)
        self.progress_bar.grid(row=0, column=0, sticky='w', padx=5, columnspan=2)
        self.progress_label = tk.Label(progress_frame, text='', anchor='w', justify='left', width=entry_width+label_width)
        self.progress_label.grid(row=1, column=0, sticky='w', padx=5, columnspan=2)
        # 日志输出区
        tk.Label(self.root, text='日志输出:').grid(row=0, column=2, sticky='nw', pady=5)
        self.log_text = scrolledtext.ScrolledText(self.root, width=60, height=42, state='disabled')
        self.log_text.grid(row=1, column=2, rowspan=6, padx=10, sticky='nw')
        # 下载延迟输入
        tk.Label(self.root, text='下载延迟(秒):', width=label_width, anchor='w').grid(row=3, column=0, sticky='w')
        self.delay_var = tk.StringVar(value='3')
        tk.Entry(self.root, textvariable=self.delay_var, width=entry_width).grid(row=3, column=1, sticky='w')
        # 自适应拉伸
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(6, weight=1)

    def log(self, msg, level='info'):
        # 屏蔽下载百分比进度的日志（如“下载进度: xx%”）
        if isinstance(msg, str) and msg.strip().startswith('下载进度:'):
            return
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
        target_size = (150, 150)
        if not url:
            self.cover_label.config(image='', text='无封面')
            return
        try:
            response = requests.get(url, timeout=10)
            img_data = response.content
            img = Image.open(BytesIO(img_data)).convert('RGBA')
            # 保持比例缩放并居中填充白底
            img.thumbnail(target_size, Image.LANCZOS)
            bg = Image.new('RGBA', target_size, (255, 255, 255, 255))
            offset = ((target_size[0] - img.width) // 2, (target_size[1] - img.height) // 2)
            bg.paste(img, offset, img if img.mode == 'RGBA' else None)
            self.cover_imgtk = ImageTk.PhotoImage(bg)
            self.cover_label.config(image=self.cover_imgtk, text='')
        except Exception:
            self.cover_label.config(image='', text='加载失败')

    def set_progress(self, current, total, filename=None):
        percent = (current / total * 100) if total else 0
        self.progress_var.set(percent)
        if filename:
            self.progress_label.config(text=f'({current}/{total}) {filename}')
        else:
            self.progress_label.config(text=f'({current}/{total})')

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
            def progress_hook(current, total, filename=None):
                self.root.after(0, lambda: self.set_progress(current, total, filename))
            AlbumDownloader(album_id, log_func=self.log, delay=delay, save_dir=self.default_download_dir, progress_func=progress_hook).download_album()
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
