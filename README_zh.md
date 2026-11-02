[English](README.md) | [简体中文](README_zh.md) | [日本語](README_ja.md) | [한국어](README_ko.md)

# av-subtitles

我片库里一半视频是没有字幕的，尤其是日语的。看一半猜一半实在难受，
就写了这个小工具：把视频丢给它，还你一个字幕文件。

流水线很简单，没什么花活：

```
视频 ──ffmpeg──▶ 16kHz 单声道 wav ──faster-whisper──▶ .srt
                                                  └──可选──▶ 翻译版 .srt
```

## 它能做什么

- 用 ffmpeg 抽出音轨，用 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  转写。语言可以自动检测，也可以用 `--lang ja` 指定。
- 在视频旁边生成一个普通 SRT：`movie.ja.srt`。
- `--translate en` 顺带出一份英文字幕，用的是 Whisper 自带的 translate 任务。
- `--translate zh` 顺带出一份中文字幕，靠本地的 Argos Translate 翻译——
  **前提是你自己装了它**（见下文）。没装的话工具会直接报错停下，不装样子。

## 安装

需要 Python 3.9+，以及 PATH 里能找到 ffmpeg。

```bash
# 没有 ffmpeg 的先装：
sudo apt install ffmpeg        # Debian/Ubuntu
brew install ffmpeg            # macOS

pip install -r requirements.txt
```

Whisper 模型会在第一次运行时自动下载。

## 用法

```bash
# 自动检测语言
python subs.py movie.mp4

# 日语的，别猜了
python subs.py movie.mp4 --lang ja

# 顺带一份英文字幕
python subs.py movie.mp4 --lang ja --translate en

# 顺带一份中文字幕（需要 Argos，见下文）
python subs.py movie.mp4 --lang ja --translate zh

# 换模型、指定输出路径
python subs.py movie.mp4 --model small -o subs/movie.srt
```

| 参数 | 说明 |
| --- | --- |
| `--lang` | 源语言代码（`ja`、`en`、`zh`……），默认自动检测 |
| `--translate en\|zh` | 额外生成一份翻译字幕 |
| `--model` | Whisper 模型大小，默认 `base` |
| `-o` | 源语言 SRT 的输出路径 |

不写 `-o` 时的命名规则：

- `movie.<语言>.srt` —— 转写结果
- `movie.en.translated.srt` / `movie.zh.translated.srt` —— 翻译结果

把 SRT 和视频同名放在一起，VLC、mpv、IINA、Stash、Jellyfin
这些播放器基本都会自己加载。

## 模型大小与 CPU 速度预期

这工具默认跑 CPU（int8），模型别贪大，先说清楚：

| 模型 | 下载大小 | CPU 上的表现 |
| --- | --- | --- |
| `tiny` | 约 75 MB | 很快，但错误肉眼可见 |
| `base` | 约 145 MB | 短片完全够用，默认就是它 |
| `small` | 约 470 MB | 明显更准，也明显更慢 |
| `medium` / `large-v3` | 约 1.5 GB / 约 3 GB | 要等很久，真要用请上 GPU |

几分钟的短片，`base` 在普通笔记本 CPU 上没问题。两小时的长片，
要么用 `tiny`/`base` 挂着跑、去泡杯茶，要么大模型挂一夜。
日语准确率从 `base` 到 `small` 提升很明显，在意的可以升一档。

## 翻译功能的真实边界

- **英文（`--translate en`）**：Whisper 内置的 translate 任务，
  不管源语言是什么，出来都是英文。发音清楚时质量还行，
  俚语多、多人抢话时会飘。
- **中文（`--translate zh`）**：靠
  [Argos Translate](https://github.com/argosopentech/argos-translate)
  本地离线翻译，**不在** `requirements.txt` 里——它体积不小，
  而且不是人人都需要。要开启：

  ```bash
  pip install argostranslate
  argospm update
  argospm install translate-en_zh   # 源语言是日语的还要装 translate-ja_en
  ```

  没装 Argos 就没有中文，工具会把上面这几行原样报给你，不糊弄。

## 局限性

- 准确率看音质脸色。背景音乐大、多人同时说话、含糊的咬字，
  都会转出垃圾段落。换大模型能缓解，根治不了。
- 没有说话人区分、没有角色标注，就一条字幕流。
- 时间轴直接来自 Whisper 的分段，一般没问题，
  偶尔需要丢进字幕编辑器微调一两句。
- 默认只用 CPU。代码里写的是 `device="cpu"`，有 N 卡的话
  改成 `cuda` / `float16` 就能用上。

## 许可证

MIT。我用 Whisper 项目常用的 JFK 演讲片段（公有领域录音）实测了
整条流水线；片段没有打包进仓库，随便找一段发音清楚的短音频
就能自己试。
