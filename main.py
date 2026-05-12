import argparse
import sys
import unicodedata
from pathlib import Path

import whisper
import pyphen

# ── Configuración ──────────────────────────────────────────────
MODEL_SIZE   = "medium"
LANGUAGE     = None   # Whisper detecta el idioma automáticamente
MAX_WORDS    = 8      # máx palabras por línea en modo sin lyrics
MAX_DURATION = 4.0    # máx segundos por línea en modo sin lyrics
# ──────────────────────────────────────────────────────────────

PYPHEN_SUPPORTED = {"es", "en", "fr", "de", "it", "pt", "nl", "ru", "pl", "cs", "sk", "hu"}


def get_dic(lang: str):
    """Retorna diccionario pyphen si el idioma está soportado, si no None."""
    if lang in PYPHEN_SUPPORTED:
        try:
            return pyphen.Pyphen(lang=lang)
        except Exception:
            return None
    return None


def silabear(palabra: str, dic) -> list:
    lang_mode = "pyphen" if dic else "char"

    # Japonés y coreano: separar por carácter (mora/sílaba gráfica)
    if lang_mode == "char":
        chars = [c for c in palabra if not unicodedata.category(c).startswith('Z')]
        return chars if chars else [palabra]

    # Idiomas con pyphen
    limpia = ''.join(c for c in palabra if c.isalpha())
    if not limpia:
        return [palabra]
    silabas = dic.inserted(limpia, hyphen="|").split("|")
    return silabas if silabas else [palabra]


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
    texto = texto.lower()
    texto = ''.join(c for c in texto if c.isalpha() or c.isspace())
    return texto.strip()


def generar_ass_header(vertical: bool = False):
    res_x, res_y = (1080, 1920) if vertical else (1920, 1080)
    return f"""\
[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def buscar_audio(base: Path) -> Path:
    """Busca el primer archivo de audio soportado en audio/."""
    audio_dir = base / "audio"
    for ext in ("*.mp3", "*.mp4", "*.wav", "*.m4a", "*.flac"):
        archivos = list(audio_dir.glob(ext))
        if archivos:
            return archivos[0]
    return None


def alinear_palabras(lyric_words, whisper_words):
    import difflib

    lyric_norm   = [normalizar(w) for w in lyric_words]
    whisper_norm = [normalizar(w["word"]) for w in whisper_words]
    matcher      = difflib.SequenceMatcher(None, lyric_norm, whisper_norm)
    resultado    = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op in ("equal", "replace"):
            lyric_chunk = lyric_words[i1:i2]
            whisper_chunk = whisper_words[j1:j2]
            for k, palabra in enumerate(lyric_chunk):
                if k < len(whisper_chunk):
                    w = whisper_chunk[k]
                    # Verificar que la palabra no sea muy diferente (posible palabra perdida)
                    lnorm = normalizar(palabra)
                    wnorm = normalizar(w["word"])
                    similitud = difflib.SequenceMatcher(None, lnorm, wnorm).ratio()
                    if similitud > 0.4 or op == "equal":
                        resultado.append({"word": palabra, "start": w["start"], "end": w["end"]})
                    else:
                        # Whisper tiene una palabra muy diferente — interpolar timing
                        prev = resultado[-1] if resultado else {"start": w["start"], "end": w["start"]}
                        gap = (w["start"] - prev["end"]) / (len(lyric_chunk) - k)
                        t = prev["end"]
                        for palabra_extra in lyric_chunk[k:]:
                            resultado.append({
                                "word": palabra_extra,
                                "start": round(t, 3),
                                "end": round(t + gap, 3),
                            })
                        break
                else:
                    prev = resultado[-1] if resultado else {"start": 0, "end": 0}
                    resultado.append({"word": palabra, "start": prev["end"], "end": prev["end"] + 0.3})
        elif op == "delete":
            for palabra in lyric_words[i1:i2]:
                prev = resultado[-1] if resultado else {"start": 0, "end": 0}
                resultado.append({"word": palabra, "start": prev["end"], "end": prev["end"] + 0.3})

    return resultado


# ── Modo sin lyrics ────────────────────────────────────────────

def dividir_segmento(segmento: dict) -> list:
    words    = segmento.get("words", [])
    duration = segmento["end"] - segmento["start"]

    if not words:
        return []

    if len(words) <= MAX_WORDS and duration <= MAX_DURATION:
        return [{"words": words}]

    lineas = []
    chunk  = []
    for w in words:
        chunk.append(w)
        es_corte_natural = w["word"].strip().endswith((",", ".", ";", "...", "?", "!"))
        if len(chunk) >= MAX_WORDS or es_corte_natural:
            lineas.append({"words": chunk})
            chunk = []
    if chunk:
        lineas.append({"words": chunk})

    return lineas


def segmentos_a_lineas(segments: list) -> list:
    lineas = []
    for seg in segments:
        for linea in dividir_segmento(seg):
            words = linea["words"]
            if not words:
                continue
            lineas.append({
                "start": words[0]["start"],
                "end":   words[-1]["end"],
                "words": words,
            })
    return lineas


def escribir_linea_ass(f, linea: dict, dic):
    start     = ms_to_ass_time(linea["start"] * 1000)
    end       = ms_to_ass_time(linea["end"]   * 1000)
    resultado = ""

    for w in linea["words"]:
        texto   = w["word"].strip()
        dur_ms  = (w["end"] - w["start"]) * 1000
        silabas = silabear(texto, dic)

        if len(silabas) <= 1:
            resultado += f"{{\\k{int(dur_ms) // 10}}}{texto} "
        else:
            dur_sil = dur_ms / len(silabas)
            for sil in silabas:
                resultado += f"{{\\k{int(dur_sil) // 10}}}{sil}"
            resultado += " "

    f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{resultado.strip()}\n")


# ── Runner principal ───────────────────────────────────────────

def run(song: str, no_lyrics: bool = False, vertical: bool = False):
    base = Path(__file__).parent / "fansubs" / song

    audio_path = buscar_audio(base)
    if not audio_path:
        print(f"❌ No se encontró audio (.mp3/.mp4/.wav/.m4a/.flac) en {base / 'audio'}")
        sys.exit(1)

    lyrics_files = list((base / "lyrics").glob("*.txt"))
    usar_lyrics  = not no_lyrics and bool(lyrics_files)

    if not usar_lyrics and not no_lyrics and not lyrics_files:
        print("⚠️  No se encontró .txt en lyrics/ → usando modo Whisper automático")

    output_path = base / "timing" / "output_karaoke.ass"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🎵 Audio:  {audio_path.name}")
    print(f"🔧 Modo:   {'con lyrics' if usar_lyrics else 'Whisper automático'}")

    # ── Transcribir con Whisper ────────────────────────────────
    print(f"🤖 Cargando modelo Whisper '{MODEL_SIZE}'...")
    model  = whisper.load_model(MODEL_SIZE)
    result = model.transcribe(
        str(audio_path),
        language=LANGUAGE,
        word_timestamps=True,
        verbose=False,
    )

    detected_lang = result.get("language", "es")
    dic           = get_dic(detected_lang)
    silabeo_modo  = "pyphen" if dic else "por carácter"
    print(f"🌐 Idioma detectado: {detected_lang} | Silabeo: {silabeo_modo}")
    print(f"🔍 {len(result['segments'])} segmentos detectados por Whisper")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(generar_ass_header(vertical))

        if usar_lyrics:
            # ── Modo con lyrics ────────────────────────────────
            lyric_path    = lyrics_files[0]
            print(f"📄 Lyrics: {lyric_path.name}")

            lineas_lyric  = [l.strip() for l in lyric_path.read_text(encoding="utf-8").splitlines() if l.strip()]
            palabras_flat = []
            indices_linea = []

            for linea in lineas_lyric:
                palabras = linea.split()
                inicio   = len(palabras_flat)
                palabras_flat.extend(palabras)
                indices_linea.append((inicio, len(palabras_flat)))

            print(f"📝 {len(lineas_lyric)} líneas / {len(palabras_flat)} palabras en lyric")

            palabras_whisper = [
                {"word": w["word"].strip(), "start": w["start"], "end": w["end"]}
                for seg in result["segments"]
                for w in seg.get("words", [])
            ]

            print(f"🔍 {len(palabras_whisper)} palabras detectadas por Whisper")
            print("⚙️  Alineando...")

            palabras_alineadas = alinear_palabras(palabras_flat, palabras_whisper)

            for ini, fin in indices_linea:
                if ini >= len(palabras_alineadas):
                    continue
                words_seg = palabras_alineadas[ini:min(fin, len(palabras_alineadas))]
                if not words_seg:
                    continue

                start_t   = ms_to_ass_time(words_seg[0]["start"]  * 1000)
                end_t     = ms_to_ass_time(words_seg[-1]["end"]   * 1000)
                resultado = ""

                for w in words_seg:
                    dur_ms  = (w["end"] - w["start"]) * 1000
                    silabas = silabear(w["word"], dic)
                    if len(silabas) <= 1:
                        resultado += f"{{\\k{int(dur_ms) // 10}}}{w['word']} "
                    else:
                        dur_sil = dur_ms / len(silabas)
                        for sil in silabas:
                            resultado += f"{{\\k{int(dur_sil) // 10}}}{sil}"
                        resultado += " "

                f.write(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{resultado.strip()}\n")

        else:
            # ── Modo sin lyrics ────────────────────────────────
            print(f"⚙️  Dividiendo segmentos (máx {MAX_WORDS} palabras / {MAX_DURATION}s por línea)...")
            lineas = segmentos_a_lineas(result["segments"])
            print(f"📝 {len(lineas)} líneas generadas")

            for linea in lineas:
                escribir_linea_ass(f, linea, dic)

    print(f"✅ Generado: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de timeos karaoke con Whisper")
    parser.add_argument("song", help="Nombre de la carpeta en fansubs/ (ej: LinkinPark-InTheEnd)")
    parser.add_argument("--no-lyrics",action="store_true",help="Ignorar el archivo de lyrics y usar Whisper directamente",)
    parser.add_argument("--vertical",action="store_true",help="Genera el header para video vertical (1080x1920)",)
    args = parser.parse_args()
    run(args.song, no_lyrics=args.no_lyrics, vertical=args.vertical)