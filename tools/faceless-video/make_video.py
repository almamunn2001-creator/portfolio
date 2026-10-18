"""Render a vertical faceless video: illustrated scenes, word-by-word subtitles,
offline neural voiceover (Kokoro) and generated background music.

Usage:
  python3 make_video.py script.txt out.mp4 --models DIR [--voice am_onyx] [--speed 0.88]
"""
import argparse
import os
import re
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import scenes

W, H, FPS, SR = 1080, 1920, 30, 24000
ZOOM = 1.12          # source image oversize for Ken Burns motion
GAP = 0.55           # silence after each line (s)
XFADE = 0.35         # crossfade between scenes (s)
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
TEXT_Y = 0.25        # vertical centre of subtitles (fraction of height)
HIGHLIGHT = (255, 214, 64)


def parse_script(path):
    items = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        scene, text = [p.strip() for p in line.split("|", 1)]
        items.append((scene, text))
    return items


# ---------------------------------------------------------------- audio

def tts(items, models, voice, speed):
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(models, "kokoro-v1.0.onnx"), os.path.join(models, "voices-v1.0.bin"))
    clips = []
    for _, text in items:
        a, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
        assert sr == SR
        idx = np.where(np.abs(a) > 0.01)[0]
        a = a[max(idx[0] - 600, 0): idx[-1] + 2400]
        clips.append(a.astype(np.float32))
    return clips


def reverb(x, sr, seconds=2.2, mix=0.35):
    n = int(sr * seconds)
    rng = np.random.default_rng(0)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir /= np.sqrt((ir ** 2).sum())
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[: len(x)]
    return x * (1 - mix) + wet * mix


def music(duration, sr=SR):
    """Soft emotional piano + pad, Am - F - C - G."""
    t_total = int(duration * sr) + sr
    out = np.zeros(t_total)
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    bar = 3.2
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)

    def note(m, start, dur, vel):
        s = int(start * sr)
        n = min(int(dur * sr), t_total - s)
        if n <= 0:
            return
        t = np.arange(n) / sr
        f = hz(m)
        tone = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.8 for k in range(1, 6))
        env = np.exp(-t * 2.2) * (1 - np.exp(-t * 300))
        out[s:s + n] += tone * env * vel

    t, i = 0.0, 0
    while t < duration + 1:
        ch = chords[i % 4]
        note(ch[0] - 24, t, bar, 0.5)                      # bass
        for j, m in enumerate([ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1]]):
            note(m + 12, t + j * bar / 6, 2.5, 0.22)       # arpeggio
        # pad
        s, n = int(t * sr), min(int(bar * sr), t_total - int(t * sr))
        if n > 0:
            tt = np.arange(n) / sr
            pad = sum(np.sin(2 * np.pi * hz(m) * tt) + np.sin(2 * np.pi * hz(m) * 1.003 * tt) for m in ch)
            env = np.minimum(1, tt / 0.8) * np.minimum(1, (bar - tt) / 0.8)
            out[s:s + n] += pad * env * 0.05
        t += bar
        i += 1
    out = reverb(out, sr)
    out /= np.abs(out).max() + 1e-9
    fade = int(2.5 * sr)
    out[:int(0.5 * sr)] *= np.linspace(0, 1, int(0.5 * sr))
    out = out[: int(duration * sr)]
    out[-fade:] *= np.linspace(1, 0, fade)
    return out


# ---------------------------------------------------------------- subtitles

def word_times(text, dur):
    """Estimate when each word starts, weighting by length (+ pause at commas)."""
    words = text.split()
    weights = [len(re.sub(r"\W", "", w)) + 2 + (4 if w[-1] in ",.;:" else 0) for w in words]
    total = sum(weights)
    acc, starts = 0, []
    for wt in weights:
        starts.append(dur * acc / total)
        acc += wt
    return words, starts


def layout(words, font, max_w):
    lines, cur = [], []
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for i, w in enumerate(words):
        test = " ".join(words[j] for j in cur + [i])
        if cur and d.textlength(test, font=font) > max_w:
            lines.append(cur)
            cur = [i]
        else:
            cur.append(i)
    lines.append(cur)
    return lines


def subtitle_layer(words, shown, active, font):
    """RGBA overlay with words[0:shown] visible, words[active] highlighted."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = layout(words, font, W * 0.82)
    lh = font.size * 1.22
    y0 = H * TEXT_Y - lh * len(lines) / 2
    space = d.textlength(" ", font=font)
    boxes = []
    for li, line in enumerate(lines):
        lw = d.textlength(" ".join(words[i] for i in line), font=font)
        x = (W - lw) / 2
        for i in line:
            boxes.append((i, x, y0 + li * lh))
            x += d.textlength(words[i], font=font) + space
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for i, x, y in boxes:
        if i < shown:
            sd.text((x + 4, y + 8), words[i], font=font, fill=(0, 0, 0, 200))
    layer = Image.alpha_composite(layer, shadow.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(layer)
    for i, x, y in boxes:
        if i < shown:
            col = HIGHLIGHT if i == active else (255, 255, 255)
            d.text((x, y), words[i], font=font, fill=col, stroke_width=7, stroke_fill=(0, 0, 0))
    return layer


# ---------------------------------------------------------------- video

def kenburns(img, p, k):
    """p: progress 0..1, k: segment index (alternates direction)."""
    sw, sh = img.size
    z = 1.0 + 0.07 * (p if k % 2 == 0 else 1 - p)
    cw, ch = sw / ZOOM / z, sh / ZOOM / z
    dx = (sw - cw) * (0.5 + 0.25 * (p - 0.5) * (1 if k % 3 else -1))
    dy = (sh - ch) * (0.5 - 0.15 * (p - 0.5))
    return img.resize((W, H), Image.BILINEAR, box=(dx, dy, dx + cw, dy + ch))


def vignette():
    y, x = np.ogrid[:H, :W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    a = np.clip((r - 0.75) / 0.7, 0, 1) * 150
    v = np.zeros((H, W, 4), np.uint8)
    v[..., 3] = a.astype(np.uint8)
    return Image.fromarray(v, "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("out")
    ap.add_argument("--models", required=True)
    ap.add_argument("--voice", default="am_onyx")
    ap.add_argument("--speed", type=float, default=0.88)
    ap.add_argument("--music-db", type=float, default=-17)
    args = ap.parse_args()

    items = parse_script(args.script)
    print("voiceover…")
    clips = tts(items, args.models, args.voice, args.speed)

    # timeline
    starts, t = [], 0.6
    for i, c in enumerate(clips):
        starts.append(t)
        t += len(c) / SR + GAP + (0.8 if i == len(clips) - 2 else 0)
    total = t + 1.8

    voice = np.zeros(int(total * SR))
    for s, c in zip(starts, clips):
        i = int(s * SR)
        voice[i:i + len(c)] += c
    voice /= np.abs(voice).max() + 1e-9
    voice *= 0.9

    print("music…")
    m = music(total)
    # duck music while the voice is speaking
    env = np.convolve(np.abs(voice), np.ones(SR // 5) / (SR // 5), "same")
    duck = 1 - 0.45 * np.clip(env / (env.max() * 0.3), 0, 1)
    mix = voice + m * duck * 10 ** (args.music_db / 20)
    mix /= max(1.0, np.abs(mix).max() / 0.97)

    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, "mix.wav")
    sf.write(wav, mix.astype(np.float32), SR)

    print("illustrations…")
    srcs = {}
    for sc, _ in items:
        if sc not in srcs:
            srcs[sc] = scenes.render(sc, int(W * ZOOM), int(H * ZOOM))

    font = ImageFont.truetype(FONT, 84)
    vig = vignette()
    seg_bounds = [0.0] + [starts[i + 1] - GAP / 2 for i in range(len(items) - 1)] + [total]
    word_data = []
    for (sc, text), s, c in zip(items, starts, clips):
        words, ws = word_times(text, len(c) / SR * 0.92)
        word_data.append((words, [s + x for x in ws]))

    print("rendering frames…")
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", args.out,
    ], stdin=subprocess.PIPE)

    sub_cache = {}
    nframes = int(total * FPS)
    for f in range(nframes):
        t = f / FPS
        k = max(i for i in range(len(items)) if seg_bounds[i] <= t)
        a, b = seg_bounds[k], seg_bounds[k + 1]
        frame = kenburns(srcs[items[k][0]], (t - a) / (b - a), k)
        if k > 0 and t - a < XFADE:  # crossfade from previous scene
            pa, pb = seg_bounds[k - 1], seg_bounds[k]
            prev = kenburns(srcs[items[k - 1][0]], min(1, (t - pa) / (pb - pa)), k - 1)
            frame = Image.blend(prev, frame, (t - a) / XFADE)
        frame = frame.convert("RGBA")
        frame = Image.alpha_composite(frame, vig)
        words, wstarts = word_data[k]
        shown = sum(1 for x in wstarts if t >= x)
        if t > b - 0.12 and k < len(items) - 1:
            shown = 0  # clear text right before the cut
        if shown:
            key = (k, shown)
            if key not in sub_cache:
                sub_cache[key] = subtitle_layer(words, shown, shown - 1, font)
            frame = Image.alpha_composite(frame, sub_cache[key])
        if t > total - 1.2:  # fade to black
            frame = Image.blend(frame, Image.new("RGBA", (W, H), (0, 0, 0, 255)), (t - (total - 1.2)) / 1.2)
        ff.stdin.write(frame.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    print(f"done: {args.out} ({total:.1f}s)")


if __name__ == "__main__":
    main()
