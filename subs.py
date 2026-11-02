#!/usr/bin/env python3
"""av-subtitles - generate subtitles for videos that have none.

Pipeline: video -> ffmpeg extracts 16kHz mono wav -> faster-whisper
transcribes -> SRT file next to the video (or wherever -o points).

Usage:
    python subs.py movie.mp4                  # auto-detect language
    python subs.py movie.mp4 --lang ja        # force Japanese
    python subs.py movie.mp4 --translate en   # + an English SRT (Whisper translate)
    python subs.py movie.mp4 --translate zh   # + a Chinese SRT (needs Argos Translate)
    python subs.py movie.mp4 --model base -o out.srt
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def extract_audio(video: Path, wav: Path) -> None:
    if shutil.which("ffmpeg") is None:
        die("ffmpeg not found. Install it first (e.g. `sudo apt install ffmpeg` "
            "or `brew install ffmpeg`).")
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video),
        "-vn", "-ac", "1", "-ar", "16000",
        str(wav),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        die(f"ffmpeg failed to extract audio:\n{result.stderr.strip()}")


def fmt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(segments) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{fmt_ts(seg['start'])} --> {fmt_ts(seg['end'])}")
        lines.append(seg["text"])
        lines.append("")
    return "\n".join(lines)


def load_wav_samples(wav: Path):
    """Read a 16kHz mono s16le WAV into a float32 numpy array.

    We decode the WAV ourselves instead of handing the file path to
    faster-whisper: its built-in decoding goes through PyAV, whose API
    keeps changing between releases. ffmpeg already guarantees the
    format, so the stdlib `wave` module is all we need.
    """
    import numpy as np

    with wave.open(str(wav), "rb") as w:
        if w.getnchannels() != 1 or w.getframerate() != 16000 \
                or w.getsampwidth() != 2:
            die("internal error: extracted WAV is not 16kHz mono s16le")
        frames = w.readframes(w.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def transcribe(model, wav: Path, lang, task="transcribe"):
    segments, info = model.transcribe(
        load_wav_samples(wav),
        language=lang,          # None = auto-detect
        task=task,
        beam_size=5,
    )
    segs = [
        {"start": s.start, "end": s.end, "text": s.text.strip()}
        for s in segments
        if s.text.strip()
    ]
    return segs, info


def translate_zh(segments, src_lang):
    """Translate segment texts into Chinese with Argos Translate.

    Argos is optional on purpose. If it (or the needed language package)
    is missing we say so and stop - no silent fallback, no fake output.
    """
    try:
        import argostranslate.translate as argos_translate
    except ImportError:
        die("--translate zh needs Argos Translate, which is not installed.\n"
            "Install it with:\n"
            "    pip install argostranslate\n"
            "    argospm update && argospm install translate-en_zh "
            "(adjust the pair to your source language)\n"
            "Argos is left out of requirements.txt on purpose: it is heavy "
            "and only needed for Chinese output.", code=2)

    installed = argos_translate.get_installed_languages()
    src = next((l for l in installed if l.code == src_lang), None)
    zh = next((l for l in installed if l.code == "zh"), None)
    if src is None or zh is None:
        die(f"Argos has no {src_lang} -> zh language package installed.\n"
            f"Install it with:  argospm install translate-{src_lang}_zh\n"
            "(Argos routes some pairs through English; if a direct pair "
            "does not exist, install translate-en_zh and translate "
            f"{src_lang}_en as well.)", code=2)

    translation = src.get_translation(zh)
    if translation is None:
        die(f"Argos cannot translate {src_lang} -> zh with the installed "
            "packages. Check `argospm list`.", code=2)

    out = []
    for seg in segments:
        seg = dict(seg)
        seg["text"] = translation.translate(seg["text"])
        out.append(seg)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Generate an SRT subtitle file for a video that has none.")
    ap.add_argument("input", help="input video (or audio) file")
    ap.add_argument("--lang", default=None,
                    help="source language code, e.g. ja / en / zh "
                         "(default: auto-detect)")
    ap.add_argument("--translate", choices=["en", "zh"], default=None,
                    help="also write a translated SRT: en = Whisper translate "
                         "task, zh = Argos Translate (must be installed)")
    ap.add_argument("--model", default="base",
                    help="faster-whisper model size: tiny / base / small / "
                         "medium / large-v3 (default: base)")
    ap.add_argument("-o", "--output", default=None,
                    help="output path for the source-language SRT "
                         "(default: <video>.<lang>.srt next to the video)")
    args = ap.parse_args()

    video = Path(args.input)
    if not video.is_file():
        die(f"input file not found: {video}")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die("faster-whisper is not installed. Run: pip install -r requirements.txt")

    print(f"[1/3] Extracting audio from {video.name} ...")
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "audio.wav"
        extract_audio(video, wav)

        print(f"[2/3] Loading model '{args.model}' (CPU, int8) ...")
        model = WhisperModel(args.model, device="cpu", compute_type="int8")

        print("[3/3] Transcribing ...")
        segments, info = transcribe(model, wav, args.lang)
        src_lang = info.language or args.lang or "und"
        print(f"      language: {src_lang} "
              f"(probability {info.language_probability:.2f}), "
              f"{len(segments)} segments")

        if not segments:
            die("no speech recognized - the SRT would be empty, nothing written.")

        out = Path(args.output) if args.output else \
            video.with_name(f"{video.stem}.{src_lang}.srt")
        out.write_text(to_srt(segments), encoding="utf-8")
        print(f"      wrote {out}")

        if args.translate == "en":
            print("      translating to English (Whisper translate task) ...")
            en_segments, _ = transcribe(model, wav, args.lang, task="translate")
            en_out = video.with_name(f"{video.stem}.en.translated.srt")
            en_out.write_text(to_srt(en_segments), encoding="utf-8")
            print(f"      wrote {en_out}")
        elif args.translate == "zh":
            print("      translating to Chinese (Argos Translate) ...")
            zh_segments = translate_zh(segments, src_lang)
            zh_out = video.with_name(f"{video.stem}.zh.translated.srt")
            zh_out.write_text(to_srt(zh_segments), encoding="utf-8")
            print(f"      wrote {zh_out}")


if __name__ == "__main__":
    main()
