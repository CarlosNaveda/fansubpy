import math
import random
from .constants import FRAG_DROP, FRAG_DUR


def generate_fragments(io, line, syl, color):
    """Abanico de puntos que caen al terminar la sílaba."""
    x = syl.center
    y = syl.middle
    frag_start = line.start_time + syl.start_time + syl.duration

    for _ in range(80):
        frag            = line.copy()
        frag.layer      = 3
        frag.start_time = frag_start
        frag.end_time   = frag_start + FRAG_DUR

        angle_rad = math.radians(random.uniform(200, 340))
        distance  = random.randint(30, FRAG_DROP)
        x_orig    = x + random.randint(-int(syl.width // 3), int(syl.width // 3))
        y_orig    = y + random.randint(-5, 5)

        frag.text = (
            "{\\an5"
            "\\move(%d,%d,%d,%d)"
            "\\fad(30,%d)"
            "\\bord0\\shad0"
            "\\1c%s"
            "\\alpha&H10&"
            "\\blur0"
            "\\fscx36\\fscy36}"
            "."
        ) % (
            x_orig, y_orig,
            int(x_orig + math.cos(angle_rad) * distance),
            int(y_orig + math.sin(angle_rad) * distance),
            FRAG_DUR - 80,
            color
        )
        io.write_line(frag)


def generate_electric_sparks(io, line, syl):
    """Chispas horizontales como interferencia eléctrica."""
    x = syl.center
    y = syl.middle
    spark_start = line.start_time + syl.start_time + syl.duration

    for _ in range(60):
        spark            = line.copy()
        spark.layer      = 3
        spark.start_time = spark_start
        spark.end_time   = spark_start + 600

        if random.choice([True, False]):
            angle_deg = random.uniform(340, 380)
        else:
            angle_deg = random.uniform(160, 200)

        angle_rad = math.radians(angle_deg)
        distance  = random.randint(20, 70)
        x_orig    = x + random.randint(-int(syl.width // 4), int(syl.width // 4))
        y_orig    = y + random.randint(-4, 4)

        spark.text = (
            "{\\an5"
            "\\move(%d,%d,%d,%d)"
            "\\fad(10,580)"
            "\\bord0\\shad0"
            "\\1c%s"
            "\\alpha&H08&"
            "\\blur0"
            "\\fscx28\\fscy28}"
            "."
        ) % (
            x_orig, y_orig,
            int(x_orig + math.cos(angle_rad) * distance),
            int(y_orig + math.sin(angle_rad) * distance),
            random.choice(["&HFFFFFF&", "&HCBE87A&", "&HE8E87A&"])
        )
        io.write_line(spark)


def generate_stars(
    io, line,
    impact_x, impact_y, impact_time,
    count=6,
    dur=350,
    paleta=None,
    size_range=(28, 48),
    dist_range=(25, 70),
    blur=1,
    border_color="&H00000000",
):
    """
    Estrellitas de colores que explotan desde un punto de impacto.
    Reutilizable por cualquier efecto — parámetros completamente configurables.

    Args:
        io, line        : contexto pyonfx
        impact_x/y      : coordenadas del punto de impacto
        impact_time     : tiempo absoluto de inicio (ms)
        count           : cantidad de estrellitas
        dur             : duración en ms
        paleta          : lista de colores ASS BGR (ej. ["&H00FFFFFF&", ...])
        size_range      : (min, max) escala fscx/fscy
        dist_range      : (min, max) distancia de vuelo en px
        blur            : valor de blur
        border_color    : color del borde (por defecto negro)
    """
    if paleta is None:
        paleta = ["&H00FFFFFF&"]

    shapes = ["★", "✦", "✧", "·", "•", "✶"]

    for _ in range(count):
        star            = line.copy()
        star.layer      = 4
        star.start_time = impact_time
        star.end_time   = impact_time + dur

        angle    = random.uniform(0, 2 * math.pi)
        distance = random.randint(*dist_range)
        x_orig   = impact_x + random.randint(-10, 10)
        y_orig   = impact_y + random.randint(-10, 10)
        x_dest   = int(x_orig + math.cos(angle) * distance)
        y_dest   = int(y_orig + math.sin(angle) * distance)
        color    = random.choice(paleta)
        size     = random.randint(*size_range)
        shape    = random.choice(shapes)

        star.text = (
            "{\\an5"
            "\\move(%d,%d,%d,%d)"
            "\\fad(0,%d)"
            "\\1c%s\\3c%s"
            "\\bord0\\shad0\\blur%d"
            "\\fscx%d\\fscy%d}"
            "%s"
        ) % (
            x_orig, y_orig, x_dest, y_dest,
            dur - 60,
            color, border_color,
            blur,
            size, size,
            shape
        )
        io.write_line(star)
