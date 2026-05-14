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
C_ORO_VIP  = "&H0000D4FF"   # dorado más brillante para Messi/Ronaldinho

PALETA_ESTRELLA     = [C_BURDEOS, C_DORADO, C_AMARILLO, C_ACTIVO, C_BLANCO]
PALETA_ESTRELLA_VIP = [C_ORO_VIP, C_AMARILLO, C_BLANCO, C_DORADO]

# ── Sílabas VIP — easter egg (hardcoded por canción) ──────────
# Messi: Mes, si / Ronaldinho: Ro, nal, din, ho
SILABAS_VIP = {"Mes", "si", "Ro", "nal", "din", "ho"}

# ── Tiempos ────────────────────────────────────────────────────
ENTER_DUR    = 350   # ms entrada de la línea desde arriba
EXIT_EARLY   = 180   # ms antes del end que empieza la salida (punto 3)
DROP_PX      = 50    # px que baja la línea en la entrada/salida
BOUNCE_H     = 70    # px que sube el logo tras impactar
TRAVEL_DUR   = 120   # ms que tarda el logo en viajar entre sílabas
STAR_COUNT   = 6     # estrellitas normales por impacto
STAR_COUNT_VIP = 12  # estrellitas VIP (doble)
STAR_DUR     = 350   # ms que duran las estrellitas
STAR_DUR_VIP = 500   # ms estrellitas VIP (más largas)

# ── Bolitas ────────────────────────────────────────────────────
BALL_SIZE           = 55
BALL_ENTER_Y_OFFSET = -220


def barca_bounce(io, line):
    """
    Efecto Barça — Bolitas que rebotan de sílaba en sílaba con estrellitas de colores.
    Entrada: línea cae desde arriba en color apagado.
    Bounce: logo viaja de sílaba en sílaba, impacta, pinta de azul y genera estrellitas.
    Easter egg: Messi y Ronaldinho tienen estrellitas doradas dobles.
    Salida: línea empieza a bajar EXIT_EARLY ms antes del end.
    """
    syls = list(Utils.all_non_empty(line.syls))
    if not syls:
        return

    line_start  = line.start_time
    line_end    = line.end_time
    exit_start  = line_end - EXIT_EARLY   # punto 3: salida anticipada

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
            t_ease    = 1 - (1 - t_norm) ** 2
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

        es_vip = False
        sil_key = syl.text.strip()
        if sil_key in {"Mes", "Ro", "nal", "din", "ho"}:
            es_vip = True
        elif sil_key == "si":
            # "si" solo es VIP si la sílaba anterior fue "Mes"
            sil_prev = syls[i - 1].text.strip() if i > 0 else ""
            es_vip = sil_prev == "Mes"

        # Espera pre-sílaba — color apagado
        # Solo hasta exit_start para no solapar con la salida anticipada
        wait_dur = min(syl_abs_start, exit_start) - line_start
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

        # Sílaba activa — bounce del texto + color
        if syl_abs_start < exit_start:
            active_end      = min(syl_abs_end, exit_start)
            active_dur      = active_end - syl_abs_start
            steps_active    = max(4, active_dur // FRAME_MS)
            step_dur_active = active_dur / steps_active

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
                    # VIP: flash dorado en vez de blanco
                    color = C_ORO_VIP if es_vip else C_BLANCO
                    blur, bord = 3, 3
                else:
                    color = C_ORO_VIP if es_vip else C_ACTIVO
                    blur, bord = 0, 2

                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur%d\\bord%d}"
                ) % (x, y + y_bump, color, C_BORDE, blur, bord) + syl.text
                io.write_line(frame)

        # Estrellitas — VIP tiene doble cantidad, más grandes y solo doradas
        _generate_stars(io, line, x, y, syl_abs_start, vip=es_vip)

        # Bolitas
        _generate_balls(io, line, syls, i, syl_abs_start, y, exit_start)

        # Post-canto — VIP queda dorado, normales en azul apagado
        after_start = syl_abs_end
        after_end   = min(exit_start, line_end)
        after_dur   = after_end - after_start
        if after_dur > 0:
            steps    = max(2, after_dur // FRAME_MS)
            step_dur = after_dur / steps

            color_post = C_ORO_VIP if es_vip else C_ACTIVO

            for s in range(steps):
                frame            = line.copy()
                frame.layer      = 0
                frame.start_time = after_start + int(s * step_dur)
                frame.end_time   = after_start + int((s + 1) * step_dur)
                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha&H70&\\bord1\\blur0}"
                ) % (x, y, color_post, C_BORDE) + syl.text
                io.write_line(frame)

    # ── FASE 4: Salida anticipada — empieza EXIT_EARLY ms antes del end ──
    exit_dur      = EXIT_EARLY + POST_HIDE
    steps_post    = max(4, exit_dur // FRAME_MS)
    step_dur_post = exit_dur / steps_post

    for i, syl in enumerate(syls):
        x = syl.center
        y = syl.middle

        # Detectar VIP para la salida
        sil_key    = syl.text.strip()
        sil_prev   = syls[i - 1].text.strip() if i > 0 else ""
        es_vip_sal = sil_key in {"Mes", "Ro", "nal", "din", "ho"} or \
                     (sil_key == "si" and sil_prev == "Mes")
        color_sal  = C_ORO_VIP if es_vip_sal else C_ACTIVO

        for s in range(steps_post):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = exit_start + int(s * step_dur_post)
            frame.end_time   = exit_start + int((s + 1) * step_dur_post)

            t_norm    = s / steps_post
            t_ease    = t_norm ** 1.5
            alpha_str = "&H%02X&" % int(255 * t_norm)

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur2\\bord1}"
            ) % (x, y + int(t_ease * DROP_PX), color_sal, C_BORDE, alpha_str) + syl.text
            io.write_line(frame)

    # ── Glow respirando post-Messi ─────────────────────────────────
    # Arranca cuando se termina de cantar "si" (última sílaba de Messi)
    _generate_messi_glow(io, line, syls, exit_start)


# ── Helpers ────────────────────────────────────────────────────

def _generate_messi_glow(io, line, syls, exit_start):
    """
    Glow dorado pulsante sobre sílabas VIP completas (Messi y Ronaldinho)
    una vez que se terminó de cantar cada palabra completa.
    """
    GLOW_PERIOD = 600
    BLUR_MIN    = 1
    BLUR_MAX    = 8

    # Detectar secuencias VIP completas en la línea
    # Messi: Mes + si / Ronaldinho: Ro + nal + din + ho
    VIP_SEQUENCES = [
        ["Mes", "si"],
        ["Ro", "nal", "din", "ho"],
    ]

    for sequence in VIP_SEQUENCES:
        # Buscar la secuencia en las sílabas
        vip_syls = []
        seq_idx  = 0
        for syl in syls:
            if syl.text.strip() == sequence[seq_idx]:
                vip_syls.append(syl)
                seq_idx += 1
                if seq_idx == len(sequence):
                    break  # secuencia completa encontrada
            else:
                # reset si se rompe la secuencia
                vip_syls = []
                seq_idx  = 0
                if syl.text.strip() == sequence[0]:
                    vip_syls.append(syl)
                    seq_idx = 1

        if len(vip_syls) < len(sequence):
            continue  # secuencia no encontrada en esta línea

        # Glow arranca cuando termina la última sílaba de la palabra
        last_syl   = vip_syls[-1]
        glow_start = line.start_time + last_syl.start_time + last_syl.duration
        glow_end   = exit_start

        if glow_end <= glow_start:
            continue

        glow_dur = glow_end - glow_start
        steps    = max(4, glow_dur // FRAME_MS)
        step_dur = glow_dur / steps

        for syl in vip_syls:
            x = syl.center
            y = syl.middle

            for s in range(steps):
                frame            = line.copy()
                frame.layer      = 3
                frame.start_time = glow_start + int(s * step_dur)
                frame.end_time   = glow_start + int((s + 1) * step_dur)

                t_norm = s / steps
                breath = (math.sin(t_norm * 2 * math.pi * (glow_dur / GLOW_PERIOD)) + 1) / 2
                blur   = int(BLUR_MIN + breath * (BLUR_MAX - BLUR_MIN))

                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur%d\\bord2}"
                ) % (x, y, C_ORO_VIP, C_BORDE, blur) + syl.text
                io.write_line(frame)



def _generate_stars(io, line, impact_x, impact_y, impact_time, vip=False):
    """
    Estrellitas de colores desde el punto de impacto.
    VIP (Messi/Ronaldinho): doble cantidad, más grandes, más lejos, solo doradas.
    """
    shapes     = ["★", "✦", "✧", "·", "•", "✶"]
    count      = STAR_COUNT_VIP if vip else STAR_COUNT
    paleta     = PALETA_ESTRELLA_VIP if vip else PALETA_ESTRELLA
    size_range = (45, 72) if vip else (28, 48)
    dist_range = (40, 100) if vip else (25, 70)

    if vip:
        # VIP: duran 3x la duración de la sílaba, con tope en el fin de la línea
        syl_dur = line.end_time - impact_time  # tiempo restante de la línea
        dur = min(STAR_DUR_VIP * 3, syl_dur) if syl_dur > 0 else STAR_DUR_VIP
    else:
        dur = STAR_DUR

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
        blur_val = 2 if vip else 1  # más glow en VIP

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
            color, C_BORDE,
            blur_val,
            size, size,
            shape
        )
        io.write_line(star)


def _generate_balls(io, line, syls, syl_idx, syl_abs_start, text_y, exit_start):
    """Bolitas moviéndose entre sílabas. Se detiene si llega exit_start."""
    syl      = syls[syl_idx]
    target_x = int(syl.center)
    target_y = int(text_y - BALL_SIZE // 2 - 12)

    if syl_idx == 0:
        origin_x   = target_x
        origin_y   = target_y + BALL_ENTER_Y_OFFSET
        travel_dur = 300
    else:
        prev_syl   = syls[syl_idx - 1]
        origin_x   = int(prev_syl.center)
        origin_y   = int(text_y - BALL_SIZE // 2 - BOUNCE_H)
        travel_dur = TRAVEL_DUR

    # Viaje hacia la sílaba
    steps    = max(4, travel_dur // FRAME_MS)
    step_dur = travel_dur / steps

    for s in range(steps):
        t_start = syl_abs_start - travel_dur + int(s * step_dur)
        t_end   = syl_abs_start - travel_dur + int((s + 1) * step_dur)
        if t_start >= exit_start:
            break

        frame            = line.copy()
        frame.layer      = 5
        frame.start_time = t_start
        frame.end_time   = min(t_end, exit_start)

        t_norm = s / steps
        t_ease = t_norm ** 1.8
        cur_x  = int(origin_x + (target_x - origin_x) * t_norm)
        cur_y  = int(origin_y + (target_y - origin_y) * t_ease)
        rot    = int(math.sin(t_norm * math.pi * 2) * 20)
        scale  = int(BALL_SIZE * (0.8 + 0.2 * t_norm))

        frame.text = (
            "{\\an5\\pos(%d,%d)\\fscx%d\\fscy%d\\frz%d"
            "\\1c%s\\3c%s\\bord0\\shad0\\blur0}"
            "●"
        ) % (
            cur_x, cur_y, scale, scale, rot,
            random.choice([C_DORADO, C_BURDEOS]), C_BORDE
        )
        io.write_line(frame)

    # Bounce post-impacto
    if syl_idx < len(syls) - 1:
        next_syl       = syls[syl_idx + 1]
        next_abs_start = line.start_time + next_syl.start_time
        bounce_dur     = next_abs_start - syl_abs_start

        if bounce_dur > 0:
            steps_b    = max(4, bounce_dur // FRAME_MS)
            step_dur_b = bounce_dur / steps_b

            for s in range(steps_b):
                t_start = syl_abs_start + int(s * step_dur_b)
                if t_start >= exit_start:
                    break

                frame            = line.copy()
                frame.layer      = 5
                frame.start_time = t_start
                frame.end_time   = min(syl_abs_start + int((s + 1) * step_dur_b), exit_start)

                t_norm = s / steps_b
                cur_x  = int(target_x + (next_syl.center - target_x) * t_norm)
                cur_y  = int(target_y - BOUNCE_H * math.sin(t_norm * math.pi))
                rot    = int(t_norm * 360)

                frame.text = (
                    "{\\an5\\pos(%d,%d)\\fscx%d\\fscy%d\\frz%d"
                    "\\1c%s\\3c%s\\bord0\\shad0\\blur0}"
                    "●"
                ) % (
                    cur_x, cur_y, BALL_SIZE, BALL_SIZE, rot,
                    random.choice([C_AMARILLO, C_DORADO]), C_BORDE
                )
                io.write_line(frame)
    else:
        # Última sílaba: logo sube y desaparece
        exit_dur   = POST_HIDE
        steps_exit = max(4, exit_dur // FRAME_MS)
        step_dur_e = exit_dur / steps_exit

        for s in range(steps_exit):
            t_start = syl_abs_start + int(s * step_dur_e)
            if t_start >= exit_start:
                break

            frame            = line.copy()
            frame.layer      = 5
            frame.start_time = t_start
            frame.end_time   = min(syl_abs_start + int((s + 1) * step_dur_e), exit_start)

            t_norm    = s / steps_exit
            cur_y     = int(target_y - t_norm * BOUNCE_H * 2.5)
            alpha_str = "&H%02X&" % int(255 * t_norm)

            frame.text = (
                "{\\an5\\pos(%d,%d)\\fscx%d\\fscy%d"
                "\\alpha%s\\bord0\\shad0\\blur0\\1c%s\\3c%s}"
                "●"
            ) % (
                target_x, cur_y, BALL_SIZE, BALL_SIZE,
                alpha_str, C_DORADO, C_BORDE
            )
            io.write_line(frame)