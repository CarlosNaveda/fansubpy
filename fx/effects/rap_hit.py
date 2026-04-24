import math
import random
from pyonfx import Utils
from core.constants import FRAME_MS, ENTER_DUR, DROP_PX, WAVE_AMP, POST_HIDE
from core.particles import generate_fragments


def rap_hit(io, line):
    """
    Golpes secos sin onda sinusoidal — feel de rap.
    Entrada: sube desde abajo. Espera: jitter seco.
    Activa: posiciones fijas que simulan impacto.
    Salida: sube y desaparece.
    """
    color_base   = "&H3B3B3B&"
    color_active = "&HF2F2F2&"
    color_white  = "&HFFFFFF&"
    color_after  = "&H969696&"
    color_border = "&H000000&"
    color_shadow = "&H969696&"

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

        # ── FASE 0: Entrada — sube desde abajo ──────────────────
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
            ) % (x, y + y_drop + y_off, color_base, color_border, alpha_str) + syl.text
            io.write_line(frame)

        # ── FASE 1: Espera — jitter seco ────────────────────────
        wait_dur = syl_abs_start - line_start
        if wait_dur > 0:
            steps    = max(2, wait_dur // FRAME_MS)
            step_dur = wait_dur / steps

            for s in range(steps):
                frame            = line.copy()
                frame.layer      = 0
                frame.start_time = line_start + int(s * step_dur)
                frame.end_time   = line_start + int((s + 1) * step_dur)

                y_off = random.choice([-2, 0, 2])
                frame.text = (
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\4c%s\\bord3\\blur0\\shad0}"
                ) % (x, y + y_off, color_base, color_border, color_shadow) + syl.text
                io.write_line(frame)

        # ── FASE 2: Activa — golpes secos ────────────────────────
        steps_active    = max(3, syl.duration // FRAME_MS)
        step_dur_active = syl.duration / steps_active

        for s in range(steps_active):
            frame            = line.copy()
            frame.layer      = 2
            frame.start_time = syl_abs_start + int(s * step_dur_active)
            frame.end_time   = syl_abs_start + int((s + 1) * step_dur_active)

            t_norm = s / steps_active

            if t_norm < 0.2:
                y_off, color = -16, color_active
            elif t_norm < 0.4:
                y_off, color = 8,   color_white
            elif t_norm < 0.7:
                y_off, color = -4,  color_active
            else:
                y_off, color = 0,   color_active

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\4c%s\\bord3\\blur0\\shad0}"
            ) % (x, y + y_off, color, color_border, color_shadow) + syl.text
            io.write_line(frame)

        generate_fragments(io, line, syl, color_active)

        # ── FASE 3: Post-canto — muerto total ───────────────────
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
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\4c%s\\alpha&H90&\\bord2\\blur0\\shad0}"
                ) % (x, y, color_after, color_border, color_shadow) + syl.text
                io.write_line(frame)

        # ── FASE 4: Salida — sube y desaparece ──────────────────
        steps_post    = max(4, POST_HIDE // FRAME_MS)
        step_dur_post = POST_HIDE / steps_post

        for s in range(steps_post):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = line_end + int(s * step_dur_post)
            frame.end_time   = line_end + int((s + 1) * step_dur_post)

            t_norm    = s / steps_post
            y_off     = int(math.sin(t_norm * 2 * math.pi + phase) * WAVE_AMP)
            y_drop    = int((t_norm ** 0.7) * DROP_PX)
            alpha_str = "&H%02X&" % int(255 * (t_norm ** 1.3))

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur2\\bord1}"
            ) % (x, y + y_off - y_drop, color_after, color_border, alpha_str) + syl.text
            io.write_line(frame)
