"""
Uso:
    python main.py <carpeta_cancion>

Ejemplo:
    python main.py linkin-park-in-the-end

Lee:    ../fansubs/<carpeta_cancion>/audio/<nombre>.mp3
        ../fansubs/<carpeta_cancion>/lyrics/<nombre>.txt
Genera: ../fansubs/<carpeta_cancion>/timings/output_karaoke.ass
"""

import argparse
import sys
from pathlib import Path

import whisper
import pyphen

# ── Configuración ──────────────────────────────────────────────
MODEL_SIZE = "medium"
LANGUAGE   = "en"
# ──────────────────────────────────────────────────────────────

dic = pyphen.Pyphen(lang="es")


def silabear(palabra):
    limpia = ''.join(c for c in palabra if c.isalpha())
    if not limpia:
        return [palabra]
    return dic.inserted(limpia, hyphen="|").split("|")


def ms_to_ass_time(ms):
    ms = int(ms)
    h  = ms // 3_600_000
    ms %= 3_600_000
    m  = ms // 60_000
    ms %= 60_000
    s  = ms // 1_000
    cs = (ms % 1_000) // 10
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def normalizar(texto):
    import unicodedata
    texto = texto.lower()
    texto = ''.join(c for c in texto if c.isalpha() or c.isspace())
    return texto.strip()


def generar_ass_header():
    return """\
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def alinear_palabras(lyric_words, whisper_words):
    import difflib

    lyric_norm   = [normalizar(w) for w in lyric_words]
    whisper_norm = [normalizar(w["word"]) for w in whisper_words]
    matcher      = difflib.SequenceMatcher(None, lyric_norm, whisper_norm)
    resultado    = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op in ("equal", "replace"):
            lyric_chunk   = lyric_words[i1:i2]
            whisper_chunk = whisper_words[j1:j2]
            for k, palabra in enumerate(lyric_chunk):
                if k < len(whisper_chunk):
                    w = whisper_chunk[k]
                    resultado.append({"word": palabra, "start": w["start"], "end": w["end"]})
                else:
                    prev = resultado[-1] if resultado else {"start": 0, "end": 0}
                    resultado.append({"word": palabra, "start": prev["end"], "end": prev["end"] + 0.3})
        elif op == "delete":
            for palabra in lyric_words[i1:i2]:
                prev = resultado[-1] if resultado else {"start": 0, "end": 0}
                resultado.append({"word": palabra, "start": prev["end"], "end": prev["end"] + 0.3})

    return resultado


def run(song: str):
    base = Path(__file__).parent.parent / "fansubs" / song

    # Busca el primer .mp3 en audio/ y el primer .txt en lyrics/
    audio_files  = list((base / "audio").glob("*.mp3"))
    lyrics_files = list((base / "lyrics").glob("*.txt"))

    if not audio_files:
        print(f"❌ No se encontró .mp3 en {base / 'audio'}")
        sys.exit(1)
    if not lyrics_files:
        print(f"❌ No se encontró .txt en {base / 'lyrics'}")
        sys.exit(1)

    audio_path  = audio_files[0]
    lyric_path  = lyrics_files[0]
    output_path = base / "timings" / "output_karaoke.ass"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🎵 Audio:  {audio_path.name}")
    print(f"📄 Lyrics: {lyric_path.name}")

    # ── Cargar lyric ───────────────────────────────────────────
    lineas_lyric    = [l.strip() for l in lyric_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    palabras_flat   = []
    indices_linea   = []

    for linea in lineas_lyric:
        palabras = linea.split()
        inicio   = len(palabras_flat)
        palabras_flat.extend(palabras)
        indices_linea.append((inicio, len(palabras_flat)))

    print(f"📝 {len(lineas_lyric)} líneas / {len(palabras_flat)} palabras en lyric")

    # ── Transcribir con Whisper ────────────────────────────────
    print(f"🤖 Cargando modelo Whisper '{MODEL_SIZE}'...")
    model  = whisper.load_model(MODEL_SIZE)
    result = model.transcribe(str(audio_path), language=LANGUAGE, word_timestamps=True, verbose=False)

    palabras_whisper = [
        {"word": w["word"].strip(), "start": w["start"], "end": w["end"]}
        for seg in result["segments"]
        for w in seg.get("words", [])
    ]
    print(f"🔍 {len(palabras_whisper)} palabras detectadas por Whisper")

    # ── Alinear y generar ASS ──────────────────────────────────
    print("⚙️  Alineando...")
    palabras_alineadas = alinear_palabras(palabras_flat, palabras_whisper)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(generar_ass_header())

        for ini, fin in indices_linea:
            if ini >= len(palabras_alineadas):
                continue

            words_seg = palabras_alineadas[ini:min(fin, len(palabras_alineadas))]
            if not words_seg:
                continue

            start     = ms_to_ass_time(words_seg[0]["start"]  * 1000)
            end       = ms_to_ass_time(words_seg[-1]["end"]   * 1000)
            resultado = ""

            for w in words_seg:
                dur_ms  = (w["end"] - w["start"]) * 1000
                silabas = silabear(w["word"])

                if len(silabas) <= 1:
                    resultado += f"{{\\k{int(dur_ms) // 10}}}{w['word']} "
                else:
                    dur_sil = dur_ms / len(silabas)
                    for sil in silabas:
                        resultado += f"{{\\k{int(dur_sil) // 10}}}{sil}"
                    resultado += " "

            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{resultado.strip()}\n")

    print(f"✅ Generado: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de timeos karaoke con Whisper")
    parser.add_argument("song", help="Nombre de la carpeta en fansubs/ (ej: linkin-park-in-the-end)")
    args = parser.parse_args()
    run(args.song)
