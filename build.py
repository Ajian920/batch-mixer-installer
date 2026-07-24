# -*- coding: utf-8 -*-
"""
打包脚本 - 生成安装器 exe
运行前确保已安装 PyInstaller: pip install pyinstaller

用法:
  python build.py
"""
import subprocess, sys, os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASE, 'dist')

# 1. 打包主程序
print('[1/3] 打包主程序...')
subprocess.run([
    sys.executable, '-m', 'PyInstaller', '--onefile', '--windowed',
    '--name', '批混剪工作室',
    '--add-data', 'core.py;.',
    '--distpath', DIST,
    '--workpath', os.path.join(BASE, 'build_tmp'),
    '--specpath', BASE,
    'app.py', '--noconfirm'
], check=True)

# 2. 打包安装器（内嵌所有文件）
print('[2/3] 打包安装器...')
subprocess.run([
    sys.executable, '-m', 'PyInstaller', '--onefile', '--windowed',
    '--name', '批混剪工作室_安装器',
    '--add-data', os.path.join(DIST, '批混剪工作室.exe') + ';.',
    '--add-data', 'app.py;.',
    '--add-data', 'core.py;.',
    '--add-data', '启动.bat;.',
    '--add-data', 'ffmpeg;ffmpeg',
    '--distpath', DIST,
    '--workpath', os.path.join(BASE, 'build_tmp'),
    '--specpath', BASE,
    'installer.py', '--noconfirm'
], check=True)

# 3. 清理
print('[3/3] 清理...')
for d in ['build_tmp', 'build']:
    p = os.path.join(BASE, d)
    if os.path.exists(p):
        shutil.rmtree(p)
for f in os.listdir(BASE):
    if f.endswith('.spec'):
        os.remove(os.path.join(BASE, f))

print(f'完成！安装器位于: {os.path.join(DIST, "批混剪工作室_安装器.exe")}')
