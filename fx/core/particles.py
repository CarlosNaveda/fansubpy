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


def generate_ember_burst(io, line, x, y, width, start_time, paleta, count=10, dur=650):
    """
    Brasas que suben desde un punto dado, con flicker y encogimiento
    progresivo — como chispas que se desprenden de una llama.
    Punto de emisión genérico (no atado al centro de la sílaba) para
    poder lanzarlas desde el frente de quemado en movimiento.
    """
    shapes = ["•", "·", "✦"]

    for _ in range(count):
        ember            = line.copy()
        ember.layer      = 3
        ember.start_time = start_time + random.randint(0, 80)
        ember.end_time   = ember.start_time + dur

        x_orig = x + random.randint(-int(width // 2), int(width // 2))
        y_orig = y + random.randint(-4, 4)
        rise   = random.randint(40, 110)
        drift  = random.randint(-20, 20)
        x_dest = x_orig + drift
        y_dest = y_orig - rise

        color = random.choice(paleta)
        size  = random.randint(14, 30)
        shape = random.choice(shapes)

        ember.text = (
            "{\\an5"
            "\\move(%d,%d,%d,%d)"
            "\\fad(20,%d)"
            "\\bord0\\shad0"
            "\\1c%s"
            "\\alpha&H20&"
            "\\blur1"
            "\\fscx%d\\fscy%d}"
            "%s"
        ) % (
            x_orig, y_orig, x_dest, y_dest,
            dur - 60,
            color,
            size, size,
            shape
        )
        io.write_line(ember)


def generate_smoke(io, line, x, y, width, start_time, paleta, count=8, dur=750):
    """
    Humo que se desprende del frente de quemado — manchas grises,
    difusas, que suben y se expanden mientras se desvanecen.
    A diferencia de las brasas, no brilla: es opaco y blando.
    """
    for _ in range(count):
        puff            = line.copy()
        puff.layer      = 3
        puff.start_time = start_time + random.randint(0, 150)
        puff.end_time   = puff.start_time + dur

        x_orig = x + random.randint(-int(width // 2), int(width // 2))
        y_orig = y + random.randint(-4, 4)
        rise   = random.randint(70, 160)
        drift  = random.randint(-30, 30)
        x_dest = x_orig + drift
        y_dest = y_orig - rise

        color     = random.choice(paleta)
        size0     = random.randint(16, 24)
        size1     = size0 + random.randint(40, 65)
        grow_dur  = dur - random.randint(0, 80)

        puff.text = (
            "{\\an5"
            "\\move(%d,%d,%d,%d)"
            "\\fad(40,%d)"
            "\\bord0\\shad0"
            "\\1c%s"
            "\\alpha&H38&"
            "\\blur6"
            "\\fscx%d\\fscy%d"
            "\\t(0,%d,\\fscx%d\\fscy%d)}"
            "●"
        ) % (
            x_orig, y_orig, x_dest, y_dest,
            dur - 100,
            color,
            size0, size0,
            grow_dur, size1, size1
        )
        io.write_line(puff)


def generate_embers(io, line, syl, paleta, count=22, dur=650):
    """Brasas que suben desde el centro de la sílaba al encenderse."""
    generate_ember_burst(
        io, line, syl.center, syl.middle, syl.width,
        line.start_time + syl.start_time,
        paleta, count, dur
    )


def generate_ash_flakes(io, line, syl, color, start_time, count=16, dur=550):
    """
    Ceniza que se desprende y cae al consumirse la sílaba por completo —
    motas oscuras que caen con leve giro y se desvanecen.
    """
    x = syl.center
    y = syl.middle

    for _ in range(count):
        flake            = line.copy()
        flake.layer      = 3
        flake.start_time = start_time + random.randint(0, 120)
        flake.end_time   = flake.start_time + dur

        x_orig = x + random.randint(-int(syl.width // 2), int(syl.width // 2))
        y_orig = y + random.randint(-int(syl.height // 2), int(syl.height // 2))
        fall   = random.randint(40, 90)
        drift  = random.randint(-15, 15)
        x_dest = x_orig + drift
        y_dest = y_orig + fall

        size = random.randint(10, 20)
        rot  = random.randint(0, 360)

        flake.text = (
            "{\\an5"
            "\\move(%d,%d,%d,%d)"
            "\\fad(0,%d)"
            "\\bord0\\shad0"
            "\\1c%s"
            "\\alpha&H40&"
            "\\blur0\\frz%d"
            "\\fscx%d\\fscy%d}"
            "."
        ) % (
            x_orig, y_orig, x_dest, y_dest,
            dur - 100,
            color,
            rot,
            size, size
        )
        io.write_line(flake)


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
