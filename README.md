[English](README.md) | [简体中文](README_zh.md) | [日本語](README_ja.md) | [한국어](README_ko.md)

# av-subtitles

## In plain words

A lot of adult videos come with no subtitles at all — Japanese ones
especially. The whole video is in a language you don't speak, so you end
up watching the pictures and guessing what's going on. This tool fixes
that: it gives those videos subtitles.

What it does, in plain terms: it pulls the sound out of the video,
listens to what people are saying, and types it out as a subtitle file —
an `.srt`, the little text file your player shows at the bottom of the
screen, one line at a time. Put that file next to the video, press play,
and you can finally follow the dialogue.

It can translate while it's at it. English subtitles can come out of the
same run. Chinese subtitles are possible too, through an optional
translator that also runs offline on your own machine — it's an add-on,
not built in (details under "Translation, honestly" below).

And the part that matters most for this kind of video: **everything runs
on your own computer.** Your video is never uploaded to any website, no
online service ever sees it. Whatever is in your library stays in your
library.

Under the hood, the whole thing is just this one line:

```
video ──ffmpeg──▶ 16kHz mono wav ──faster-whisper──▶ .srt
                                              └──optional──▶ translated .srt
```

(ffmpeg is the tool that pulls the audio out of the video;
faster-whisper is the speech-to-text engine that does the listening
and typing.)

## What it does

- Pulls the audio out of the video and writes down what's said, with
  [faster-whisper](https://github.com/SYSTRAN/faster-whisper) doing the
  listening. The language is auto-detected, or pin it with `--lang ja`.
- Writes a plain subtitle file next to the video: `movie.ja.srt`.
- `--translate en` also writes an English subtitle — the same speech,
  translated as it is transcribed.
- `--translate zh` also writes a Chinese subtitle, translated offline on
  your own machine with Argos Translate — **if** you installed it (see
  below). If you didn't, the tool tells you so and stops. It does not
  pretend.

## Install

You need Python 3.9+ and ffmpeg on your PATH.

```bash
# ffmpeg, if you don't have it yet:
sudo apt install ffmpeg        # Debian/Ubuntu
brew install ffmpeg            # macOS

pip install -r requirements.txt
```

The Whisper model downloads automatically the first time you run it.

## Usage

```bash
# auto-detect the language
python subs.py movie.mp4

# it's Japanese, don't guess
python subs.py movie.mp4 --lang ja

# also write an English subtitle
python subs.py movie.mp4 --lang ja --translate en

# also write a Chinese subtitle (needs Argos, see below)
python subs.py movie.mp4 --lang ja --translate zh

# pick a model, pick the output path
python subs.py movie.mp4 --model small -o subs/movie.srt
```

| Option | Meaning |
| --- | --- |
| `--lang` | source language code (`ja`, `en`, `zh`, ...). Default: auto-detect |
| `--translate en\|zh` | also write a translated SRT |
| `--model` | Whisper model size, default `base` |
| `-o` | output path for the source-language SRT |

Output names (when `-o` is not given):

- `movie.<lang>.srt` — the transcription
- `movie.en.translated.srt` / `movie.zh.translated.srt` — the translation

Drop the SRT next to the video with the matching name and most players
(VLC, mpv, IINA, Stash, Jellyfin...) pick it up on their own.

## Models and CPU expectations

This runs on CPU (int8). Be honest with yourself about model size:

| Model | Download | On CPU |
| --- | --- | --- |
| `tiny` | ~75 MB | very fast, rough around the edges |
| `base` | ~145 MB | fine for short clips — this is the default |
| `small` | ~470 MB | noticeably better, noticeably slower |
| `medium` / `large-v3` | ~1.5 GB / ~3 GB | you will wait. Use a GPU build if you go here |

For a short clip (a few minutes), `base` on an ordinary laptop CPU is
perfectly usable. For a two-hour video, either leave `tiny`/`base`
running and go make tea, or use a bigger model overnight. Japanese
accuracy in particular jumps a lot from `base` to `small`.

## Translation, honestly

- **English (`--translate en`)**: Whisper's built-in translate task.
  Whatever the source language, it comes out as English. Quality is
  decent for clear speech, wobbly for slang and overlapping voices.
- **Chinese (`--translate zh`)**: done by
  [Argos Translate](https://github.com/argosopentech/argos-translate),
  fully offline, but it's **not** in `requirements.txt` — it's heavy and
  most people won't need it. To enable:

  ```bash
  pip install argostranslate
  argospm update
  argospm install translate-en_zh   # plus translate-ja_en if your source is Japanese
  ```

  No Argos, no Chinese. The tool errors out with exactly these
  instructions instead of faking it.

## Limitations

- Accuracy lives and dies with the audio. Background music, overlapping
  dialogue and mumbling will produce garbage in places. A bigger model
  helps, nothing fixes it completely.
- No speaker labels, no diarization. One subtitle stream, that's it.
- Timings come straight from Whisper's segments — usually fine,
  occasionally a line needs nudging in a subtitle editor.
- CPU-only by default. The code sets `device="cpu"`; if you have an
  NVIDIA GPU, changing that one line to `cuda` / `float16` works.

## License

MIT. I tested the pipeline with the well-known JFK speech excerpt used
by the Whisper project (a public domain recording). It's not bundled
here — any short clip with clear speech works for a test drive.
