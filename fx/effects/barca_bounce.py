import math
import random
from pyonfx import Utils
from core.constants import FRAME_MS, POST_HIDE

# ── Paleta Barça (BGR para ASS) ────────────────────────────────
C_APAGADO  = "&H00D0A99C"   # #9CA9D0 — líneas sin tocar
C_ACTIVO   = "&H00984D00"   # #004D98 — sílaba cantada
C_BURDEOS  = "&H004400A5"   # #A50044
C_DORADO   = "&H0000BBED"   # #EDBB00
C_AMARILLO = "&H0002EDFF"   # #FFED02
C_BLANCO   = "&H00FFFFFF"
C_BORDE    = "&H00000000"

PALETA_ESTRELLA = [C_BURDEOS, C_DORADO, C_AMARILLO, C_ACTIVO, C_BLANCO]

# ── Tiempos ────────────────────────────────────────────────────
ENTER_DUR   = 350   # ms entrada de la línea desde arriba
DROP_PX     = 50    # px que baja la línea en la entrada/salida
BOUNCE_H    = 70    # px que sube el logo tras impactar
TRAVEL_DUR  = 120   # ms que tarda el logo en viajar entre sílabas
STAR_COUNT  = 6     # estrellitas por impacto
STAR_DUR    = 350   # ms que duran las estrellitas

# ── CatCulé ────────────────────────────────────────────────────
CAT_SIZE           = 55      # escala del logo (fscx/fscy)
CAT_ENTER_Y_OFFSET = -220    # desde dónde cae el logo (relativo a Y del texto)


def barca_bounce(io, line):
    """
    Efecto Barça — CatCulé rebota de sílaba en sílaba con estrellitas de colores.
    Entrada: línea cae desde arriba en color apagado.
    Bounce: logo viaja de sílaba en sílaba, impacta, pinta de azul y genera estrellitas.
    Salida: línea cae hacia abajo con fade.
    """
    syls = list(Utils.all_non_empty(line.syls))
    if not syls:
        return

    line_start = line.start_time
    line_end   = line.end_time

    # ── FASE 0: Entrada — línea cae desde arriba, color apagado ──
    steps_enter    = max(4, ENTER_DUR // FRAME_MS)
    step_dur_enter = ENTER_DUR / steps_enter

    for syl in syls:
        x = syl.center
        y = syl.middle

        for s in range(steps_enter):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = line_start - ENTER_DUR + int(s * step_dur_enter)
            frame.end_time   = line_start - ENTER_DUR + int((s + 1) * step_dur_enter)

            t_norm    = s / steps_enter
            t_ease    = 1 - (1 - t_norm) ** 2   # ease out
            y_drop    = int((1 - t_ease) * DROP_PX)
            alpha_str = "&H%02X&" % int(255 * (1 - t_norm))

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur1\\bord2}"
            ) % (x, y - y_drop, C_APAGADO, C_BORDE, alpha_str) + syl.text
            io.write_line(frame)

    # ── FASE 1 + 2 + 3: Por sílaba ───────────────────────────────
    for i, syl in enumerate(syls):
        x = syl.center
        y = syl.middle
        syl_abs_start = line_start + syl.start_time
        syl_abs_end   = syl_abs_start + syl.duration

        # Espera pre-sílaba — color apagado
        wait_dur = syl_abs_start - line_start
        if wait_dur > 0:
            steps    = max(2, wait_dur // FRAME_MS)
            step_dur = wait_dur / steps

            for s in range(steps):
                frame            = line.copy()
                frame.layer      = 0
                frame.start_time = line_start + int(s * step_dur)
                frame.end_time   = line_start + int((s + 1) * step_dur)
                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\bord2\\blur0}"
                ) % (x, y, C_APAGADO, C_BORDE) + syl.text
                io.write_line(frame)

        # Sílaba activa — bounce del texto + color azul
        steps_active    = max(4, syl.duration // FRAME_MS)
        step_dur_active = syl.duration / steps_active

        for s in range(steps_active):
            frame            = line.copy()
            frame.layer      = 2
            frame.start_time = syl_abs_start + int(s * step_dur_active)
            frame.end_time   = syl_abs_start + int((s + 1) * step_dur_active)

            t_norm = s / steps_active
            if t_norm < 0.15:
                y_bump = -8
            elif t_norm < 0.35:
                y_bump = 5
            else:
                y_bump = 0

            if t_norm < 0.2:
                color, blur, bord = C_BLANCO, 3, 3
            else:
                color, blur, bord = C_ACTIVO, 0, 2

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur%d\\bord%d}"
            ) % (x, y + y_bump, color, C_BORDE, blur, bord) + syl.text
            io.write_line(frame)

        # Estrellitas en el punto de impacto
        _generate_stars(io, line, x, y, syl_abs_start)

        # Logo CatCulé
        _generate_catcule(io, line, syls, i, syl_abs_start, y)

        # Post-canto — sílaba ya cantada
        after_dur = line_end - syl_abs_end
        if after_dur > 0:
            steps    = max(2, after_dur // FRAME_MS)
            step_dur = after_dur / steps

            for s in range(steps):
                frame            = line.copy()
                frame.layer      = 0
                frame.start_time = syl_abs_end + int(s * step_dur)
                frame.end_time   = syl_abs_end + int((s + 1) * step_dur)
                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha&H70&\\bord1\\blur0}"
                ) % (x, y, C_ACTIVO, C_BORDE) + syl.text
                io.write_line(frame)

    # ── FASE 4: Salida — cae hacia abajo con fade ─────────────────
    steps_post    = max(4, POST_HIDE // FRAME_MS)
    step_dur_post = POST_HIDE / steps_post

    for syl in syls:
        x = syl.center
        y = syl.middle

        for s in range(steps_post):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = line_end + int(s * step_dur_post)
            frame.end_time   = line_end + int((s + 1) * step_dur_post)

            t_norm    = s / steps_post
            t_ease    = t_norm ** 1.5
            alpha_str = "&H%02X&" % int(255 * t_norm)

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur2\\bord1}"
            ) % (x, y + int(t_ease * DROP_PX), C_ACTIVO, C_BORDE, alpha_str) + syl.text
            io.write_line(frame)


# ── Helpers ────────────────────────────────────────────────────

def _generate_stars(io, line, impact_x, impact_y, impact_time):
    """Estrellitas de colores que explotan desde el punto de impacto."""
    shapes = ["★", "✦", "✧", "·", "•", "✶"]
    for _ in range(STAR_COUNT):
        star            = line.copy()
        star.layer      = 4
        star.start_time = impact_time
        star.end_time   = impact_time + STAR_DUR

        angle    = random.uniform(0, 2 * math.pi)
        distance = random.randint(25, 70)
        x_orig   = impact_x + random.randint(-10, 10)
        y_orig   = impact_y + random.randint(-10, 10)
        x_dest   = int(x_orig + math.cos(angle) * distance)
        y_dest   = int(y_orig + math.sin(angle) * distance)
        color    = random.choice(PALETA_ESTRELLA)
        size     = random.randint(28, 48)
        shape    = random.choice(shapes)

        star.text = (
            "{\\an5"
            "\\move(%d,%d,%d,%d)"
            "\\fad(0,%d)"
            "\\1c%s\\3c%s"
            "\\bord0\\shad0\\blur1"
            "\\fscx%d\\fscy%d}"
            "%s"
        ) % (
            x_orig, y_orig, x_dest, y_dest,
            STAR_DUR - 60,
            color, C_BORDE,
            size, size,
            shape
        )
        io.write_line(star)


def _generate_catcule(io, line, syls, syl_idx, syl_abs_start, text_y):
    """
    Genera el logo CatCule moviéndose hacia la silaba syl_idx.
    - Primera silaba: cae desde arriba.
    - Silabas siguientes: viaja en parabola desde la anterior.
    - Tras el impacto: rebota hacia arriba viajando a la siguiente.
    - Ultima silaba: sube y desaparece.
    """
    syl      = syls[syl_idx]
    target_x = int(syl.center)
    target_y = int(text_y - CAT_SIZE // 2 - 12)

    # Origen del viaje
    if syl_idx == 0:
        origin_x   = target_x
        origin_y   = target_y + CAT_ENTER_Y_OFFSET
        travel_dur = 300
    else:
        prev_syl   = syls[syl_idx - 1]
        origin_x   = int(prev_syl.center)
        origin_y   = int(text_y - CAT_SIZE // 2 - BOUNCE_H)
        travel_dur = TRAVEL_DUR

    # ── Viaje hacia la sílaba ──────────────────────────────────
    steps    = max(4, travel_dur // FRAME_MS)
    step_dur = travel_dur / steps

    for s in range(steps):
        frame            = line.copy()
        frame.layer      = 5
        frame.start_time = syl_abs_start - travel_dur + int(s * step_dur)
        frame.end_time   = syl_abs_start - travel_dur + int((s + 1) * step_dur)

        t_norm = s / steps
        t_ease = t_norm ** 1.8   # acelera al caer
        cur_x  = int(origin_x + (target_x - origin_x) * t_norm)
        cur_y  = int(origin_y + (target_y - origin_y) * t_ease)
        rot    = int(math.sin(t_norm * math.pi * 2) * 20)
        scale  = int(CAT_SIZE * (0.8 + 0.2 * t_norm))   # crece al acercarse

        frame.text = (
            "{\\an5\\pos(%d,%d)\\fscx%d\\fscy%d\\frz%d"
            "\\1c%s\\3c%s\\bord0\\shad0\\blur0}"
            "●"
        ) % (
            cur_x, cur_y,
            scale, scale,
            rot,
            random.choice([C_DORADO, C_BURDEOS]),
            C_BORDE
        )
        io.write_line(frame)

    # ── Bounce post-impacto ────────────────────────────────────
    if syl_idx < len(syls) - 1:
        next_syl       = syls[syl_idx + 1]
        next_abs_start = line.start_time + next_syl.start_time
        bounce_dur     = next_abs_start - syl_abs_start

        if bounce_dur > 0:
            steps_b    = max(4, bounce_dur // FRAME_MS)
            step_dur_b = bounce_dur / steps_b

            for s in range(steps_b):
                frame            = line.copy()
                frame.layer      = 5
                frame.start_time = syl_abs_start + int(s * step_dur_b)
                frame.end_time   = syl_abs_start + int((s + 1) * step_dur_b)

                t_norm = s / steps_b
                cur_x  = int(target_x + (next_syl.center - target_x) * t_norm)
                # parabola de rebote: sube y baja
                cur_y  = int(target_y - BOUNCE_H * math.sin(t_norm * math.pi))
                rot    = int(t_norm * 360)

                frame.text = (
                    "{\\an5\\pos(%d,%d)\\fscx%d\\fscy%d\\frz%d"
                    "\\1c%s\\3c%s\\bord0\\shad0\\blur0}"
                    "●"
                ) % (
                    cur_x, cur_y,
                    CAT_SIZE, CAT_SIZE,
                    rot,
                    random.choice([C_AMARILLO, C_DORADO]),
                    C_BORDE
                )
                io.write_line(frame)
    else:
        # Última sílaba: logo sube y desaparece
        exit_dur   = POST_HIDE
        steps_exit = max(4, exit_dur // FRAME_MS)
        step_dur_e = exit_dur / steps_exit

        for s in range(steps_exit):
            frame            = line.copy()
            frame.layer      = 5
            frame.start_time = syl_abs_start + int(s * step_dur_e)
            frame.end_time   = syl_abs_start + int((s + 1) * step_dur_e)

            t_norm    = s / steps_exit
            cur_y     = int(target_y - t_norm * BOUNCE_H * 2.5)
            alpha_str = "&H%02X&" % int(255 * t_norm)

            frame.text = (
                "{\\an5\\pos(%d,%d)\\fscx%d\\fscy%d"
                "\\alpha%s\\bord0\\shad0\\blur0\\1c%s\\3c%s}"
                "●"
            ) % (
                target_x, cur_y,
                CAT_SIZE, CAT_SIZE,
                alpha_str,
                C_DORADO, C_BORDE
            )
            io.write_line(frame)