# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os, sys, shutil, subprocess

def resource_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def mksc(target, lnk, wd=""):
    d = wd if wd else os.path.dirname(target)
    cmd_list = [
        "$ws = New-Object -ComObject WScript.Shell",
        "$sc = $ws.CreateShortcut(r'" + lnk + "')",
        "$sc.TargetPath = r'" + target + "'",
        "$sc.WorkingDirectory = r'" + d + "'",
        "$sc.Save()"
    ]
    subprocess.run(["powershell", "-Command", "; ".join(cmd_list)], capture_output=True)

WORK_FOLDERS = ["片头", "片中", "片尾", "背景", "背景音乐", "字幕", "输出目录"]

class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("批混剪工作室 - 安装向导")
        self.geometry("560x460")
        self.resizable(False, False)
        self.configure(bg="#f5f7fa")
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg="#1565c0", height=90)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="批混剪工作室",
                 font=("Microsoft YaHei UI", 22, "bold"), fg="white", bg="#1565c0").pack(expand=True)
        body = tk.Frame(self, bg="#f5f7fa", padx=32, pady=18)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="欢迎安装 批混剪工作室 v3",
                 font=("Microsoft YaHei UI", 13, "bold"), bg="#f5f7fa", fg="#212121").pack(anchor="w")
        tk.Label(body, text="视频批量混剪工具",
                 font=("Microsoft YaHei UI", 9), bg="#f5f7fa", fg="#757575").pack(anchor="w", pady=(4, 14))
        tk.Label(body, text="安装路径",
                 font=("Microsoft YaHei UI", 10, "bold"), bg="#f5f7fa", fg="#424242").pack(anchor="w")
        path_row = tk.Frame(body, bg="#f5f7fa")
        path_row.pack(fill="x", pady=(4, 12))
        dp = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "批混剪工作室")
        self.path_var = tk.StringVar(value=dp)
        tk.Entry(path_row, textvariable=self.path_var, font=("Microsoft YaHei UI", 10),
                 bg="white", relief="solid", width=38).pack(side="left", fill="x", expand=True)
        tk.Button(path_row, text="浏览...", command=self._browse,
                  font=("Microsoft YaHei UI", 9), relief="groove").pack(side="left", padx=(8, 0))
        self.shortcut_var = tk.BooleanVar(value=True)
        tk.Checkbutton(body, text="创建桌面快捷方式", variable=self.shortcut_var,
                       font=("Microsoft YaHei UI", 10), bg="#f5f7fa").pack(anchor="w", pady=2)
        self.startmenu_var = tk.BooleanVar(value=True)
        tk.Checkbutton(body, text="创建开始菜单快捷方式", variable=self.startmenu_var,
                       font=("Microsoft YaHei UI", 10), bg="#f5f7fa").pack(anchor="w", pady=2)
        tk.Label(body, text="安装时自动创建工作文件夹：片头 片中 片尾 背景 背景音乐 字幕 输出目录",
                 font=("Microsoft YaHei UI", 8), bg="#f5f7fa", fg="#9e9e9e", wraplength=480).pack(anchor="w", pady=(4, 8))
        self.progress = ttk.Progressbar(body, mode="determinate", length=460)
        self.progress.pack(fill="x")
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(body, textvariable=self.status_var, font=("Microsoft YaHei UI", 9),
                 bg="#f5f7fa", fg="#757575").pack(anchor="w", pady=(4, 0))
        btn_row = tk.Frame(body, bg="#f5f7fa")
        btn_row.pack(fill="x", pady=(12, 0))
        tk.Button(btn_row, text="开始安装", font=("Microsoft YaHei UI", 12, "bold"),
                  bg="#1565c0", fg="white", width=14, bd=0, command=self._install).pack(side="right")
        tk.Button(btn_row, text="取消", font=("Microsoft YaHei UI", 10),
                  width=8, relief="groove", command=self.destroy).pack(side="right", padx=(0, 12))

    def _browse(self):
        p = filedialog.askdirectory(title="选择安装路径")
        if p:
            self.path_var.set(os.path.join(p, "批混剪工作室"))

    def _install(self):
        dest = self.path_var.get().strip()
        if not dest:
            messagebox.showwarning("提示", "请选择安装路径")
            return
        if os.path.exists(dest) and os.listdir(dest):
            if not messagebox.askyesno("确认", "目录已存在：\n" + dest + "\n\n是否覆盖安装？"):
                return
        src = resource_dir()
        items = []
        for f in ["批混剪工作室.exe", "app.py", "core.py", "启动.bat"]:
            sp = os.path.join(src, f)
            if os.path.exists(sp):
                items.append(("file", f, sp))
        for d in ["ffmpeg"]:
            sp = os.path.join(src, d)
            if os.path.isdir(sp):
                items.append(("dir", d, sp))
        total = len(items) + len(WORK_FOLDERS)
        self.progress["maximum"] = total
        step = 0
        try:
            os.makedirs(dest, exist_ok=True)
            for kind, name, sp in items:
                self.status_var.set("复制 " + name + "...")
                self.update()
                if kind == "file":
                    shutil.copy2(sp, os.path.join(dest, name))
                else:
                    dd = os.path.join(dest, name)
                    if os.path.exists(dd):
                        shutil.rmtree(dd)
                    shutil.copytree(sp, dd)
                step += 1
                self.progress["value"] = step
                self.update()
            for d in WORK_FOLDERS:
                os.makedirs(os.path.join(dest, d), exist_ok=True)
                step += 1
                self.progress["value"] = step
                self.update()
            exe_p = os.path.join(dest, "批混剪工作室.exe")
            tgt = exe_p if os.path.exists(exe_p) else os.path.join(dest, "启动.bat")
            if self.shortcut_var.get():
                dk = os.path.join(os.environ["USERPROFILE"], "Desktop")
                mksc(tgt, os.path.join(dk, "批混剪工作室.lnk"), dest)
            if self.startmenu_var.get():
                sm = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "批混剪工作室")
                os.makedirs(sm, exist_ok=True)
                mksc(tgt, os.path.join(sm, "批混剪工作室.lnk"), dest)
            self.progress["value"] = total
            self.status_var.set("安装完成！")
            self.update()
            if messagebox.askyesno("完成", "安装成功！\n\n路径：" + dest + "\n\n已创建工作文件夹\n是否立即启动？"):
                subprocess.Popen([tgt], cwd=dest)
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", "安装失败：\n" + str(e))
            self.status_var.set("安装失败")

if __name__ == "__main__":
    Installer().mainloop()
