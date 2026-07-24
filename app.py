import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from threading import Thread
import random
import os
import core

APP_TITLE = '批混剪工作室'

# ── 浅蓝渐变碳色配色 ──
BG        = '#0a1520'   # 深青黑底
BG_SIDEBAR= '#0c1a28'   # 侧栏深青
BG_INPUT  = '#122838'   # 输入框青蓝
BG_HOVER  = '#183048'   # 悬停
BG_CARD   = '#0e1e30'   # 卡片深青
FG        = '#a0dce8'   # 淡青文字
FG_DIM    = '#4a8090'   # 弱化青灰
FG_BRIGHT = '#d0f4ff'   # 亮青白
ACCENT    = '#00d4ff'   # 赛博亮青
ACCENT_HV = '#40e8ff'   # 亮青悬停
GREEN     = '#00ffa0'   # 赛博绿
ORANGE    = '#ffb860'   # 暖橙
RED       = '#ff4060'   # 赛博红
YELLOW    = '#ffe060'   # 赛博黄
BORDER    = '#1a4060'   # 青蓝边框
SEL_BG    = '#0a5080'   # 选中青
SCROLLBAR = '#1a3050'   # 滚动条

COLORS = {
    '白色': '#FFFFFF', '亮黄': '#FFE066', '珊瑚红': '#FF6B6B',
    '天蓝': '#6BA3FF', '青色': '#6BFFF0', '翠绿': '#6FD4A0',
    '暖橙': '#FFB366', '粉红': '#FF85B3', '浅紫': '#B388FF',
    '金色': '#FFD54F', '银灰': '#9E9E9E', '冷白': '#D8DEE9',
}

VIDEO_EXTS = ('*.mp4', '*.mkv', '*.mov', '*.avi', '*.webm', '*.flv')
AUDIO_EXTS = ('*.mp3', '*.wav', '*.aac', '*.m4a', '*.flac', '*.ogg')

scan_vid = lambda f: sorted(x for e in VIDEO_EXTS for x in f.glob(e))
scan_aud = lambda f: sorted(x for e in AUDIO_EXTS for x in f.glob(e))
scan_sub = lambda f: sorted(f.glob('*.srt')) + sorted(f.glob('*.SRT'))

KW_MAP = {
    'intro': ['片头', 'intro', 'opening', '开头'],
    'mid':   ['片中', 'mid', 'middle', 'body', '正片'],
    'outro': ['片尾', 'outro', 'ending', 'tail', '结尾'],
    'bg':    ['背景', 'bg', 'background'],
    'sub':   ['字幕', 'sub', 'subtitle', 'srt'],
    'music': ['音乐', 'music', 'audio', 'bgm'],
}


def scan_root(root):
    result = {}
    for child in root.iterdir():
        if not child.is_dir():
            continue
        nl = child.name.lower()
        for key, kws in KW_MAP.items():
            if key not in result and any(k in nl for k in kws):
                result[key] = child
                break
    return result


# ══════════════════════════════════════════
#  ttk 主题
# ══════════════════════════════════════════

def setup_theme(root):
    style = ttk.Style(root)
    style.theme_use('clam')

    style.configure('.', background=BG, foreground=FG, fieldbackground=BG_INPUT,
                    bordercolor=BORDER, troughcolor='#0a1828', selectbackground=SEL_BG,
                    selectforeground=FG_BRIGHT, font=('Microsoft YaHei UI', 10))

    style.configure('TFrame', background=BG)
    style.configure('Sidebar.TFrame', background=BG_SIDEBAR)
    style.configure('Card.TFrame', background=BG_CARD)
    style.configure('Top.TFrame', background='#080e18')

    style.configure('TLabel', background=BG, foreground=FG, font=('Microsoft YaHei UI', 10))
    style.configure('Header.TLabel', background='#080e18', foreground=FG_BRIGHT,
                    font=('Microsoft YaHei UI', 11, 'bold'))
    style.configure('Dim.TLabel', background=BG, foreground=FG_DIM, font=('Microsoft YaHei UI', 9))
    style.configure('Accent.TLabel', background=BG, foreground=ACCENT, font=('Microsoft YaHei UI', 10))
    style.configure('Sidebar.TLabel', background=BG_SIDEBAR, foreground=FG)
    style.configure('Card.TLabel', background=BG_CARD, foreground=FG)
    style.configure('CardHeader.TLabel', background=BG_CARD, foreground=FG_BRIGHT,
                    font=('Microsoft YaHei UI', 10, 'bold'))

    style.configure('TCheckbutton', background=BG, foreground=FG, font=('Microsoft YaHei UI', 10),
                    indicatorbackground=BG_INPUT, indicatorforeground=ACCENT)
    style.configure('Sidebar.TCheckbutton', background=BG_SIDEBAR)
    style.map('TCheckbutton', background=[('active', BG_HOVER)])

    style.configure('TButton', background=BG_INPUT, foreground=FG, borderwidth=1,
                    focuscolor=ACCENT, font=('Microsoft YaHei UI', 10))
    style.map('TButton', background=[('active', BG_HOVER), ('pressed', BORDER)])

    style.configure('Accent.TButton', background=ACCENT, foreground='white',
                    font=('Microsoft YaHei UI', 11, 'bold'), borderwidth=0)
    style.map('Accent.TButton', background=[('active', ACCENT_HV), ('disabled', '#404040')])

    style.configure('TScale', background=BG, troughcolor='#0a1828')
    style.map('TScale', background=[('active', ACCENT)])

    style.configure('TMenubutton', background=BG_INPUT, foreground=FG,
                    font=('Microsoft YaHei UI', 10), borderwidth=1)
    style.map('TMenubutton', background=[('active', BG_HOVER)])

    style.configure('Vertical.TScrollbar', background=SCROLLBAR, troughcolor=BG,
                    borderwidth=0, arrowcolor=FG_DIM)
    style.map('Vertical.TScrollbar', background=[('active', BORDER)])

    style.configure('TProgressbar', background=ACCENT, troughcolor='#0a1828', borderwidth=0)


# ══════════════════════════════════════════
#  素材目录行
# ══════════════════════════════════════════

class DirRow(ttk.Frame):
    def __init__(self, master, label, pick_cmd, idx, is_music=False, is_sub=False):
        super().__init__(master, style='Card.TFrame')
        self.pick_cmd = pick_cmd
        self.files = []
        self.is_music = is_music
        self.is_sub = is_sub
        self.enabled = tk.BooleanVar(value=True)
        self._chk = tk.Checkbutton(self, text='\u2611', variable=self.enabled,
                                    bg=BG_CARD, fg=ACCENT, selectcolor=BG_INPUT,
                                    activebackground=BG_CARD, highlightthickness=0,
                                    font=('Segoe UI Symbol', 13), width=2, anchor='w')
        self._chk.pack(side='left', padx=(8, 4))
        self._chk.configure(command=self._on_toggle)
        ttk.Label(self, text=label, width=7, anchor='w',
                  style='Card.TLabel').pack(side='left', padx=(0, 4))
        self.ent = tk.Entry(self, bg=BG_INPUT, fg=FG, insertbackground=FG_BRIGHT,
                            relief='flat', highlightthickness=1, highlightbackground=BORDER,
                            highlightcolor=ACCENT, font=('Microsoft YaHei UI', 9))
        self.ent.pack(side='left', padx=4, fill='x', expand=True)
        ttk.Button(self, text='选择', command=lambda: pick_cmd(self),
                   width=5).pack(side='left', padx=4)
        self.cnt = ttk.Label(self, text='0', style='Dim.TLabel', width=4)
        self.cnt.pack(side='left', padx=(2, 8))
        self.pack(fill='x', padx=4, pady=2)

    def _on_toggle(self):
        self._chk.configure(fg=ACCENT if self.enabled.get() else FG_DIM)

    def set_path(self, path):
        self.ent.delete(0, 'end')
        self.ent.insert(0, path)
        p = Path(path)
        if p.exists() and p.is_dir():
            self.files = scan_aud(p) if self.is_music else (scan_sub(p) if self.is_sub else scan_vid(p))
            self.cnt.configure(text=str(len(self.files)), foreground=ACCENT)
        else:
            self.files = []
            self.cnt.configure(text='0', foreground=FG_DIM)

    def get_files(self):
        return self.files if self.enabled.get() else []


# ══════════════════════════════════════════
#  可折叠分组
# ══════════════════════════════════════════

class Section(ttk.Frame):
    def __init__(self, master, title, default_open=True):
        super().__init__(master, style='Card.TFrame')
        self._open = default_open
        hdr = ttk.Frame(self, style='Card.TFrame')
        hdr.pack(fill='x')
        self._arrow = ttk.Label(hdr, text='\u25be' if default_open else '\u25b8',
                                style='Card.TLabel', width=2, font=('Consolas', 11))
        self._arrow.pack(side='left', padx=(10, 4), pady=8)
        ttk.Label(hdr, text=title, style='CardHeader.TLabel').pack(side='left', pady=8)
        self._sep = tk.Frame(self, bg=BORDER, height=1)
        self._sep.pack(fill='x', padx=10, pady=(0, 2))
        self._body = ttk.Frame(self, style='Card.TFrame')
        if default_open:
            self._body.pack(fill='both', expand=True)
        hdr.bind('<Button-1>', lambda e: self._toggle())
        self._arrow.bind('<Button-1>', lambda e: self._toggle())

    def _toggle(self):
        self._open = not self._open
        self._arrow.configure(text='\u25be' if self._open else '\u25b8')
        if self._open:
            self._body.pack(fill='both', expand=True)
        else:
            self._body.pack_forget()

    @property
    def body(self):
        return self._body


# ══════════════════════════════════════════
#  主窗口
# ══════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry('1280x860')
        self.minsize(1000, 700)
        self.configure(bg=BG)
        self.rows = {}
        setup_theme(self)
        self._build()

    def _build(self):
        # ===== 顶部栏 =====
        top = ttk.Frame(self, style='Top.TFrame')
        top.pack(fill='x')
        top_inner = ttk.Frame(top, style='Top.TFrame')
        top_inner.pack(fill='x', padx=16, pady=10)
        ttk.Label(top_inner, text=APP_TITLE, style='Header.TLabel').pack(side='left')
        ttk.Label(top_inner, text='v3', style='Dim.TLabel').pack(side='left', padx=(6, 0))

        btn_bar = ttk.Frame(top_inner, style='Top.TFrame')
        btn_bar.pack(side='right')
        ttk.Button(btn_bar, text='总扫描', command=self._scan).pack(side='left', padx=(0, 6))
        ttk.Button(btn_bar, text='刷新', command=self._refresh).pack(side='left', padx=(0, 12))
        self.scan_lbl = ttk.Label(btn_bar, text='未扫描', style='Dim.TLabel')
        self.scan_lbl.pack(side='left', padx=(0, 12))
        self.status_lbl = ttk.Label(btn_bar, text='就绪', style='Accent.TLabel')
        self.status_lbl.pack(side='left', padx=(0, 12))
        self.start_btn = ttk.Button(btn_bar, text='  \u25b6  开始合成  ', style='Accent.TButton',
                                    command=self._start)
        self.start_btn.pack(side='left', ipady=2)

        ttk.Separator(self, orient='horizontal').pack(fill='x')

        # ===== 中间左右分栏 =====
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # ── 左侧栏 ──
        sidebar = ttk.Frame(paned, style='Sidebar.TFrame')
        paned.add(sidebar, weight=1)

        canvas = tk.Canvas(sidebar, bg=BG_SIDEBAR, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(sidebar, orient='vertical', command=canvas.yview)
        scroll_frame = ttk.Frame(canvas, style='Sidebar.TFrame')
        scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(-1 * (e.delta // 120), 'units'))

        # 素材目录
        sec1 = Section(scroll_frame, '素材目录')
        sec1.pack(fill='x', padx=6, pady=(6, 4))
        b1 = sec1.body
        for i, (k, l) in enumerate([('intro', '片头'), ('mid', '片中'), ('outro', '片尾')]):
            self.rows[k] = DirRow(b1, l, self._pick_dir, i)
        for i, (k, l) in enumerate([('bg', '背景'), ('sub', '字幕')]):
            self.rows[k] = DirRow(b1, l, self._pick_dir, i + 3, is_sub=(k == 'sub'))
        self.rows['music'] = DirRow(b1, '背景音乐', self._pick_dir, 5, is_music=True)

        out_row = ttk.Frame(b1, style='Card.TFrame')
        out_row.pack(fill='x', padx=4, pady=2)
        ttk.Label(out_row, text='输出目录', width=7, anchor='w',
                  style='Card.TLabel').pack(side='left', padx=(8, 4))
        self.out_ent = tk.Entry(out_row, bg=BG_INPUT, fg=FG, insertbackground=FG_BRIGHT,
                                relief='flat', highlightthickness=1, highlightbackground=BORDER,
                                highlightcolor=ACCENT, font=('Microsoft YaHei UI', 9))
        self.out_ent.pack(side='left', padx=4, fill='x', expand=True)
        ttk.Button(out_row, text='选择', command=self._pick_out,
                   width=5).pack(side='left', padx=4)

        # 合成参数
        sec2 = Section(scroll_frame, '合成参数')
        sec2.pack(fill='x', padx=6, pady=4)
        b2 = sec2.body

        r = ttk.Frame(b2, style='Card.TFrame'); r.pack(fill='x', padx=8, pady=4)
        ttk.Label(r, text='混剪模式', style='Card.TLabel').pack(side='left')
        self.mode = tk.StringVar(value='sequential')
        self.seq_b = ttk.Button(r, text='顺序', command=lambda: self._set_mode('sequential'))
        self.seq_b.pack(side='left', padx=(8, 4))
        self.shuf_b = ttk.Button(r, text='乱序', command=lambda: self._set_mode('shuffle'))
        self.shuf_b.pack(side='left', padx=4)
        ttk.Label(r, text='数量', style='Card.TLabel').pack(side='left', padx=(16, 4))
        self.cnt_ent = tk.Entry(r, width=5, bg=BG_INPUT, fg=ACCENT, insertbackground=FG_BRIGHT,
                                relief='flat', highlightthickness=1, highlightbackground=BORDER,
                                highlightcolor=ACCENT, font=('Microsoft YaHei UI', 10))
        self.cnt_ent.pack(side='left', padx=4)
        ttk.Label(r, text='留空=全部', style='Dim.TLabel').pack(side='left', padx=4)

        r = ttk.Frame(b2, style='Card.TFrame'); r.pack(fill='x', padx=8, pady=4)
        ttk.Label(r, text='字幕颜色', style='Card.TLabel').pack(side='left')
        self.scol = tk.StringVar(value='白色')
        self._make_option(r, self.scol, list(COLORS.keys()), 6, self._upd_scol).pack(side='left', padx=(8, 2))
        self.scol_dot = tk.Label(r, text='\u25cf', fg=COLORS['白色'], bg=BG_CARD, font=('Arial', 12))
        self.scol_dot.pack(side='left', padx=2)
        ttk.Label(r, text='字体', style='Card.TLabel').pack(side='left', padx=(12, 4))
        self.sub_font = tk.Entry(r, width=10, bg=BG_INPUT, fg=FG, insertbackground=FG_BRIGHT,
                                 relief='flat', highlightthickness=1, highlightbackground=BORDER,
                                 highlightcolor=ACCENT, font=('Microsoft YaHei UI', 9))
        self.sub_font.pack(side='left', padx=2); self.sub_font.insert(0, 'Arial')
        ttk.Label(r, text='SRT格式', style='Dim.TLabel').pack(side='left', padx=6)

        r = ttk.Frame(b2, style='Card.TFrame'); r.pack(fill='x', padx=8, pady=4)
        ttk.Label(r, text='图片水印', style='Card.TLabel').pack(side='left')
        self.img_wm = tk.Entry(r, bg=BG_INPUT, fg=FG, insertbackground=FG_BRIGHT,
                               relief='flat', highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=ACCENT, font=('Microsoft YaHei UI', 9))
        self.img_wm.pack(side='left', padx=4, fill='x', expand=True)
        ttk.Button(r, text='选择', command=self._pick_wm, width=5).pack(side='left', padx=2)

        r = ttk.Frame(b2, style='Card.TFrame'); r.pack(fill='x', padx=8, pady=4)
        ttk.Label(r, text='字幕大小', style='Card.TLabel').pack(side='left')
        self.sub_size = tk.IntVar(value=68)
        self._make_slider(r, self.sub_size, 12, 120).pack(side='left', padx=8)
        ttk.Label(r, text='边距', style='Card.TLabel').pack(side='left', padx=(8, 0))
        self.sub_margin = tk.IntVar(value=60)
        self._make_slider(r, self.sub_margin, 0, 200).pack(side='left', padx=8)

        r = ttk.Frame(b2, style='Card.TFrame'); r.pack(fill='x', padx=8, pady=4)
        ttk.Label(r, text='文字水印', style='Card.TLabel').pack(anchor='nw', padx=0, pady=(0, 2))
        self.txt_wm = tk.Text(r, width=0, height=3, bg=BG_INPUT, fg=FG, insertbackground=FG_BRIGHT,
                              relief='flat', highlightthickness=1, highlightbackground=BORDER,
                              highlightcolor=ACCENT, font=('Microsoft YaHei UI', 10), wrap='word')
        self.txt_wm.pack(fill='x', padx=0, pady=(0, 4))

        r = ttk.Frame(b2, style='Card.TFrame'); r.pack(fill='x', padx=8, pady=4)
        ttk.Label(r, text='位置', style='Card.TLabel').pack(side='left')
        self.pos = tk.StringVar(value='右上')
        self._make_option(r, self.pos, ['左上', '中上', '右上', '左下', '中下', '右下', '居中'], 5).pack(side='left', padx=(8, 2))
        ttk.Label(r, text='颜色', style='Card.TLabel').pack(side='left', padx=(10, 0))
        self.tcol = tk.StringVar(value='白色')
        self._make_option(r, self.tcol, list(COLORS.keys()), 6, self._upd_tcol).pack(side='left', padx=(8, 2))
        self.tcol_dot = tk.Label(r, text='\u25cf', fg=COLORS['白色'], bg=BG_CARD, font=('Arial', 12))
        self.tcol_dot.pack(side='left', padx=2)
        ttk.Label(r, text='竖排', style='Card.TLabel').pack(side='left', padx=(10, 0))
        self.vert = tk.BooleanVar(value=False)
        tk.Checkbutton(r, text='', variable=self.vert, bg=BG_CARD, fg=ACCENT,
                       selectcolor=BG_INPUT, activebackground=BG_CARD, highlightthickness=0).pack(side='left', padx=4)

        r = ttk.Frame(b2, style='Card.TFrame'); r.pack(fill='x', padx=8, pady=4)
        self.tts_enabled = tk.BooleanVar(value=False)
        tk.Checkbutton(r, text='字幕转语音', variable=self.tts_enabled, bg=BG_CARD, fg=FG,
                       selectcolor=BG_INPUT, activebackground=BG_CARD, highlightthickness=0,
                       font=('Microsoft YaHei UI', 10)).pack(side='left')
        ttk.Label(r, text='音量', style='Card.TLabel').pack(side='left', padx=(16, 4))
        self.tts_volume = tk.DoubleVar(value=0.5)
        self._make_slider(r, self.tts_volume, 0.0, 1.0, 0.05, 140).pack(side='left', padx=4)
        ttk.Label(r, text='系统语音', style='Dim.TLabel').pack(side='left', padx=4)

        r = ttk.Frame(b2, style='Card.TFrame'); r.pack(fill='x', padx=8, pady=(4, 8))
        ttk.Label(r, text='水印大小', style='Card.TLabel').pack(side='left')
        self.wm_size = tk.IntVar(value=48)
        self._make_slider(r, self.wm_size, 12, 120).pack(side='left', padx=8)
        ttk.Label(r, text='透明度', style='Card.TLabel').pack(side='left', padx=(8, 0))
        self.wm_opacity = tk.DoubleVar(value=0.85)
        self._make_slider(r, self.wm_opacity, 0.1, 1.0, 0.05, 140).pack(side='left', padx=8)

        # ── 右侧日志面板 ──
        right = ttk.Frame(paned)
        paned.add(right, weight=2)

        log_hdr = ttk.Frame(right)
        log_hdr.pack(fill='x', padx=8, pady=(8, 4))
        ttk.Label(log_hdr, text='工作日志', style='Header.TLabel').pack(side='left')
        ttk.Button(log_hdr, text='清空', command=self._clear_log, width=5).pack(side='right')

        log_frame = ttk.Frame(right)
        log_frame.pack(fill='both', expand=True, padx=8, pady=(0, 8))
        self.log_box = tk.Text(log_frame, bg='#081018', fg=ACCENT, insertbackground=FG_BRIGHT,
                               relief='flat', font=('Consolas', 10), highlightthickness=1,
                               highlightbackground=BORDER, highlightcolor=ACCENT,
                               wrap='word', padx=10, pady=8, bd=0)
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_scroll.set)
        self.log_box.pack(side='left', fill='both', expand=True)
        log_scroll.pack(side='right', fill='y')
        self.log_box.configure(state='disabled')

        # ===== 底部状态栏 =====
        bottom = ttk.Frame(self, style='Top.TFrame')
        bottom.pack(fill='x', side='bottom')
        ttk.Separator(bottom, orient='horizontal').pack(fill='x')
        ttk.Label(bottom, text='就绪', style='Dim.TLabel').pack(side='left', padx=12, pady=4)

    # ── 辅助 ──
    def _make_option(self, parent, var, opts, w, cmd=None):
        m = tk.OptionMenu(parent, var, *opts, command=cmd)
        m.configure(bg=BG_INPUT, fg=FG, activebackground=BG_HOVER, activeforeground=FG_BRIGHT,
                    highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
                    font=('Microsoft YaHei UI', 9), width=w, relief='flat', bd=1)
        m['menu'].configure(bg=BG_CARD, fg=FG, activebackground=SEL_BG,
                            activeforeground='white', font=('Microsoft YaHei UI', 9))
        return m

    def _make_slider(self, parent, var, from_, to_, res=1, length=140):
        return tk.Scale(parent, from_=from_, to=to_, resolution=res, orient='horizontal',
                        variable=var, bg=BG_CARD, fg=FG_DIM, troughcolor='#0a1828',
                        highlightthickness=0, length=length, showvalue=True,
                        font=('Microsoft YaHei UI', 8), sliderrelief='flat',
                        activebackground=ACCENT, bd=0)

    # ── 回调 ──
    def _upd_scol(self, v): self.scol_dot.configure(fg=COLORS.get(v, '#FFF'))
    def _upd_tcol(self, v): self.tcol_dot.configure(fg=COLORS.get(v, '#FFF'))

    def log(self, msg):
        self.log_box.configure(state='normal')
        self.log_box.insert('end', msg + '\n')
        self.log_box.see('end')
        self.log_box.configure(state='disabled')

    def _clear_log(self):
        self.log_box.configure(state='normal')
        self.log_box.delete('1.0', 'end')
        self.log_box.configure(state='disabled')

    def _pick_dir(self, row):
        p = filedialog.askdirectory(title='选择音乐文件夹' if row.is_music else '选择目录')
        if p: row.set_path(p)

    def _pick_out(self):
        p = filedialog.askdirectory(title='选择输出目录')
        if p: self.out_ent.delete(0, 'end'); self.out_ent.insert(0, p)

    def _pick_wm(self):
        p = filedialog.askopenfilename(title='选择水印图片',
                                       filetypes=[('image', '*.png *.jpg *.jpeg *.webp')])
        if p: self.img_wm.delete(0, 'end'); self.img_wm.insert(0, p)

    def _set_mode(self, v):
        self.mode.set(v)
        if v == 'sequential':
            self.seq_b.configure(style='Accent.TButton')
            self.shuf_b.configure(style='TButton')
        else:
            self.shuf_b.configure(style='Accent.TButton')
            self.seq_b.configure(style='TButton')

    def _refresh(self):
        for r in self.rows.values():
            p = r.ent.get().strip()
            if p: r.set_path(p)
        self.log('已刷新')

    def _scan(self):
        root = filedialog.askdirectory(title='选择根目录')
        if not root: return
        self.log(f'扫描: {root}')
        found = scan_root(Path(root))
        mapped = []
        for k, folder in found.items():
            if k == 'output':
                self.out_ent.delete(0, 'end')
                self.out_ent.insert(0, str(folder))
                mapped.append(f'output={folder.name}')
                continue
            if k in self.rows:
                self.rows[k].set_path(str(folder))
                self.rows[k].enabled.set(True)
                mapped.append(f'{k}={folder.name}')
        self.scan_lbl.configure(text=f'发现 {len(found)} 个目录')
        self.log(f"完成: {', '.join(mapped) if mapped else '未匹配'}")

    def _pos_key(self):
        return {'右上': 'right_top', '左上': 'left_top', '中上': 'center_top',
                '右下': 'right_bottom', '左下': 'left_bottom', '中下': 'center_bottom',
                '居中': 'center'}.get(self.pos.get(), 'right_top')

    def _get_wm_text(self):
        raw = self.txt_wm.get('1.0', 'end').strip()
        if not raw:
            return ''
        if self.vert.get():
            raw = ''.join(ch for ch in raw if ch not in ('\r', '\n', ' '))
            return '\n'.join(raw)
        return raw.replace('\r\n', '\n').replace('\r', '\n')

    def _start(self):
        self.log('检查参数...')
        self.status_lbl.configure(text='检查参数...')
        try:
            self.log(f'FFmpeg: {core.ffmpeg_cmd()}')
        except Exception as e:
            self.log(f'FFmpeg error: {e}')
            messagebox.showerror('错误', '未找到 FFmpeg')
            return
        try:
            intros = self.rows['intro'].get_files()
            if not intros:
                messagebox.showwarning('提示', '请先选择片头目录')
                return
            mids = self.rows['mid'].get_files()
            outros = self.rows['outro'].get_files()
            subs = self.rows['sub'].get_files()
            bgs = self.rows['bg'].get_files()
            musics = self.rows['music'].get_files()
            self.log(f'片头:{len(intros)} 片中:{len(mids)} 片尾:{len(outros)} 字幕:{len(subs)} 背景:{len(bgs)} 音乐:{len(musics)}')
            out_dir = Path(self.out_ent.get().strip()) if self.out_ent.get().strip() else intros[0].parent / 'output'
            bg = bgs[0] if bgs else None
            iw = Path(self.img_wm.get().strip()) if self.img_wm.get().strip() else None
            tw = self._get_wm_text()
            tc = COLORS.get(self.tcol.get(), '#FFFFFF').lstrip('#')
            sc = COLORS.get(self.scol.get(), '#FFFFFF').lstrip('#')

            combos = core.make_combinations(intros, mids, outros, self.mode.get())
            cs = self.cnt_ent.get().strip()
            tc_n = int(cs) if cs else len(combos)
            if tc_n == 1:
                combos = combos[:1]
            elif tc_n < len(combos):
                combos = combos[:tc_n]
            elif tc_n > len(combos):
                orig = list(combos)
                while len(combos) < tc_n:
                    combos.append(random.choice(orig))
            total = len(combos)
            self.log(f'合成 {total} 个视频...')
            self.status_lbl.configure(text='合成中...')
            self.start_btn.configure(state='disabled', text='  合成中...  ')

            def run():
                try:
                    for idx, combo in enumerate(combos, 1):
                        sub = None
                        if subs:
                            cand = [s for s in subs if s.stem == combo['intro'].stem]
                            sub = cand[0] if cand else subs[(idx - 1) % len(subs)]
                        music = random.choice(musics) if musics else None
                        self.log(f'[{idx}/{total}] {combo["intro"].name}' + (f' \u266a{music.name}' if music else ''))
                        self.status_lbl.configure(text=f'合成中 {idx}/{total}...')
                        core.process_one(
                            combo['intro'], combo['mid'], combo['outro'],
                            out_dir / f'output_{idx:03d}.mp4',
                            iw, tw, self._pos_key(), sub, music, bg,
                            sc, self.sub_size.get(), self.sub_font.get().strip() or 'Arial', self.sub_margin.get(),
                            tc, self.wm_size.get(), self.wm_opacity.get(),
                            self.tts_enabled.get(), self.tts_volume.get(),
                        )
                        self.log(f'[{idx}/{total}] 完成')
                    self.log(f'全部完成！共 {total} 个')
                    self.status_lbl.configure(text=f'完成！共 {total} 个视频')
                    messagebox.showinfo('完成', f'共 {total} 个视频')
                    try:
                        os.startfile(str(out_dir))
                    except Exception:
                        pass
                except Exception as e:
                    self.log(f'错误: {e}')
                    self.status_lbl.configure(text='合成出错')
                    messagebox.showerror('错误', str(e))
                finally:
                    self.start_btn.configure(state='normal', text='  \u25b6  开始合成  ')
                    self.status_lbl.configure(text='就绪')

            Thread(target=run, daemon=True).start()
        except Exception as e:
            self.log(f'参数错误: {e}')
            self.status_lbl.configure(text='参数错误')
            messagebox.showerror('错误', str(e))


if __name__ == '__main__':
    App().mainloop()