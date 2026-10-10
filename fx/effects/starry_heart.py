import math
import random
from pyonfx import Utils
from core.constants import FRAME_MS
from core.particles import generate_stars

# ── Paleta pastel (BGR para ASS) ───────────────────────────────
C_APAGADO = "&H00DBB4CD"   # #CDB4DB lavanda — sílabas sin cantar
C_ACTIVO  = "&H00C5B7FF"   # #FFB7C5 rosa — sílaba cantada
C_CORAZON = "&H00AB8FFF"   # #FF8FAB rosa intenso — corazón
C_CELESTE = "&H00FEE0BD"   # #BDE0FE
C_AMARILLO = "&H00A8F1FF"  # #FFF1A8
C_MENTA   = "&H00D8F0C1"   # #C1F0D8
C_BLANCO  = "&H00FFFFFF"
C_BORDE   = "&H008A5C7A"   # #7A5C8A malva — borde para legibilidad

PALETA_ESTRELLA = [C_AMARILLO, C_CELESTE, C_MENTA, C_ACTIVO, C_BLANCO]

# ── Formas (dibujos ASS \p1, caja de 100x100) ──────────────────
HEART_SHAPE = (
    "m 50 30 b 50 10 20 0 10 20 b 0 40 30 60 50 85 "
    "b 70 60 100 40 90 20 b 80 0 50 10 50 30"
)
SPARKLE_SHAPE = (
    "m 50 0 b 55 40 60 45 100 50 b 60 55 55 60 50 100 "
    "b 45 60 40 55 0 50 b 40 45 45 40 50 0"
)

# ── Entrada (cae desde arriba) y salida (se va por debajo) ─────
TRANS_DUR     = 450   # ms máx. de la entrada/salida
MIN_TRANS     = 200   # ms mín. aunque las líneas estén pegadas (se sincronizan como cinta)
DROP_FACTOR   = 1.15  # distancia de caída = alto de la línea × este factor
STAGGER       = 30    # ms de desfase entre sílabas al entrar/salir (cascada)

# ── Corazón ────────────────────────────────────────────────────
HEART_SIZE    = 42    # escala del corazón (% de la caja de 100px)
WAVE_MARGIN   = 12    # px que el corazón sobrepasa el texto por arriba/abajo en la onda
WAVE_MIN      = 0.45  # fracción mín. de la amplitud (sílabas muy juntas)
DROP_DUR      = 300   # ms máx. de la bajada a la primera sílaba / subida tras la última
CROSS_DUR     = 160   # ms del latido del corazón al atravesar una sílaba
MAX_TILT      = 25    # grados máx. que se inclina el corazón siguiendo la curva
BOB_AMP       = 5     # px de flotación mientras espera
BOB_PERIOD    = 1200  # ms de un ciclo de flotación
BEAT_PERIOD   = 900   # ms entre latidos mientras espera

# ── Reacción de la sílaba al paso del corazón ──────────────────
REACT_DUR     = 360   # ms que dura el giro + agrandado
REACT_SCALE   = 115   # % al que crece la sílaba
REACT_ROT     = 12    # grados que gira (el sentido alterna según cruce el corazón)

# ── Estrellas ──────────────────────────────────────────────────
TWINKLE_COUNT = 7     # estrellas titilando alrededor de cada línea
TWINKLE_PERIOD = (700, 1300)  # ms de un ciclo de brillo (aleatorio por estrella)
BURST_COUNT   = 6     # estrellitas que salen cuando el corazón atraviesa una sílaba
BURST_DUR     = 500


def starry_heart(io, line):
    """
    Latido estelar — un corazón atraviesa las sílabas en onda entre estrellas que brillan.
    Paleta pastel. Entrada: la línea cae desde arriba. Salida: se va por debajo.
    Corazón: onda senoidal que cruza cada sílaba por el centro al cantarse, alternando
    de arriba hacia abajo y de abajo hacia arriba; siempre termina arriba.
    Sílaba: al cruzarla gira y crece un poco, pasa de lavanda a rosa y suelta estrellitas.
    """
    syls = list(Utils.all_non_empty(line.syls))
    if not syls:
        return

    n     = len(syls)
    drop  = max(s.height for s in syls) * DROP_FACTOR
    enter = _window_in(line, n)
    exit_ = _window_out(line, n)

    for i, syl in enumerate(syls):
        x = syl.center
        y = syl.middle
        syl_abs_start, syl_abs_end = _syl_times(line, syl)
        motion = _Motion(enter, exit_, i, drop)

        # ── Sílaba: lavanda → toque del corazón → rosa, siguiendo la caída/salida ─
        rot    = -REACT_ROT * _cross_dir(i)
        react  = REACT_DUR
        a, b   = int(react * 0.35), int(react * 0.7)
        flash  = min(150, max(syl_abs_end - syl_abs_start, 60))
        react_steps = [
            (0, flash, "\\1c%s\\blur1" % C_ACTIVO),
            (0, a, "\\fscx%d\\fscy%d\\frz%d" % (REACT_SCALE, REACT_SCALE, rot)),
            (a, b, "\\fscx100\\fscy100\\frz%d" % (-rot // 3)),
            (b, react, "\\frz0"),
        ]

        bounds = sorted({motion.in0, motion.in1, syl_abs_start, motion.out0, motion.out1})
        for s, e in zip(bounds, bounds[1:]):
            if not (motion.in0 <= s and e <= motion.out1) or e <= s:
                continue
            if s < syl_abs_start:
                state = "\\1c%s\\blur1" % C_APAGADO
            else:
                state = _timeline_tags("\\1c%s\\blur3" % C_BLANCO, react_steps, s - syl_abs_start)
            _write(io, line, 1, s, e, (
                "{\\an5%s\\3c%s\\bord2%s%s}"
            ) % (motion.pos_tags(x, y, s, e), C_BORDE, state, motion.alpha_tags(s, e)) + syl.text)

        # Halo rosa detrás de la sílaba mientras se canta (solo con la línea quieta).
        # Gira y crece igual que la sílaba; si no, su hueco transparente queda a la vista.
        halo_start = max(syl_abs_start, motion.in1)
        halo_end   = min(syl_abs_end + 300, motion.out0)
        halo_react = _timeline_tags("", react_steps[1:], halo_start - syl_abs_start)
        _write(io, line, 0, halo_start, halo_end, (
            "{\\an5\\pos(%d,%d)\\1a&HFF&\\3c%s\\bord6\\blur8\\fad(60,%d)%s}"
        ) % (x, y, C_ACTIVO, min(300, halo_end - halo_start), halo_react) + syl.text)

        # Estrellitas desde el punto donde el corazón atraviesa la sílaba
        generate_stars(
            io, line, x, y + motion.dy(syl_abs_start), syl_abs_start,
            count=BURST_COUNT, dur=BURST_DUR,
            paleta=PALETA_ESTRELLA,
            size_range=(20, 36), dist_range=(25, 65), blur=1,
            border_color=C_BORDE,
        )

    _generate_heart(io, line, syls, _Motion(enter, exit_, 0, drop, stagger=False))
    _generate_twinkles(io, line, enter, exit_)


# ── Helpers ────────────────────────────────────────────────────

def _syl_times(line, syl):
    """
    Inicio y fin absolutos de la sílaba, recortados al end de la línea
    (si en Aegisub se movió el start sin ajustar los \\k, pueden pasarse).
    """
    start = min(line.start_time + syl.start_time, line.end_time)
    end   = min(start + syl.duration, line.end_time)
    return start, end


def _window(gap):
    """
    Duración de una transición y cuánto se mete dentro de la línea.
    Si el hueco con la vecina es menor que la duración, la salida de una y la
    entrada de la otra comparten la misma ventana centrada en el hueco: como una
    cae y la otra baja a la misma velocidad, siempre quedan separadas.
    """
    dur     = int(max(MIN_TRANS, min(TRANS_DUR, gap)))
    overlap = int(max(0, dur - gap) / 2)
    return dur, overlap


def _window_in(line, n):
    dur, overlap = _window(line.leadin)
    start = line.start_time - dur + overlap
    return {"start": start, "end": start + dur, "stagger": min(STAGGER, int(dur * 0.3) // max(n, 1))}


def _window_out(line, n):
    dur, overlap = _window(line.leadout)
    start = line.end_time - overlap
    return {"start": start, "end": start + dur, "stagger": min(STAGGER, int(dur * 0.3) // max(n, 1))}


class _Motion:
    """Desplazamiento vertical y transparencia de una sílaba (o del corazón) en el tiempo."""

    def __init__(self, enter, exit_, i, drop, stagger=True):
        k          = i if stagger else 0
        self.in0   = enter["start"] + k * enter["stagger"]
        self.in1   = enter["end"]
        self.out0  = exit_["start"] + k * exit_["stagger"]
        self.out1  = exit_["end"]
        self.drop  = drop

    def _progress(self, t):
        """(-1..0) durante la entrada, 0 quieta, (0..1) durante la salida."""
        if t < self.in1:
            return -1 + max(0.0, (t - self.in0) / max(self.in1 - self.in0, 1))
        if t > self.out0:
            return min(1.0, (t - self.out0) / max(self.out1 - self.out0, 1))
        return 0.0

    def dy(self, t):
        return self.drop * self._progress(t)

    def alpha(self, t):
        return int(255 * abs(self._progress(t)))

    def pos_tags(self, x, y, s, e):
        y0, y1 = y + self.dy(s), y + self.dy(e)
        if int(y0) == int(y1):
            return "\\pos(%d,%d)" % (x, y0)
        return "\\move(%d,%d,%d,%d)" % (x, y0, x, y1)

    def alpha_tags(self, s, e):
        a0, a1 = self.alpha(s), self.alpha(e)
        if a0 == a1 == 0:
            return ""
        return "\\alpha&H%02X&\\t(0,%d,\\alpha&H%02X&)" % (a0, e - s, a1)


def _timeline_tags(initial, steps, offset):
    """
    Etiquetas para continuar una secuencia de \\t que empezó hace `offset` ms:
    los pasos ya terminados se aplican directo y los demás se desplazan.
    """
    tags = initial
    for t1, t2, tag in steps:
        if t2 <= offset:
            tags += tag
        else:
            tags += "\\t(%d,%d,%s)" % (t1 - offset, t2 - offset, tag)
    return tags


def _write(io, line, layer, start, end, text):
    """Escribe una copia de la línea si el intervalo no está vacío."""
    if end <= start:
        return
    frame            = line.copy()
    frame.layer      = layer
    frame.start_time = start
    frame.end_time   = end
    frame.text       = text
    io.write_line(frame)


def _frames(start, end):
    """Divide [start, end) en cuadros de ~FRAME_MS. Devuelve (t0, t1, u) con u en [0, 1)."""
    dur = end - start
    if dur <= 0:
        return []
    steps = max(1, dur // FRAME_MS)
    return [
        (start + int(s * dur / steps), start + int((s + 1) * dur / steps), s / steps)
        for s in range(steps)
    ]


def _beat_factor(t):
    """Factor de escala de un latido lub-dub que se repite cada BEAT_PERIOD ms."""
    t %= BEAT_PERIOD
    if t < 170:
        return 1 + 0.22 * math.sin(math.pi * t / 170)
    if t < 380:
        return 1 + 0.12 * math.sin(math.pi * (t - 170) / 210)
    return 1.0


def _cross_dir(i):
    """Sentido en que el corazón cruza la sílaba i: +1 bajando, -1 subiendo."""
    return 1 if i % 2 == 0 else -1


def _generate_heart(io, line, syls, motion):
    """
    Corazón que recorre la línea en una onda senoidal y atraviesa cada sílaba
    por el centro justo cuando se canta: baja a través de una, da la vuelta por
    debajo, sube a través de la siguiente, da la vuelta por arriba, y así.
    Entra y sale junto con la línea (motion).
    """
    line_end = line.end_time
    half_h   = HEART_SIZE * 0.85 / 2
    mid_y    = sum(s.middle for s in syls) / len(syls)
    # Amplitud suficiente para que el corazón salga entero por arriba/abajo del texto
    amp      = max(s.height for s in syls) / 2 + half_h + WAVE_MARGIN

    xs     = [s.center for s in syls]
    starts = [_syl_times(line, s)[0] for s in syls]
    gaps   = [b - a for a, b in zip(xs, xs[1:])]
    half_step = (sum(gaps) / len(gaps) / 2) if gaps else 40

    def put(t0, t1, x, y, scale=1.0, rot=0.0):
        size = int(HEART_SIZE * scale)
        _write(io, line, 5, t0, t1, (
            "{\\an5\\pos(%d,%d)\\p1\\bord1\\shad0\\blur1\\1c%s\\3c%s"
            "\\fscx%d\\fscy%d\\frz%d\\alpha&H%02X&}"
        ) % (x, y + motion.dy(t0), C_CORAZON, C_BLANCO, size, size, rot,
             motion.alpha(t0)) + HEART_SHAPE)

    def hover(t0, t1, x, y_base):
        """Espera flotando y latiendo."""
        waves = max(1, round((t1 - t0) / (BOB_PERIOD / 2)))
        for f0, f1, u in _frames(t0, t1):
            y = y_base - BOB_AMP * math.sin(math.pi * waves * u)
            put(f0, f1, x, y, _beat_factor(f0 - t0))

    def arc(t0, t1, x0, x1, y_of, cross=True):
        """
        Tramo de x0 a x1 con altura y_of(u).
        Con cross=True el tramo arranca atravesando una sílaba y el corazón late.
        """
        prev = None
        for f0, f1, u in _frames(t0, t1):
            x = x0 + (x1 - x0) * u
            y = y_of(u)
            # Inclinación según la pendiente de la curva
            if prev:
                dx, dy = x - prev[0], y - prev[1]
                tilt = -math.degrees(math.atan2(dy, max(dx, 0.1))) * 0.5
                tilt = max(-MAX_TILT, min(MAX_TILT, tilt))
            else:
                tilt = 0
            prev  = (x, y)
            since = f0 - t0
            pulse = 1 + 0.3 * math.sin(math.pi * since / CROSS_DUR) if cross and since < CROSS_DUR else 1.0
            put(f0, f1, x, y, pulse, tilt)

    # ── Antes de la primera sílaba: espera arriba y baja a atravesarla ─
    drop_dur   = int(min(DROP_DUR, max(starts[0] - motion.in0, 0) * 0.6))
    drop_start = starts[0] - drop_dur
    wait_x     = xs[0] - half_step
    hover(motion.in0, drop_start, wait_x, mid_y - amp)
    arc(drop_start, starts[0], wait_x, xs[0],
        lambda u: mid_y - amp * math.cos(math.pi / 2 * u), cross=False)

    # ── Entre sílabas: media onda por debajo o por arriba ─────
    for i in range(len(syls) - 1):
        a = amp * max(WAVE_MIN, min(1.0, abs(xs[i + 1] - xs[i]) / (2 * amp)))
        d = _cross_dir(i)
        arc(starts[i], starts[i + 1], xs[i], xs[i + 1],
            lambda u, a=a, d=d: mid_y + d * a * math.sin(math.pi * u))

    # ── Después de la última: siempre termina arriba ──────────
    last_x, last_t = xs[-1], starts[-1]
    crossing       = True
    if _cross_dir(len(syls) - 1) == 1:
        # Cruzó la última bajando: media onda por debajo hasta una sílaba
        # imaginaria, que atraviesa subiendo, para quedar arriba.
        avg_dt = (starts[-1] - starts[0]) / (len(syls) - 1) if len(syls) > 1 else DROP_DUR
        v_dur  = int(min(max(avg_dt, 150), max(line_end - last_t, 0) * 0.6))
        v_x    = last_x + 2 * half_step
        arc(last_t, last_t + v_dur, last_x, v_x,
            lambda u: mid_y + amp * math.sin(math.pi * u))
        last_x, last_t, crossing = v_x, last_t + v_dur, False

    rest_x   = last_x + half_step
    rise_end = last_t + min(DROP_DUR, max(line_end - last_t, 0))
    arc(last_t, rise_end, last_x, rest_x,
        lambda u: mid_y - amp * math.sin(math.pi / 2 * u), cross=crossing)

    # Espera arriba y se va por debajo junto con la línea
    hover(rise_end, motion.out1, rest_x, mid_y - amp)


def _generate_twinkles(io, line, enter, exit_):
    """Estrellas fijas alrededor de la línea que titilan durante toda su vida."""
    start = enter["start"]
    end   = exit_["end"]
    dur   = end - start
    fade  = enter["end"] - enter["start"], exit_["end"] - exit_["start"]

    for _ in range(TWINKLE_COUNT):
        x = random.randint(int(line.left) - 40, int(line.right) + 40)
        # Arriba o abajo del texto, nunca encima de las letras
        if random.random() < 0.5:
            y = random.randint(int(line.top) - 70, int(line.top) - 15)
        else:
            y = random.randint(int(line.bottom) + 10, int(line.bottom) + 45)

        size   = random.randint(12, 24)
        period = random.randint(*TWINKLE_PERIOD)
        color  = random.choice(PALETA_ESTRELLA)
        offset = random.randint(0, period)

        tags = []
        for t in range(-offset, dur, period):
            half = period // 2
            tags.append("\\t(%d,%d,\\alpha&H10&\\fscx%d\\fscy%d)" % (
                max(t, 0), max(t + half, 0), int(size * 1.4), int(size * 1.4)))
            tags.append("\\t(%d,%d,\\alpha&HB0&\\fscx%d\\fscy%d)" % (
                max(t + half, 0), max(t + period, 0), size, size))

        _write(io, line, 3, start, end, (
            "{\\an5\\pos(%d,%d)\\p1\\bord0\\shad0\\blur1\\1c%s"
            "\\alpha&HB0&\\fscx%d\\fscy%d\\frz%d\\fad(%d,%d)%s}"
        ) % (x, y, color, size, size, random.randint(0, 45), *fade, "".join(tags))
            + SPARKLE_SHAPE)
