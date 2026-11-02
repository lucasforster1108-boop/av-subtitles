[English](README.md) | [简体中文](README_zh.md) | [日本語](README_ja.md) | [한국어](README_ko.md)

# av-subtitles

ライブラリにある動画の半分くらいは字幕がありません。特に日本語のもの。
半分くらいしか分からないまま観るのに疲れたので、動画を渡せば字幕ファイルを
返してくれるこのツールを作りました。

仕組みはシンプルです：

```
動画 ──ffmpeg──▶ 16kHz モノラル wav ──faster-whisper──▶ .srt
                                                    └──任意──▶ 翻訳版 .srt
```

## できること

- ffmpeg で音声を取り出し、[faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  で書き起こします。言語は自動判定、`--lang ja` で固定もできます。
- 動画の隣に普通の SRT を出力します：`movie.ja.srt`
- `--translate en` で、Whisper 自体の translate タスクを使った英語字幕も出せます。
- `--translate zh` で中国語字幕も出せますが、これはローカルの Argos Translate
  で翻訳します——**自分でインストールした場合だけ**（後述）。入っていない場合は
  ごまかさずにエラーを出して止まります。

## インストール

Python 3.9+ と、PATH の通った ffmpeg が必要です。

```bash
# ffmpeg がまだなら：
sudo apt install ffmpeg        # Debian/Ubuntu
brew install ffmpeg            # macOS

pip install -r requirements.txt
```

Whisper のモデルは初回実行時に自動でダウンロードされます。

## 使い方

```bash
# 言語を自動判定
python subs.py movie.mp4

# 日本語と分かっているなら固定する
python subs.py movie.mp4 --lang ja

# 英語字幕も一緒に出す
python subs.py movie.mp4 --lang ja --translate en

# 中国語字幕も一緒に出す（Argos が必要、後述）
python subs.py movie.mp4 --lang ja --translate zh

# モデルと出力先を指定
python subs.py movie.mp4 --model small -o subs/movie.srt
```

| オプション | 意味 |
| --- | --- |
| `--lang` | 入力言語コード（`ja`、`en`、`zh` など）。デフォルトは自動判定 |
| `--translate en\|zh` | 翻訳字幕も追加で出力 |
| `--model` | Whisper のモデルサイズ。デフォルトは `base` |
| `-o` | 原語 SRT の出力パス |

`-o` を省略した場合の命名：

- `movie.<言語>.srt` —— 書き起こし結果
- `movie.en.translated.srt` / `movie.zh.translated.srt` —— 翻訳結果

SRT を動画と同じ名前で隣に置けば、VLC、mpv、IINA、Stash、Jellyfin
あたりは勝手に読み込んでくれます。

## モデルサイズと CPU での目安

デフォルトは CPU（int8）実行です。欲張らないのが大事です：

| モデル | ダウンロード | CPU での感触 |
| --- | --- | --- |
| `tiny` | 約 75 MB | とても速いが、粗さは目立つ |
| `base` | 約 145 MB | 短いクリップなら十分。デフォルトはこれ |
| `small` | 約 470 MB | はっきり良くなるが、はっきり遅い |
| `medium` / `large-v3` | 約 1.5 GB / 約 3 GB | かなり待ちます。この辺を使うなら GPU 版を |

数分のクリップなら、普通のノート PC の CPU で `base` は問題なく使えます。
2 時間の動画は `tiny`/`base` を回してお茶でも淹れるか、大きなモデルで
一晩かけるか。日本語の精度は `base` から `small` でかなり上がります。

## 翻訳について、正直に

- **英語（`--translate en`）**：Whisper 内蔵の translate タスク。
  入力が何語でも出力は英語です。はっきりした発音ならそこそこ、
  スラングや被った音声では揺れます。
- **中国語（`--translate zh`）**：
  [Argos Translate](https://github.com/argosopentech/argos-translate)
  による完全オフライン翻訳ですが、`requirements.txt` には**入れていません**。
  重いし、全員に必要でもないので。有効化するには：

  ```bash
  pip install argostranslate
  argospm update
  argospm install translate-en_zh   # 入力が日本語なら translate-ja_en も
  ```

  Argos がなければ中国語は出ません。その代わり、ツールはこの手順を
  そのまま表示して止まります。できているふりはしません。

## 制限

- 精度は音質次第です。BGM が大きい、複数人が同時に話す、滑舌が悪い——
  そういう箇所は崩れます。モデルを上げれば緩和はされますが、完全には直りません。
- 話者分離も話者ラベルもありません。字幕は 1 本だけです。
- タイミングは Whisper のセグメントそのままです。大抵は問題ありませんが、
  たまに字幕エディタで微調整が要ります。
- デフォルトは CPU のみ。コード内の `device="cpu"` を `cuda` /
  `float16` に変えれば NVIDIA GPU も使えます。

## ライセンス

MIT。パイプラインの実測には Whisper プロジェクトでよく使われる
JFK の演説クリップ（パブリックドメインの録音）を使いました。
クリップ自体は同梱していません——発音のはっきりした短い音声なら
何でも試せます。
