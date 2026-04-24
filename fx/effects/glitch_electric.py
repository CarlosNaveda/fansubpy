import math
import random
from pyonfx import Utils
from core.constants import FRAME_MS, ENTER_DUR, POST_HIDE
from core.particles import generate_electric_sparks


def glitch_electric(io, line):
    """
    Aberración cromática eléctrica — 3 capas superpuestas (R/B offset + base).
    Entrada: barrido horizontal desde la izquierda.
    Espera: jitter cromático sutil con fantasmas ocasionales.
    Activa: destello blanco + split cromático con shake vertical seco.
    Salida: desvanece deslizando a la derecha.
    """
    color_base    = "&H8B3B18&"   # azul frío oscuro
    color_active  = "&HFFFFFF&"   # blanco eléctrico puro
    color_after   = "&HAA8B6E&"   # azul apagado post-canto
    color_border  = "&H000000&"   # borde negro
    color_glitch_r = "&H4A4AE2&"  # offset cálido (BGR)
    color_glitch_b = "&HCBE87A&"  # offset cian  (BGR)

    GLITCH_OFFSET = 8   # px de separación cromática
    SHAKE_FRAMES  = 3   # frames del shake inicial
    FLASH_DUR     = 32  # ms del destello blanco (~2 frames)

    syls = list(Utils.all_non_empty(line.syls))
    if not syls:
        return

    line_start = line.start_time
    line_end   = line.end_time

    for i, syl in enumerate(syls):
        x     = syl.center
        y     = syl.middle
        phase = i * (2 * math.pi / max(len(syls), 1)) * 0.7

        syl_abs_start = line_start + syl.start_time
        syl_abs_end   = syl_abs_start + syl.duration

        # ── FASE 0: Entrada — barrido horizontal desde izquierda ─
        steps_enter    = max(4, ENTER_DUR // FRAME_MS)
        step_dur_enter = ENTER_DUR / steps_enter

        for s in range(steps_enter):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = line_start - ENTER_DUR + int(s * step_dur_enter)
            frame.end_time   = line_start - ENTER_DUR + int((s + 1) * step_dur_enter)

            t_norm    = s / steps_enter
            x_slide   = int((1 - t_norm) * -60)
            alpha_str = "&H%02X&" % int(255 * (1 - t_norm))

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur1\\bord2}"
            ) % (x + x_slide, y, color_base, color_border, alpha_str) + syl.text
            io.write_line(frame)

            # Aberración cromática desde el 40% de la entrada
            if t_norm > 0.4:
                ghost            = line.copy()
                ghost.layer      = 0
                ghost.start_time = frame.start_time
                ghost.end_time   = frame.end_time
                ghost_alpha      = int(180 * (t_norm - 0.4) / 0.6)
                ghost.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur0\\bord0}"
                ) % (x + x_slide + GLITCH_OFFSET, y, color_glitch_r, color_border,
                     "&H%02X&" % (255 - ghost_alpha)) + syl.text
                io.write_line(ghost)

        # ── FASE 1: Espera — jitter cromático sutil ─────────────
        wait_dur = syl_abs_start - line_start
        if wait_dur > 0:
            steps    = max(2, wait_dur // FRAME_MS)
            step_dur = wait_dur / steps

            for s in range(steps):
                frame            = line.copy()
                frame.layer      = 0
                frame.start_time = line_start + int(s * step_dur)
                frame.end_time   = line_start + int((s + 1) * step_dur)

                jitter = random.choice([-1, 0, 0, 1]) * 2
                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur0\\bord2}"
                ) % (x + jitter, y, color_base, color_border) + syl.text
                io.write_line(frame)

                # Fantasma cromático cada ~4 frames
                if s % 4 == 0:
                    ghost            = line.copy()
                    ghost.layer      = 0
                    ghost.start_time = frame.start_time
                    ghost.end_time   = frame.end_time
                    ghost.text = (
                        "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha&HCC&\\blur0\\bord0}"
                    ) % (x + GLITCH_OFFSET // 2, y, color_glitch_b, color_border) + syl.text
                    io.write_line(ghost)

        # ── FASE 2: Activa — glitch cromático máximo ────────────

        # Sub-fase A: destello blanco inicial
        flash            = line.copy()
        flash.layer      = 4
        flash.start_time = syl_abs_start
        flash.end_time   = syl_abs_start + FLASH_DUR
        flash.text = (
            "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur4\\bord3}"
        ) % (x, y, color_active, "&HFFFFFF&") + syl.text
        io.write_line(flash)

        # Sub-fase B: split cromático con shake
        steps_active    = max(4, syl.duration // FRAME_MS)
        step_dur_active = syl.duration / steps_active

        for s in range(steps_active):
            frame_start = syl_abs_start + int(s * step_dur_active)
            frame_end   = syl_abs_start + int((s + 1) * step_dur_active)
            t_norm      = s / steps_active

            glitch_intensity = int(GLITCH_OFFSET * (1 - t_norm * 0.5))
            shake_y = random.choice([-10, 8, -6, 10, -8]) if s < SHAKE_FRAMES \
                      else random.choice([-2, 0, 0, 2])

            if t_norm < 0.15:
                color_main, blur_v, bord_v = color_active, 0, 3
            elif t_norm < 0.5:
                color_main, blur_v, bord_v = "&HE8E87A&", 0, 2
            else:
                color_main, blur_v, bord_v = "&HDD993B&", 0, 2

            r_alpha_str = "&H%02X&" % (255 - int(220 * (1 - t_norm * 0.6)))

            # Capa R — offset derecho
            r_layer            = line.copy()
            r_layer.layer      = 2
            r_layer.start_time = frame_start
            r_layer.end_time   = frame_end
            r_layer.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur0\\bord0}"
            ) % (x + glitch_intensity + random.choice([0, 2, -1]),
                 y + shake_y, color_glitch_r, color_border, r_alpha_str) + syl.text
            io.write_line(r_layer)

            # Capa B — offset izquierdo
            b_layer            = line.copy()
            b_layer.layer      = 2
            b_layer.start_time = frame_start
            b_layer.end_time   = frame_end
            b_layer.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur0\\bord0}"
            ) % (x - glitch_intensity + random.choice([0, -2, 1]),
                 y + shake_y, color_glitch_b, color_border, r_alpha_str) + syl.text
            io.write_line(b_layer)

            # Capa base — centro
            base            = line.copy()
            base.layer      = 3
            base.start_time = frame_start
            base.end_time   = frame_end
            base.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur%d\\bord%d}"
            ) % (x, y + shake_y, color_main, color_border, blur_v, bord_v) + syl.text
            io.write_line(base)

        generate_electric_sparks(io, line, syl)

        # ── FASE 3: Post-canto — azul apagado con glitch residual ─
        after_dur = line_end - syl_abs_end
        if after_dur > 0:
            steps    = max(2, after_dur // FRAME_MS)
            step_dur = after_dur / steps

            for s in range(steps):
                frame            = line.copy()
                frame.layer      = 0
                frame.start_time = syl_abs_end + int(s * step_dur)
                frame.end_time   = syl_abs_end + int((s + 1) * step_dur)

                residual = GLITCH_OFFSET // 3 if s % 6 == 0 else 0
                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha&HA0&\\blur0\\bord1}"
                ) % (x + residual, y, color_after, color_border) + syl.text
                io.write_line(frame)

        # ── FASE 4: Salida — desvanece deslizando a la derecha ───
        steps_post    = max(4, POST_HIDE // FRAME_MS)
        step_dur_post = POST_HIDE / steps_post

        for s in range(steps_post):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = line_end + int(s * step_dur_post)
            frame.end_time   = line_end + int((s + 1) * step_dur_post)

            t_norm    = s / steps_post
            alpha_str = "&H%02X&" % int(255 * t_norm)

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur1\\bord1}"
            ) % (x + int(t_norm * 40), y, color_after, color_border, alpha_str) + syl.text
            io.write_line(frame)
