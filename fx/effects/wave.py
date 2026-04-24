import math
from pyonfx import Utils
from core.constants import FRAME_MS, ENTER_DUR, DROP_PX, WAVE_AMP, ACTIVE_AMP, POST_HIDE
from core.particles import generate_fragments


def wave(io, line):
    """
    Ola suave con sacudida vertical en sílaba activa.
    Entrada: cae desde arriba. Salida: baja y desaparece.
    Partículas en abanico al explotar cada sílaba.
    """
    color_base   = "&H136262&"
    color_active = "&H2AD5D5&"
    color_white  = "&HFFFFFF&"
    color_after  = "&H9DECEC&"
    color_border = "&H77E4E4&"

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

        # ── FASE 0: Entrada — cae desde arriba ──────────────────
        steps_enter    = max(4, ENTER_DUR // FRAME_MS)
        step_dur_enter = ENTER_DUR / steps_enter

        for s in range(steps_enter):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = line_start - ENTER_DUR + int(s * step_dur_enter)
            frame.end_time   = line_start - ENTER_DUR + int((s + 1) * step_dur_enter)

            t_norm    = s / steps_enter
            y_off     = int(math.sin(t_norm * 2 * math.pi + phase) * WAVE_AMP)
            y_drop    = int((1 - t_norm) * DROP_PX)
            alpha_str = "&H%02X&" % int(255 * (1 - t_norm))

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur2\\bord2}"
            ) % (x, y - y_drop + y_off, color_base, color_border, alpha_str) + syl.text
            io.write_line(frame)

        # ── FASE 1: Espera — ondea hasta que se canta ───────────
        wait_dur = syl_abs_start - line_start
        if wait_dur > 0:
            steps    = max(2, wait_dur // FRAME_MS)
            step_dur = wait_dur / steps

            for s in range(steps):
                frame            = line.copy()
                frame.layer      = 0
                frame.start_time = line_start + int(s * step_dur)
                frame.end_time   = line_start + int((s + 1) * step_dur)

                y_off = int(math.sin(s / steps * 4 * math.pi + phase) * WAVE_AMP)
                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur1\\bord2}"
                ) % (x, y + y_off, color_base, color_border) + syl.text
                io.write_line(frame)

        # ── FASE 2: Sílaba activa — sacudida vertical fuerte ────
        steps_active    = max(4, syl.duration // FRAME_MS)
        step_dur_active = syl.duration / steps_active

        for s in range(steps_active):
            frame            = line.copy()
            frame.layer      = 2
            frame.start_time = syl_abs_start + int(s * step_dur_active)
            frame.end_time   = syl_abs_start + int((s + 1) * step_dur_active)

            t_norm = s / steps_active
            amp    = ACTIVE_AMP * (1 - t_norm * 0.5)
            y_off  = int(math.sin(t_norm * 6 * math.pi + phase) * amp)

            if t_norm < 0.2:
                color, blur, bord = color_active, 3, 3
            elif t_norm < 0.5:
                color, blur, bord = color_white, 1, 3
            else:
                color, blur, bord = color_active, 2, 2

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur%d\\bord%d}"
            ) % (x, y + y_off, color, color_border, blur, bord) + syl.text
            io.write_line(frame)

        generate_fragments(io, line, syl, color_active)

        # ── FASE 3: Post-canto — relleno apagado ────────────────
        after_dur = line_end - syl_abs_end
        if after_dur > 0:
            steps    = max(2, after_dur // FRAME_MS)
            step_dur = after_dur / steps

            for s in range(steps):
                frame            = line.copy()
                frame.layer      = 0
                frame.start_time = syl_abs_end + int(s * step_dur)
                frame.end_time   = syl_abs_end + int((s + 1) * step_dur)

                y_off = int(math.sin(s / steps * 4 * math.pi + phase + math.pi) * (WAVE_AMP * 0.6))
                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha&H90&\\blur1\\bord1}"
                ) % (x, y + y_off, color_after, color_border) + syl.text
                io.write_line(frame)

        # ── FASE 4: Salida — baja y desaparece ──────────────────
        steps_post    = max(4, POST_HIDE // FRAME_MS)
        step_dur_post = POST_HIDE / steps_post

        for s in range(steps_post):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = line_end + int(s * step_dur_post)
            frame.end_time   = line_end + int((s + 1) * step_dur_post)

            t_norm    = s / steps_post
            y_off     = int(math.sin(t_norm * 2 * math.pi + phase) * WAVE_AMP)
            alpha_str = "&H%02X&" % int(255 * t_norm)

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur2\\bord1}"
            ) % (x, y + y_off + int(t_norm * DROP_PX), color_after, color_border, alpha_str) + syl.text
            io.write_line(frame)
