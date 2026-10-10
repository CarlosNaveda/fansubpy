# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

fansubpy generates syllable-by-syllable karaoke subtitles (`.ass`, for Aegisub) from an audio/video file, then optionally applies animated FX via pyonfx. Code, comments, CLI output and docs are in Spanish — keep that convention.

## Setup & commands

Python 3.12, virtualenv in `.venv/`. External tools: FFmpeg on PATH (Whisper needs it), Aegisub for manual review.

```bash
pip install openai-whisper pyphen pyonfx

python init.py <Proyecto>                  # copies fansubs/plantilla/ → fansubs/<Proyecto>/
python main.py <Proyecto> [--vertical] [--no-lyrics]   # audio → timing/output_karaoke.ass
python fx/run.py <Proyecto>                # timing/output_karaoke.ass → timing/output_karaoke_fx.ass
python generate_readme.py                  # regenerate AUTO sections of README.md
```

There are no tests, linter, or build step.

The scripts print emojis. When running them from a non-UTF-8 Windows shell (cp1252), set `PYTHONIOENCODING=utf-8`; otherwise `print` raises `UnicodeEncodeError`.

## Architecture

The pipeline has three stages with a manual Aegisub step in the middle:

1. **`main.py` — timing.** Whisper (`MODEL_SIZE`, `LANGUAGE` in the config block at the top) transcribes with `word_timestamps=True`. Two modes:
   - *With lyrics* (first `.txt` in `fansubs/<P>/lyrics/`): lyric lines define the line breaks; `alinear_palabras` aligns lyric words to Whisper words with `difflib.SequenceMatcher`, interpolating timing for words Whisper missed.
   - *Without lyrics*: Whisper segments are split by `MAX_WORDS` / `MAX_DURATION` / punctuation.
   Each word is split into syllables with pyphen (languages in `PYPHEN_SUPPORTED`; otherwise per character, e.g. Japanese) and the word's duration is divided **equally** among its syllables as `{\kN}` tags. Output always uses style `Default`; `--vertical` only changes `PlayResX/Y` to 1080x1920.
2. **Aegisub (manual).** The user fixes timing, assigns styles, and sets each line's Effect field (e.g. `karaoke`). The `.ass` committed under `fansubs/*/timing/` is usually this hand-edited version, so don't overwrite it by rerunning `main.py` without being asked.
3. **`fx/run.py` — effects.** Loads the `.ass` with `pyonfx.Ass`, and for each line looks up `EFFECT_MAP[(line.style, line.effect.lower())]` to choose an effect function. pyonfx's default `keep_original=True` keeps the source lines as comments, so a line that matches no entry won't show up rendered in the output.

### FX layer (`fx/`)

- `fx/run.py` imports `effects` and `core` as **top-level packages** (`from core.constants import ...`) because it's run as a script and `fx/` lands on `sys.path`. Keep that import style inside `fx/`; don't switch to `fx.core`.
- Effect signature: `def effect(io, line)`. It iterates over `Utils.all_non_empty(line.syls)` and calls `io.write_line(frame)` once per `line.copy()` frame. Animation is frame-by-frame (`FRAME_MS` ≈ 60fps) with `\pos`/`\alpha`/colour tags, usually in phases: entry before `line.start_time` → wait → active syllable → after → exit (`POST_HIDE`).
- Shared tuning constants live in `fx/core/constants.py`; reusable particle generators (fragments, sparks, embers, ash, smoke, stars) live in `fx/core/particles.py` and are re-exported from `fx/core/__init__.py`.
- To add an effect, create `fx/effects/<name>.py`, export it in `fx/effects/__init__.py`, import it in `fx/run.py`, and map a style to it in `EFFECT_MAP`. The first line of the function's docstring becomes its description in the README's effects table.
- The README describes a 6-field protocol (palette, image, line entry, per-syllable effect, line exit, Aegisub style) for specifying new effects. Ask for any missing fields when someone requests a new effect.

### README auto-generation

`generate_readme.py` rewrites the parts of `README.md` between `<!-- AUTO:badges|estructura|efectos -->` markers, parsing `fx/effects/*.py` with `ast`. A GitHub Action (`.github/workflows/update-readme.yml`) runs it on pushes to `main` that touch `fx/effects/`, `main.py`, `init.py` or `generate_readme.py`, and commits the result. Don't hand-edit inside AUTO markers.

### Project folders

`fansubs/<Proyecto>/` holds `audio/` (media files are gitignored), `lyrics/`, `timing/` and `styles/styles.ass` (Aegisub style exports kept for reference; no code reads them). `*_fx.ass` and `*.pt` files are gitignored.
