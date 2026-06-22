import sys
import argparse
from pathlib import Path
from pyonfx import Ass

from effects import wave, rap_hit, glitch_electric, barca_bounce, inner_fire


# ── Mapa (estilo ASS, efecto ASS) → función ──────────────────────
# Edita este diccionario para cada canción si los estilos cambian.
EFFECT_MAP = {
    ("Chester",      "karaoke"): wave,
    ("Shinoda",      "karaoke"): rap_hit,
    ("Chester+Hard", "karaoke"): glitch_electric,
    ("Barza",        "karaoke"): barca_bounce,
    ("Fire",         "karaoke"): inner_fire,
}


def run(song: str):
    base   = Path(__file__).parent.parent / "fansubs" / song / "timing"
    input_ = base / "output_karaoke.ass"
    output = base / "output_karaoke_fx.ass"

    if not input_.exists():
        print(f"❌ No se encontró: {input_}")
        sys.exit(1)

    print(f"📂 Procesando: {input_}")

    io = Ass(str(input_), str(output))
    _, _, lines = io.get_data()

    processed = 0
    for line in lines:
        key = (line.style, line.effect.lower())
        fn  = EFFECT_MAP.get(key)
        if fn:
            fn(io, line)
            processed += 1

    io.save()
    print(f"✅ {processed} líneas procesadas → {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de efectos karaoke pyonfx")
    parser.add_argument("song", help="Nombre de la carpeta en fansubs/ (ej: linkin-park-in-the-end)")
    args = parser.parse_args()
    run(args.song)
