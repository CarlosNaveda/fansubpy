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
