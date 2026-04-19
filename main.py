import whisper
import pyphen
from pathlib import Path

# ── Configuración ──────────────────────────────────────────────
AUDIO_PATH  = r"C:\Carlos\Videos\Fansubs\Susana Cala - Tiempo indefinido.mp3"
LYRIC_PATH  = r"C:\Carlos\Videos\Fansubs\Susana Cala - Tiempo Indefinido_Lyric.txt"
OUTPUT_ASS  = "output_karaoke.ass"
MODEL_SIZE  = "medium"
LANGUAGE    = "es"
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
    """Quita puntuación y pasa a minúsculas para comparar."""
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

def construir_karaoke(palabras_con_tiempo, palabras_lyric):
    """
    palabras_con_tiempo: lista de dicts {word, start, end} de Whisper
    palabras_lyric: lista de palabras originales del lyric (con tildes, mayúsculas, etc.)
    """
    resultado = ""
    for i, w in enumerate(palabras_con_tiempo):
        # Usar el texto del lyric si está disponible, sino el de Whisper
        texto = palabras_lyric[i] if i < len(palabras_lyric) else w["word"].strip()
        dur_ms = (w["end"] - w["start"]) * 1000
        silabas = silabear(texto)

        if len(silabas) <= 1:
            cs = int(dur_ms) // 10
            resultado += f"{{\\k{cs}}}{texto} "
        else:
            dur_por_silaba = dur_ms / len(silabas)
            for sil in silabas:
                cs = int(dur_por_silaba) // 10
                resultado += f"{{\\k{cs}}}{sil}"
            resultado += " "

    return resultado.strip()


def alinear_palabras(lyric_words, whisper_words):
    """
    Alineamiento dinámico: busca la mejor correspondencia
    entre palabras del lyric y timestamps de Whisper.
    """
    import difflib

    lyric_norm = [normalizar(w) for w in lyric_words]
    whisper_norm = [normalizar(w["word"]) for w in whisper_words]

    matcher = difflib.SequenceMatcher(None, lyric_norm, whisper_norm)

    resultado = []  # lista de {word_lyric, start, end}

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal" or op == "replace":
            # Mapear cada palabra lyric a su correspondiente whisper
            lyric_chunk = lyric_words[i1:i2]
            whisper_chunk = whisper_words[j1:j2]
            for k, palabra in enumerate(lyric_chunk):
                if k < len(whisper_chunk):
                    w = whisper_chunk[k]
                    resultado.append({"word": palabra, "start": w["start"], "end": w["end"]})
                else:
                    # Sin match, interpolamos desde el anterior
                    prev = resultado[-1] if resultado else {"start": 0, "end": 0}
                    resultado.append({"word": palabra, "start": prev["end"], "end": prev["end"] + 0.3})
        elif op == "delete":
            # Palabra en lyric sin match en whisper — interpolamos
            for palabra in lyric_words[i1:i2]:
                prev = resultado[-1] if resultado else {"start": 0, "end": 0}
                resultado.append({"word": palabra, "start": prev["end"], "end": prev["end"] + 0.3})
        # "insert" = palabra extra en Whisper, la ignoramos

    return resultado


# ── Cargar lyric ───────────────────────────────────────────────
lineas_lyric = [l.strip() for l in Path(LYRIC_PATH).read_text(encoding="utf-8").splitlines() if l.strip()]
print(f"Lyric cargado: {len(lineas_lyric)} líneas")

# Aplanar todas las palabras del lyric en orden
palabras_lyric_flat = []
indices_linea = []  # (inicio, fin) de cada línea en la lista plana
for linea in lineas_lyric:
    palabras = linea.split()
    inicio = len(palabras_lyric_flat)
    palabras_lyric_flat.extend(palabras)
    indices_linea.append((inicio, len(palabras_lyric_flat)))

print(f"Total palabras en lyric: {len(palabras_lyric_flat)}")

# ── Transcribir con Whisper ────────────────────────────────────
print(f"Cargando modelo '{MODEL_SIZE}'...")
model = whisper.load_model(MODEL_SIZE)

print("Transcribiendo con word timestamps...")
result = model.transcribe(
    AUDIO_PATH,
    language=LANGUAGE,
    word_timestamps=True,
    verbose=False
)

# Aplanar todas las palabras de Whisper
palabras_whisper = []
for seg in result["segments"]:
    for w in seg.get("words", []):
        palabras_whisper.append({
            "word": w["word"].strip(),
            "start": w["start"],
            "end": w["end"]
        })

print(f"Total palabras detectadas por Whisper: {len(palabras_whisper)}")

# ── Alinear lyric con whisper ──────────────────────────────────
print("Alineando palabras...")
palabras_alineadas = alinear_palabras(palabras_lyric_flat, palabras_whisper)

# ── Generar ASS respetando líneas del lyric ───────────────────
print("Generando ASS karaoke...")
with open(OUTPUT_ASS, "w", encoding="utf-8") as f:
    f.write(generar_ass_header())

    for idx_linea, (ini, fin) in enumerate(indices_linea):
        if ini >= len(palabras_alineadas):
            continue

        fin_real  = min(fin, len(palabras_alineadas))
        words_seg = palabras_alineadas[ini:fin_real]

        if not words_seg:
            continue

        start = ms_to_ass_time(words_seg[0]["start"]  * 1000)
        end   = ms_to_ass_time(words_seg[-1]["end"]   * 1000)

        resultado = ""
        for w in words_seg:
            texto   = w["word"]
            dur_ms  = (w["end"] - w["start"]) * 1000
            silabas = silabear(texto)

            if len(silabas) <= 1:
                cs = int(dur_ms) // 10
                resultado += f"{{\\k{cs}}}{texto} "
            else:
                dur_por_silaba = dur_ms / len(silabas)
                for sil in silabas:
                    cs = int(dur_por_silaba) // 10
                    resultado += f"{{\\k{cs}}}{sil}"
                resultado += " "

        f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{resultado.strip()}\n")

print(f"✅ Listo: {OUTPUT_ASS}")