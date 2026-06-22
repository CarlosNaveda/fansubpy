import random
from pyonfx import Utils
from core.constants import (
    FRAME_MS, ENTER_DUR, FIRE_RISE_PX, BURN_BAND, BURN_JITTER_X, BURN_JITTER_Y,
    ASH_DUR, COOL_DUR, CRUMBLE_DUR, CRUMBLE_FALL, CRUMBLE_ROT,
)
from core.particles import generate_ember_burst, generate_ash_flakes, generate_smoke


def inner_fire(io, line):
    """
    Fuego interior — la sílaba se quema de verdad al cantarse.
    Entrada: aparece como ceniza apagada. Espera: papel/carbón frío
    a la espera de la chispa. Activa: una franja de llama recorre el
    glifo de abajo hacia arriba (clip en 3 bandas, con rojo mezclado
    entre el naranja y el blanco), dejando carbón quemado detrás y
    brasas saltando desde el frente de fuego. Apenas termina de
    cantarse, la sílaba se enfría y se desmorona: cae, gira y se
    encoge mientras suelta motas de ceniza, sin esperar a que
    termine la línea.
    """
    color_ash      = "&H1E1ED8&"  # rojo del título original, sin quemar todavía
    color_char     = "&H05050A&"  # carbón quemado, casi negro
    color_white    = "&HFFFFFF&"  # núcleo de la llama
    color_flame    = "&H1478FF&"  # naranja de fuego
    color_red      = "&H1414DC&"  # rojo de brasa mezclado en la llama
    color_gold     = "&H3CC8FF&"  # borde dorado de la llama
    border_ash     = "&H000000&"
    border_char    = "&H000000&"

    color_smoke    = "&H3A3A3A&"  # humo gris medio
    color_smoke2   = "&H585858&"  # humo gris claro, más visible

    flame_choices = [color_white, color_flame, color_flame, color_red, color_red, color_gold]
    paleta_embers = [color_flame, color_red]
    paleta_smoke  = [color_smoke, color_smoke2, color_smoke2]

    syls = list(Utils.all_non_empty(line.syls))
    if not syls:
        return

    line_start = line.start_time

    for syl in syls:
        x      = syl.center
        y      = syl.middle
        left   = syl.left
        right  = syl.right
        top    = syl.top
        bottom = syl.bottom

        syl_abs_start = line_start + syl.start_time
        syl_abs_end   = syl_abs_start + syl.duration

        # ── FASE 0: Entrada — aparece como ceniza apagada ───────
        steps_enter    = max(4, ENTER_DUR // FRAME_MS)
        step_dur_enter = ENTER_DUR / steps_enter

        for s in range(steps_enter):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = line_start - ENTER_DUR + int(s * step_dur_enter)
            frame.end_time   = line_start - ENTER_DUR + int((s + 1) * step_dur_enter)

            t_norm    = s / steps_enter
            y_rise    = int((1 - t_norm) * FIRE_RISE_PX)
            alpha_str = "&H%02X&" % int(255 * (1 - t_norm))
            blur      = 3 * (1 - t_norm)

            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\alpha%s\\blur%.1f\\bord1}"
            ) % (x, y + y_rise, color_ash, border_ash, alpha_str, blur) + syl.text
            io.write_line(frame)

        # ── FASE 1: Espera — papel/carbón frío, quieto ──────────
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
                    "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur0\\bord1}"
                ) % (x, y, color_ash, border_ash) + syl.text
                io.write_line(frame)

        # ── FASE 2: Activa — la llama recorre el glifo abajo→arriba ──
        steps_active    = max(6, syl.duration // FRAME_MS)
        step_dur_active = syl.duration / steps_active
        half_band       = BURN_BAND / 2
        ember_every     = max(1, steps_active // 3)

        for s in range(steps_active):
            t0 = syl_abs_start + int(s * step_dur_active)
            t1 = syl_abs_start + int((s + 1) * step_dur_active)
            t_norm = s / steps_active

            # vibración de calor — desplaza por igual texto y recortes
            jx = random.randint(-BURN_JITTER_X, BURN_JITTER_X)
            jy = random.randint(-BURN_JITTER_Y, BURN_JITTER_Y)

            y_burn      = bottom - t_norm * (bottom - top)
            band_top    = max(top, y_burn - half_band) + jy
            band_bottom = min(bottom, y_burn + half_band) + jy

            # carbón ya quemado (debajo de la franja de llama)
            if band_bottom < bottom + jy:
                burnt            = line.copy()
                burnt.layer      = 1
                burnt.start_time = t0
                burnt.end_time   = t1
                burnt.text = (
                    "{\\an5\\pos(%d,%d)\\clip(%d,%d,%d,%d)\\1c%s\\3c%s\\blur1\\bord1}"
                ) % (x + jx, y + jy, left - 1 + jx, band_bottom, right + 1 + jx, bottom + 2 + jy, color_char, border_char) + syl.text
                io.write_line(burnt)

            # franja de llama activa, con flicker de color
            flame            = line.copy()
            flame.layer      = 2
            flame.start_time = t0
            flame.end_time   = t1
            flame_color = random.choice(flame_choices)
            flame.text = (
                "{\\an5\\pos(%d,%d)\\clip(%d,%d,%d,%d)\\1c%s\\3c%s\\blur2\\bord0\\shad0}"
            ) % (x + jx, y + jy, left - 2 + jx, band_top, right + 2 + jx, band_bottom, flame_color, border_char) + syl.text
            io.write_line(flame)

            # papel aún sin quemar (arriba de la franja)
            if band_top > top + jy:
                unburnt            = line.copy()
                unburnt.layer      = 0
                unburnt.start_time = t0
                unburnt.end_time   = t1
                unburnt.text = (
                    "{\\an5\\pos(%d,%d)\\clip(%d,%d,%d,%d)\\1c%s\\3c%s\\blur0\\bord1}"
                ) % (x + jx, y + jy, left - 1 + jx, top - 2 + jy, right + 1 + jx, band_top, color_ash, border_ash) + syl.text
                io.write_line(unburnt)

            if s % ember_every == 0:
                generate_ember_burst(
                    io, line, x, y_burn, syl.width, t0,
                    paleta_embers, count=3, dur=350
                )
                generate_smoke(
                    io, line, x, y_burn, syl.width, t0,
                    paleta_smoke, count=7, dur=900
                )

        # ── FASE 3: Enfriado — de naranja a carbón, rápido ──────
        steps_cool    = max(2, COOL_DUR // FRAME_MS)
        step_dur_cool = COOL_DUR / steps_cool

        for s in range(steps_cool):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = syl_abs_end + int(s * step_dur_cool)
            frame.end_time   = syl_abs_end + int((s + 1) * step_dur_cool)

            color = color_flame if s / steps_cool < 0.5 else color_char
            frame.text = (
                "{\\an5\\pos(%d,%d)\\1c%s\\3c%s\\blur1\\bord1}"
            ) % (x, y, color, border_char) + syl.text
            io.write_line(frame)

        # ── FASE 4: Desmoronado — cae, gira y se encoge en ceniza ──
        crumble_start = syl_abs_end + COOL_DUR
        rot_dir       = random.choice([-1, 1])
        steps_crumble    = max(4, CRUMBLE_DUR // FRAME_MS)
        step_dur_crumble = CRUMBLE_DUR / steps_crumble

        for s in range(steps_crumble):
            frame            = line.copy()
            frame.layer      = 0
            frame.start_time = crumble_start + int(s * step_dur_crumble)
            frame.end_time   = crumble_start + int((s + 1) * step_dur_crumble)

            t_norm    = s / steps_crumble
            y_fall    = int((t_norm ** 1.3) * CRUMBLE_FALL)
            rot       = rot_dir * int(t_norm * CRUMBLE_ROT)
            scale     = 100 - int(t_norm * 45)
            alpha_str = "&H%02X&" % int(255 * (t_norm ** 0.8))

            frame.text = (
                "{\\an5\\pos(%d,%d)\\frz%d\\1c%s\\3c%s\\alpha%s\\blur1\\bord1\\fscx%d\\fscy%d}"
            ) % (x, y + y_fall, rot, color_char, border_char, alpha_str, scale, scale) + syl.text
            io.write_line(frame)

        generate_ash_flakes(io, line, syl, color_char, crumble_start, dur=ASH_DUR)
