#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

try:
    from TTS.api import TTS
except Exception:
    TTS = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'video_out'
OUT.mkdir(exist_ok=True)

# Video size and layout
WIDTH, HEIGHT = 1920, 1080
PADDING = 80
BG = (18, 18, 18)
TITLE_COLOR = (255, 204, 51)
TEXT_COLOR = (240, 240, 240)

# Map language name to a TTS model or gTTS language code
TTS_MODELS = {
    'Malayalam': 'tts_models/ml/cv/vits',
    'Kannada': 'tts_models/kn/cv/vits',
    'Tamil': 'tts_models/ta/cv/vits',
    'Telugu': 'tts_models/te/cv/vits',
    'Hindi': 'tts_models/hi/cv/vits',
    'English': 'tts_models/en/ljspeech/tacotron2-DDC'
}

GTTS_LANG = {
    'Malayalam': 'ml', 'Kannada': 'kn', 'Tamil': 'ta', 'Telugu': 'te', 'Hindi': 'hi', 'English': 'en'
}

FONTS = {
    'Malayalam': str(ROOT / 'fonts' / 'NotoSansMalayalam-Regular.ttf'),
    'Kannada': str(ROOT / 'fonts' / 'NotoSansKannada-Regular.ttf'),
    'Tamil': str(ROOT / 'fonts' / 'NotoSansTamil-Regular.ttf'),
    'Telugu': str(ROOT / 'fonts' / 'NotoSansTelugu-Regular.ttf'),
    'Hindi': str(ROOT / 'fonts' / 'NotoSansDevanagari-Regular.ttf'),
    'English': str(ROOT / 'fonts' / 'DejaVuSans.ttf')
}


def load_batch_outputs():
    out_path = ROOT / 'batch_output.json'
    if not out_path.exists():
        print('batch_output.json not found. Run translate_gemma.py first.')
        sys.exit(1)
    raw = json.loads(out_path.read_text(encoding='utf8'))
    items = [d for d in raw if d.get('input', {}).get('meta', {}).get('translate', True) is not False]
    return items


def get_sequence():
    b = ROOT / 'batch.json'
    if b.exists():
        bj = json.loads(b.read_text(encoding='utf8'))
        seq = bj.get('sequence') if isinstance(bj, dict) else None
        if seq:
            seq = ['Source' if (isinstance(s, str) and s.lower() == 'english') else s for s in seq]
            return seq
    return ['Source', 'Malayalam', 'Kannada', 'Tamil', 'Telugu', 'Hindi']


def make_slide(text, lang, index):
    img = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    font_path = FONTS.get(lang)
    try:
        font_title = ImageFont.truetype(font_path, 48) if font_path and Path(font_path).exists() else ImageFont.load_default()
        font_body = ImageFont.truetype(font_path, 40) if font_path and Path(font_path).exists() else ImageFont.load_default()
    except Exception:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    draw.text((PADDING, PADDING), f"{index+1}. {lang}", fill=TITLE_COLOR, font=font_title)

    max_w = WIDTH - 2 * PADDING
    y = PADDING + 90
    lines = wrap_text(text, font_body, max_w)
    for ln in lines:
        draw.text((PADDING, y), ln, fill=TEXT_COLOR, font=font_body)
        y += font_body.getsize(ln)[1] + 8

    out = OUT / f"{index:02d}_{lang}.png"
    img.save(out)
    return out


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    cur = ''
    for w in words:
        test = (cur + ' ' + w).strip()
        if font.getsize(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def synth_audio(text, lang):
    out = OUT / f"{lang}.wav"
    if TTS and (lang in TTS_MODELS):
        try:
            tts = TTS(TTS_MODELS[lang])
            tts.tts_to_file(text=text, file_path=str(out))
            return out
        except Exception as e:
            print('TTS model failed for', lang, e)

    if gTTS and GTTS_LANG.get(lang):
        try:
            t = gTTS(text=text, lang=GTTS_LANG[lang])
            t.save(str(out))
            return out
        except Exception as e:
            print('gTTS failed for', lang, e)

    raise RuntimeError(f'No available TTS for {lang}')


def make_video_from_image(img, audio, lang):
    out = OUT / f"{lang}.mp4"
    cmd = [
        'ffmpeg', '-y', '-loop', '1', '-i', str(img), '-i', str(audio),
        '-c:v', 'libx264', '-tune', 'stillimage', '-c:a', 'aac',
        '-b:a', '192k', '-shortest', '-pix_fmt', 'yuv420p', str(out)
    ]
    subprocess.run(cmd, check=True)
    return out


def concat_videos(videos, out_name='final.mp4'):
    listfile = OUT / 'list.txt'
    with open(listfile, 'w', encoding='utf8') as f:
        for v in videos:
            f.write(f"file '{v.as_posix()}'\n")
    subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(listfile), '-c', 'copy', str(OUT / out_name)], check=True)
    return OUT / out_name


def main():
    items = load_batch_outputs()
    seq = get_sequence()
    videos = []
    for idx, lang in enumerate(seq):
        if lang.lower() in ('english', 'source'):
            continue
        texts = [it.get('translation', {}).get(lang, '').strip() for it in items]
        full = '\n\n'.join([t for t in texts if t])
        if not full:
            print('No text for', lang, '— skipping')
            continue
        print('Rendering', lang)
        img = make_slide(full, lang, idx)
        audio = synth_audio(full, lang)
        vid = make_video_from_image(img, audio, lang)
        videos.append(vid)

    if videos:
        final = concat_videos(videos)
        print('Done ->', final)
    else:
        print('No videos produced')


if __name__ == '__main__':
    main()
