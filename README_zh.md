[English](README.md) | [简体中文](README_zh.md) | [日本語](README_ja.md) | [한국어](README_ko.md)

# av-subtitles

## 先说人话

很多成人视频是根本没有字幕的，尤其是日系片。全程外语，听不懂，
只能看画面猜剧情。这个工具就是干这个的：给没字幕的片子，
自动配上一份字幕。

说白了它做的事很简单：把视频里的说话声抽出来，听一遍，把听到的
内容打成文字，做成一个字幕文件——就是 `.srt`，播放器在画面下方
一行一行显示台词的那个小文本文件。把这个文件放到视频旁边，
再打开视频，谁说了什么就能看明白了。

它还能顺手翻译：英文字幕可以在同一次运行里一起出；中文字幕也行，
走一个可选的离线翻译组件，在你自己电脑上翻（那个要另装，
细节见下面「翻译功能的真实边界」）。

对这类视频最重要的一点：**全程在你自己电脑上跑。**视频不会上传
到任何网站，没有哪个在线服务能看到你的文件。片库里是什么内容，
就只留在你自己的硬盘里。

它内部其实就这么一条线：

```
视频 ──ffmpeg──▶ 16kHz 单声道 wav ──faster-whisper──▶ .srt
                                                  └──可选──▶ 翻译版 .srt
```

（ffmpeg 是负责把声音抽出来的工具，faster-whisper 是负责「听写」的
语音转文字引擎。）

## 它能做什么

- 用 ffmpeg 把声音抽出来，用 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  把说的话听写成文字。语言可以自动检测，也可以用 `--lang ja` 指定。
- 在视频旁边生成一个普通字幕文件：`movie.ja.srt`。
- `--translate en` 顺带出一份英文字幕，边听写边翻译，同一次跑完。
- `--translate zh` 顺带出一份中文字幕，靠本地的 Argos Translate 离线
  翻译——**前提是你自己装了它**（见下文）。没装的话工具会直接报错
  停下，不装样子。

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
