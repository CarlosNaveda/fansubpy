# Fansubpy 🎵

Script de Python para generar subtítulos karaoke con timing sílaba por sílaba a partir de un archivo de audio o video, listo para importar en **Aegisub**.

> ⚠️ Este script fue desarrollado por [Claude](https://claude.ai) (Anthropic) en colaboración con Carlos Naveda. Es una primera versión funcional que se irá mejorando con el tiempo.

---

## ¿Qué hace?

1. Usa **Whisper** (OpenAI) para transcribir el audio y obtener timestamps por palabra
2. Usa el **lyric** como referencia para respetar los cortes de línea exactos
3. Alinea inteligentemente el lyric con los timestamps de Whisper usando `difflib`
4. Silabea cada palabra con **pyphen**
5. Exporta un archivo `.ass` con tags `\k` por sílaba, listo para Aegisub

---

## Requisitos previos

### 1. Python
Descarga e instala Python 3.12 desde [python.org](https://www.python.org/downloads/).

> ⚠️ Evita Python 3.14 por ahora — PyTorch aún no tiene soporte CUDA para esa versión.

### 2. FFmpeg
FFmpeg es necesario para que Whisper pueda leer archivos de audio/video.

**Instalación en Windows:**
1. Descarga el zip desde [ffmpeg.org/download.html](https://ffmpeg.org/download.html) → Windows → `ffmpeg-release-essentials.zip`
2. Extrae en `C:\ffmpeg`
3. Agrega `C:\ffmpeg\bin` al PATH del sistema:
   - Busca "Variables de entorno" en el inicio de Windows
   - Variables del sistema → `Path` → Editar → Nuevo → pega `C:\ffmpeg\bin`
4. Cierra y vuelve a abrir la terminal
5. Verifica con:
```bash
ffmpeg -version
```

---

## Instalación

### 1. Crea y activa un entorno virtual
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 2. Instala las dependencias
```bash
pip install openai-whisper pyphen pysrt
```


## Estructura

<!-- AUTO:estructura -->
```
README.md
fx/
    ├── core
    │   ├── __init__.py
    │   ├── constants.py  # constantes globales de animación
    │   └── particles.py  # helpers de partículas compartidos
    ├── effects
    │   ├── __init__.py
    │   ├── glitch_electric.py  # Aberración cromática eléctrica — 3 capas superpuestas (R/B offset + base).
    │   ├── rap_hit.py  # Golpes secos sin onda sinusoidal — feel de rap.
    │   └── wave.py  # Ola suave con sacudida vertical en sílaba activa.
    └── run.py  # punto de entrada — genera el _fx.ass
generate_readme.py  # regenera las secciones dinámicas del README
timings/
    └── main.py  # genera output_karaoke.ass con Whisper
```
<!-- /AUTO:estructura -->

## Añadir una canción nueva

```
fansubs/
└── nueva-cancion/    
    ├── lyrics/  → pega el .txt con la letra aquí
    ├── styles/  → exporta los estilos desde Aegisub
    └── timings/ → se genera automáticamente
```

## Flujo de trabajo

### 1. Generar timeos
```bash
python timings/main.py linkin-park-in-the-end
```
Necesita: `fansubs/<cancion>/audio/*.mp3` y `fansubs/<cancion>/lyrics/*.txt`  
Genera:   `fansubs/<cancion>/timings/output_karaoke.ass`

Abre el `.ass` en Aegisub para ajustar timeos manualmente si es necesario.

### 2. Aplicar efectos
```bash
python fx/run.py linkin-park-in-the-end
```
Lee:    `fansubs/<cancion>/timings/output_karaoke.ass`  
Genera: `fansubs/<cancion>/timings/output_karaoke_fx.ass` (ignorado en git)

## Efectos disponibles

<!-- AUTO:efectos -->
| Archivo | Función | Descripción |
|---|---|---|
| `glitch_electric.py` | `glitch_electric` | Aberración cromática eléctrica — 3 capas superpuestas (R/B offset + base). |
| `rap_hit.py` | `rap_hit` | Golpes secos sin onda sinusoidal — feel de rap. |
| `wave.py` | `wave` | Ola suave con sacudida vertical en sílaba activa. |
<!-- /AUTO:efectos -->

## Asignar efectos a estilos

Edita el `EFFECT_MAP` en `fx/run.py`:

```python
EFFECT_MAP = {
    ("NombreEstilo", "karaoke"): wave,
    ("OtroEstilo",   "karaoke"): rap_hit,
}
```

El primer valor es el nombre del estilo en Aegisub. El segundo es el campo `Efecto` de la línea.

## Pegar subtítulos al video con FFmpeg

Una vez exportado el `.ass` final desde Aegisub:

```bash
ffmpeg -i "tu_video.mp4" -vf "ass=output_karaoke.ass" "video_final.mp4"
```

> El font usado en el `.ass` debe estar instalado en tu sistema para que ffmpeg lo renderice correctamente.

---

## Notas

- El timing sílaba x sílaba es una **aproximación** — distribuye el tiempo de cada palabra proporcionalmente entre sus sílabas. Siempre habrá ajustes manuales en Aegisub.
- Funciona con cualquier idioma soportado por Whisper, no solo español.
- El script acepta cualquier formato de audio/video que soporte FFmpeg.

---

## Créditos

Script desarrollado por [Claude](https://claude.ai) (Anthropic) · Proyecto mantenido por [Carlos Naveda / ToNextAxis](https://youtube.com/@ToNextAxis)