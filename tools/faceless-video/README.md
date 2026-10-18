# Faceless video generator

Makes vertical 1080x1920 short-form videos (TikTok / Reels / Shorts). Each video has:

- an illustrated silhouette scene behind every line, with a slow Ken Burns zoom and crossfades
- bold subtitles that pop in word by word, with the current word highlighted in yellow
- an offline neural voiceover ([Kokoro](https://github.com/thewh1teagle/kokoro-onnx)) that follows the text
- generated soft piano background music that gets quieter while the voice speaks, normalized to -14 LUFS

## Setup

```bash
pip install kokoro-onnx soundfile pillow numpy   # ffmpeg must be on PATH
mkdir models && cd models
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

## Make a video

Edit `script.txt`. Put one `scene | line` per line. Then run:

```bash
python3 make_video.py script.txt out.mp4 --models models
```

Options:
- `--voice`: `am_onyx` (deep male, default), `bm_george` (British male), `af_heart`, `bf_emma`, ...
- `--speed`: speaking speed (default 0.88)
- `--music-db`: music volume (default -17)

Built-in scenes are in `scenes.py`: `poor rich young old married single broken truth happy`.
To add your own, write a new `s_<name>(w, h)` function and register it in `SCENES`.
