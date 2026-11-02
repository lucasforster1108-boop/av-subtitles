[English](README.md) | [简体中文](README_zh.md) | [日本語](README_ja.md) | [한국어](README_ko.md)

# av-subtitles

라이브러리에 있는 영상 중 절반쯤은 자막이 없습니다. 특히 일본어 영상이요.
절반만 알아들으면서 보는 데 지쳐서, 영상을 넣으면 자막 파일을 돌려주는
이 도구를 만들었습니다.

구조는 단순합니다:

```
영상 ──ffmpeg──▶ 16kHz 모노 wav ──faster-whisper──▶ .srt
                                                 └──선택──▶ 번역본 .srt
```

## 하는 일

- ffmpeg로 오디오를 뽑고 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)로
  받아씁니다. 언어는 자동 감지되고, `--lang ja`처럼 고정할 수도 있습니다.
- 영상 옆에 평범한 SRT를 만듭니다: `movie.ja.srt`
- `--translate en`을 주면 Whisper 자체 translate 태스크로 영어 자막도 나옵니다.
- `--translate zh`는 로컬 Argos Translate로 중국어 자막을 만드는데,
  **직접 설치했을 때만** 됩니다(아래 참고). 없으면 속이지 않고
  오류를 내고 멈춥니다.

## 설치

Python 3.9+와 PATH에 잡힌 ffmpeg가 필요합니다.

```bash
# ffmpeg가 아직 없다면:
sudo apt install ffmpeg        # Debian/Ubuntu
brew install ffmpeg            # macOS

pip install -r requirements.txt
```

Whisper 모델은 처음 실행할 때 자동으로 다운로드됩니다.

## 사용법

```bash
# 언어 자동 감지
python subs.py movie.mp4

# 일본어인 걸 알면 고정하기
python subs.py movie.mp4 --lang ja

# 영어 자막도 함께 출력
python subs.py movie.mp4 --lang ja --translate en

# 중국어 자막도 함께 출력 (Argos 필요, 아래 참고)
python subs.py movie.mp4 --lang ja --translate zh

# 모델과 출력 경로 지정
python subs.py movie.mp4 --model small -o subs/movie.srt
```

| 옵션 | 의미 |
| --- | --- |
| `--lang` | 입력 언어 코드(`ja`, `en`, `zh` 등). 기본값은 자동 감지 |
| `--translate en\|zh` | 번역 자막도 추가로 출력 |
| `--model` | Whisper 모델 크기. 기본값 `base` |
| `-o` | 원어 SRT 출력 경로 |

`-o`를 안 주면 파일 이름은 이렇게 됩니다:

- `movie.<언어>.srt` — 받아쓰기 결과
- `movie.en.translated.srt` / `movie.zh.translated.srt` — 번역 결과

SRT를 영상과 같은 이름으로 옆에 두면 VLC, mpv, IINA, Stash, Jellyfin
같은 플레이어들이 알아서 불러옵니다.

## 모델 크기와 CPU 기준 기대치

기본은 CPU(int8) 실행입니다. 모델 욕심은 금물:

| 모델 | 다운로드 | CPU에서의 체감 |
| --- | --- | --- |
| `tiny` | 약 75 MB | 아주 빠르지만 거침이 눈에 띔 |
| `base` | 약 145 MB | 짧은 클립에는 충분. 기본값이 이거 |
| `small` | 약 470 MB | 확실히 좋아지고 확실히 느려짐 |
| `medium` / `large-v3` | 약 1.5 GB / 약 3 GB | 오래 기다려야 함. 이 급은 GPU 빌드를 추천 |

몇 분짜리 클립은 평범한 노트북 CPU에서 `base`로 문제없습니다.
2시간짜리 영상은 `tiny`/`base`를 걸어 놓고 차나 한잔하거나,
큰 모델로 밤새 돌리세요. 일본어 정확도는 `base`에서 `small`로
올릴 때 체감이 큽니다.

## 번역 기능의 실제 범위

- **영어(`--translate en`)**: Whisper 내장 translate 태스크.
  입력이 무슨 언어든 출력은 영어입니다. 발음이 또렷하면 괜찮고,
  속어나 겹치는 목소리에서는 흔들립니다.
- **중국어(`--translate zh`)**:
  [Argos Translate](https://github.com/argosopentech/argos-translate)로
  완전히 오프라인 번역하지만, `requirements.txt`에는 **넣지 않았습니다**.
  무겁고 모두에게 필요한 것도 아니라서요. 켜려면:

  ```bash
  pip install argostranslate
  argospm update
  argospm install translate-en_zh   # 입력이 일본어면 translate-ja_en도
  ```

  Argos가 없으면 중국어도 없습니다. 대신 도구는 이 설치 방법을
  그대로 알려 주고 멈춥니다. 되는 척하지 않습니다.

## 한계

- 정확도는 음질이 결정합니다. 배경음악이 크거나, 여러 명이 동시에
  말하거나, 발음이 뭉개지면 그 부분은 무너집니다. 모델을 키우면
  나아지지만 완전히 고쳐지지는 않습니다.
- 화자 분리도, 화자 표시도 없습니다. 자막은 한 줄기뿐입니다.
- 타이밍은 Whisper 세그먼트 그대로입니다. 대개는 괜찮지만 가끔은
  자막 편집기에서 한두 줄 손봐야 합니다.
- 기본값은 CPU 전용입니다. 코드의 `device="cpu"`를 `cuda` /
  `float16`으로 바꾸면 NVIDIA GPU도 쓸 수 있습니다.

## 라이선스

MIT. 파이프라인 실측에는 Whisper 프로젝트에서 흔히 쓰는 JFK 연설
클립(퍼블릭 도메인 녹음)을 썼습니다. 클립 자체는 포함되어 있지
않으니, 발음이 또렷한 짧은 오디오 아무거나로 직접 시험해 보세요.
