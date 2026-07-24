import os
import sys
import random
import subprocess
import tempfile
import shutil
import glob
from dataclasses import dataclass
from pathlib import Path
from typing import List

def _get_base_dir():
    """获取程序所在目录（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def ffmpeg_cmd():
    # 优先查找本地 ffmpeg 目录
    local_base = os.path.join(_get_base_dir(), 'ffmpeg')
    if os.path.exists(local_base):
        for dirpath, dirnames, filenames in os.walk(local_base):
            if 'ffmpeg.exe' in filenames:
                return os.path.join(dirpath, 'ffmpeg.exe')
            if 'ffmpeg' in filenames:
                return os.path.join(dirpath, 'ffmpeg')
    # 其次查找系统 PATH
    for name in ['ffmpeg', 'ffmpeg.exe']:
        found = shutil.which(name)
        if found:
            return found
    # 最后查找常见安装路径
    for pat in [r'~\AppData\Local\ffmpeg\*\bin\ffmpeg.exe']:
        expanded = glob.glob(os.path.expanduser(pat))
        if expanded:
            return expanded[0]
    for p in [r'C:\ffmpeg\bin\ffmpeg.exe', r'C:\Program Files\ffmpeg\bin\ffmpeg.exe']:
        if os.path.exists(p):
            return p
    raise RuntimeError('未找到 FFmpeg，请确保 ffmpeg 目录存在')


def ffprobe_duration(path: Path) -> float:
    _ff = ffmpeg_cmd()
    ffprobe = os.path.join(os.path.dirname(_ff), os.path.basename(_ff).replace('ffmpeg', 'ffprobe'))
    cmd = [ffprobe, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path)]
    try:
        out = subprocess.check_output(cmd, text=True, encoding='utf-8', errors='replace').strip()
        return float(out)
    except Exception:
        return 0.0


def get_video_resolution(path: Path):
    _ff = ffmpeg_cmd()
    ffprobe = os.path.join(os.path.dirname(_ff), os.path.basename(_ff).replace('ffmpeg', 'ffprobe'))
    cmd = [ffprobe, '-v', 'error', '-select_streams', 'v:0',
           '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(path)]
    try:
        out = subprocess.check_output(cmd, text=True, encoding='utf-8', errors='replace').strip()
        w, h = out.split(',')
        return int(w), int(h)
    except Exception:
        return 1920, 1080


def _even(n: int) -> int:
    return n if n % 2 == 0 else n + 1


_FONT_PATHS = [
    r'C:\Windows\Fonts\simhei.ttf',
    r'C:\Windows\Fonts\msyh.ttc',
    r'C:\Windows\Fonts\simsun.ttc',
]
_FONT_CWD = None
_FONT_FILENAME = None
for _fp in _FONT_PATHS:
    if os.path.exists(_fp):
        _tmp = os.path.join(tempfile.gettempdir(), 'ff_wmfont.ttf')
        try:
            if not os.path.exists(_tmp):
                shutil.copy2(_fp, _tmp)
            _FONT_CWD = os.path.dirname(_tmp)
            _FONT_FILENAME = os.path.basename(_tmp)
        except Exception:
            pass
        break
if _FONT_CWD is None:
    _FONT_CWD = tempfile.gettempdir()
_FONT_ARG = f':fontfile={_FONT_FILENAME}' if _FONT_FILENAME else ''


@dataclass
class SubtitleItem:
    start: float
    end: float
    text: str


def parse_srt(path: Path) -> List[SubtitleItem]:
    items: List[SubtitleItem] = []
    if not path.exists():
        return items

    def to_seconds(t: str) -> float:
        t = t.strip().replace(',', '.')
        parts = t.split(':')
        h, m = int(parts[0]), int(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s

    text = path.read_text(encoding='utf-8', errors='ignore').strip()
    blocks = [b.strip() for b in text.split('\n\n') if b.strip()]
    for block in blocks:
        lines = block.splitlines()
        if len(lines) >= 2 and '-->' in lines[1]:
            start_s, end_s = lines[1].split('-->')
            content = '\n'.join(lines[2:])
            items.append(SubtitleItem(start=to_seconds(start_s), end=to_seconds(end_s), text=content))
    return items


def hex_to_ass_color(hex_color: str) -> str:
    c = hex_color.lstrip('#').strip()
    if len(c) >= 6:
        r, g, b = c[0:2], c[2:4], c[4:6]
        return f'&H00{b}{g}{r}'
    return '&H00FFFFFF'


def build_ass(items: List[SubtitleItem], color: str, size: int, font: str, margin_v: int) -> str | None:
    if not items:
        return None
    color_map = {
        'white': '&H00FFFFFF', 'yellow': '&H0000FFFF', 'red': '&H000000FF',
        'blue': '&H00FF0000', 'cyan': '&H00FFFF00', 'lime': '&H0000FF00',
    }
    if color.lower() in color_map:
        ass_color = color_map[color.lower()]
    else:
        ass_color = hex_to_ass_color(color)

    def fmt(v: float) -> str:
        h = int(v // 3600)
        m = int((v % 3600) // 60)
        s = v % 60
        return f'{h}:{m:02d}:{s:05.2f}'

    with tempfile.NamedTemporaryFile(delete=False, suffix='.ass', mode='w', encoding='utf-8', dir=_FONT_CWD) as f:
        f.write('[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n')
        f.write('[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n')
        f.write(f'Style: Default,{font},{size},{ass_color},&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,20,20,{margin_v},1\n\n')
        f.write('[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n')
        for it in items:
            text = it.text.replace('\n', '\\N')
            f.write(f'Dialogue: 0,{fmt(it.start)},{fmt(it.end)},Default,,0,0,0,,{text}\n')
        return f.name


def escape_ffmpeg_text(text: str) -> str:
    text = text.replace('\\', '\\\\\\\\')
    text = text.replace("'", "\\'")
    text = text.replace(':', '\\:')
    text = text.replace('%', '%%')
    text = text.replace('\n', '\\\n')
    text = text.replace('\r', '')
    return text


def generate_tts_audio(subtitle_items, output_path):
    tts_dir = os.path.join(tempfile.gettempdir(), 'tts_segments')
    os.makedirs(tts_dir, exist_ok=True)
    segments = []
    total = len(subtitle_items)
    print(f'[TTS] 开始生成 {total} 段语音...')
    for idx, item in enumerate(subtitle_items):
        if not item.text.strip():
            continue
        seg_path = os.path.join(tts_dir, f'tts_{idx:04d}.wav')
        clean_text = item.text.replace('\n', ' ').replace('"', "'").strip()
        if not clean_text:
            continue
        script_content = (
            'Add-Type -AssemblyName System.Speech\r\n'
            '$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer\r\n'
            f'$synth.SetOutputToWaveFile("{seg_path}")\r\n'
            '$synth.Rate = 0\r\n'
            f'$synth.Speak("{clean_text}")\r\n'
            '$synth.SetOutputToDefaultAudioDevice()')
        script_path = os.path.join(tts_dir, f'tts_{idx:04d}.ps1')
        with open(script_path, 'w', encoding='utf-8-sig') as sf:
            sf.write(script_content)
        try:
            subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path],
                capture_output=True, timeout=30)
            if os.path.exists(seg_path) and os.path.getsize(seg_path) > 100:
                segments.append((item.start, item.end, seg_path))
        except Exception:
            pass
        print(f'[TTS] {idx+1}/{total}', end='\r')
    print(f'\n[TTS] 生成 {len(segments)} 段语音完成')
    if not segments:
        return None
    padded = []
    cur_time = 0.0
    for i, (start, end, seg_path) in enumerate(segments):
        gap = start - cur_time
        if gap > 0.01:
            silence = os.path.join(tts_dir, f'silence_{i:04d}.wav')
            subprocess.run(
                [ffmpeg_cmd(), '-y', '-f', 'lavfi', '-i',
                 'anullsrc=r=24000:cl=mono', '-t', f'{gap:.3f}',
                 '-c:a', 'pcm_s16le', silence],
                capture_output=True, timeout=30)
            if os.path.exists(silence):
                padded.append(silence)
        padded.append(seg_path)
        cur_time = end
    if len(padded) == 1:
        shutil.copy2(padded[0], output_path)
    else:
        list_file = os.path.join(tts_dir, 'concat.txt')
        with open(list_file, 'w', encoding='utf-8') as lf:
            for p in padded:
                lf.write(f"file '{p.replace(os.sep, '/')}'\n")
        subprocess.run(
            [ffmpeg_cmd(), '-y', '-f', 'concat', '-safe', '0', '-i', list_file,
             '-c:a', 'pcm_s16le', output_path],
            capture_output=True, timeout=120)
    shutil.rmtree(tts_dir, ignore_errors=True)
    if os.path.exists(output_path):
        return output_path
    return None


def process_one(intro: Path, mid: Path | None, outro: Path | None, output: Path,
                image_watermark: Path | None, text_watermark: str | None,
                watermark_position: str,
                subtitle: Path | None, music: Path | None, background: Path | None,
                subtitle_color: str = 'white', subtitle_size: int = 68,
                subtitle_font: str = 'Arial', subtitle_margin: int = 60,
                text_color: str = 'white', text_size: int = 48,
                text_opacity: float = 0.85,
                tts_enabled: bool = False, tts_volume: float = 0.5):
    output.parent.mkdir(parents=True, exist_ok=True)
    videos = [intro]
    if mid:
        videos.append(mid)
    if outro:
        videos.append(outro)

    w, h = get_video_resolution(intro)
    has_bg = background is not None and background.exists()
    has_music = music is not None and music.exists()

    ass_path = None
    items = []
    if subtitle:
        items = parse_srt(subtitle)
        ass_path = build_ass(items, subtitle_color, subtitle_size, subtitle_font, subtitle_margin)

    tts_path = None
    if tts_enabled and items:
        tts_path = os.path.join(tempfile.gettempdir(), 'tts_output.wav')
        tts_result = generate_tts_audio(items, tts_path)
        if not tts_result:
            tts_path = None

    try:
        cmd = [ffmpeg_cmd(), '-y']
        for v in videos:
            cmd += ['-i', str(v)]

        bg_idx = len(videos)
        wm_idx = -1
        music_idx = -1

        if has_bg:
            cmd += ['-stream_loop', '-1', '-i', str(background)]
        if image_watermark and image_watermark.exists():
            cmd += ['-i', str(image_watermark)]
            wm_idx = bg_idx + (1 if has_bg else 0)
        if has_music:
            cmd += ['-i', str(music)]
            music_idx = bg_idx + (1 if has_bg else 0) + (1 if wm_idx != -1 else 0)

        tts_idx = -1
        if tts_path and os.path.exists(tts_path):
            cmd += ['-i', str(tts_path)]
            tts_idx = bg_idx + (1 if has_bg else 0) + (1 if wm_idx != -1 else 0) + (1 if has_music else 0)

        n_segs = len(videos)
        filters = []

        if has_bg:
            bg_w, bg_h = get_video_resolution(background)
            out_w, out_h = _even(bg_w), _even(bg_h)
            for i in range(n_segs):
                filters.append(
                    f'[{i}:v]scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,'
                    f'pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color=0x00FF00,setsar=1,'
                    f'setpts=PTS-STARTPTS[v{i}]')
                filters.append(f'[{i}:a]asetpts=PTS-STARTPTS[a{i}]')
            if n_segs > 1:
                concat_in = ''.join(f'[v{i}][a{i}]' for i in range(n_segs))
                filters.append(f'{concat_in}concat=n={n_segs}:v=1:a=1[vcat][acat]')
                vid, aud = '[vcat]', '[acat]'
            else:
                vid, aud = '[v0]', '[a0]'
            filters.append(
                f'[{bg_idx}:v]scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,'
                f'pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[bg]')
            filters.append(f'{vid}colorkey=0x00FF00:0.3:0.1[vt]')
            filters.append(f'[bg][vt]overlay=0:0[vbg]')
            vid = '[vbg]'
        else:
            out_w, out_h = _even(w), _even(h)
            for i in range(n_segs):
                filters.append(
                    f'[{i}:v]scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,'
                    f'pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,'
                    f'setpts=PTS-STARTPTS[v{i}]')
                filters.append(f'[{i}:a]asetpts=PTS-STARTPTS[a{i}]')
            if n_segs > 1:
                concat_in = ''.join(f'[v{i}][a{i}]' for i in range(n_segs))
                filters.append(f'{concat_in}concat=n={n_segs}:v=1:a=1[vcat][acat]')
                vid, aud = '[vcat]', '[acat]'
            else:
                vid, aud = '[v0]', '[a0]'

        if wm_idx != -1:
            wm_pos = {
                'right_top': 'W-w-20:20', 'left_top': '20:20', 'center_top': '(W-w)/2:20',
                'right_bottom': 'W-w-20:H-h-20', 'left_bottom': '20:H-h-20',
                'center_bottom': '(W-w)/2:H-h-20', 'center': '(W-w)/2:(H-h)/2'
            }
            pos = wm_pos.get(watermark_position, 'W-w-20:20')
            filters.append(f'{vid}[{wm_idx}:v]overlay={pos}[vwm]')
            vid = '[vwm]'

        if text_watermark:
            safe = escape_ffmpeg_text(text_watermark)
            named_colors = {
                'white': 'FFFFFF', 'yellow': 'FFFF00', 'red': 'FF0000', 'blue': '0000FF',
                'cyan': '00FFFF', 'lime': '00FF00', 'black': '000000', 'orange': 'FFA500'
            }
            color = text_color.lstrip('#')
            if color.lower() in named_colors:
                color = named_colors[color.lower()]
            pos_map = {
                'right_top': 'x=w-tw-20:y=20', 'left_top': 'x=20:y=20', 'center_top': 'x=(w-tw)/2:y=20',
                'right_bottom': 'x=w-tw-20:y=h-th-20', 'left_bottom': 'x=20:y=h-th-20',
                'center_bottom': 'x=(w-tw)/2:y=h-th-20', 'center': 'x=(w-tw)/2:y=(h-th)/2'
            }
            pos_expr = pos_map.get(watermark_position, 'x=w-tw-20:y=20')
            filters.append(
                f'{vid}drawtext=text={safe}:fontsize={text_size}:'
                f'fontcolor=0x{color}@{text_opacity}:borderw=2:bordercolor=black@0.6:'
                f'{pos_expr}{_FONT_ARG}[vtm]')
            vid = '[vtm]'

        if ass_path:
            ass_name = os.path.basename(ass_path)
            filters.append(f"{vid}ass={ass_name}[outv]")
            vid = '[outv]'

        fc = ';'.join(filters)

        if has_music:
            fc += f';{aud}volume=1.0[orig]'
            fc += f';[{music_idx}:a]volume=1.0[mus]'
            fc += ';[orig][mus]amix=inputs=2:duration=shortest:dropout_transition=2[aout]'
            audio_map = '[aout]'
        else:
            audio_map = aud

        if tts_idx != -1:
            vol = max(0.0, min(1.0, tts_volume))
            fc += f';[{tts_idx}:a]volume={vol}[ttsa]'
            fc += f';{audio_map}[ttsa]amix=inputs=2:duration=first:dropout_transition=2[final]'
            audio_map = '[final]'

        cmd += ['-filter_complex', fc]
        cmd += ['-map', vid]
        cmd += ['-map', audio_map]
        cmd += ['-shortest']
        cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                '-fps_mode', 'passthrough',
                '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
                str(output)]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=_FONT_CWD)
        if result.returncode != 0:
            err = result.stderr[-3000:] if result.stderr else 'unknown error'
            raise RuntimeError(f'FFmpeg 错误 (退出码 {result.returncode}):\n{err}')
    finally:
        if ass_path and os.path.exists(ass_path):
            os.remove(ass_path)
        if tts_path and os.path.exists(tts_path):
            try:
                os.remove(tts_path)
            except Exception:
                pass


def make_combinations(first_list: List[Path], second_list: List[Path], third_list: List[Path], mode: str) -> List[dict]:
    combos = []
    pool_mid = list(second_list)
    pool_out = list(third_list)
    if mode == 'shuffle':
        random.shuffle(pool_mid)
        random.shuffle(pool_out)
    for i, intro in enumerate(first_list):
        mid = pool_mid[i % len(pool_mid)] if pool_mid else None
        outro = pool_out[i % len(pool_out)] if pool_out else None
        combos.append({'intro': intro, 'mid': mid, 'outro': outro})
    return combos