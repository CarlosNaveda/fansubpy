# fansubpy 🎵

Script de Python para generar subtítulos karaoke con timing sílaba por sílaba a partir de un archivo de audio o video, listo para importar en **Aegisub**.

> ⚠️ Este script fue desarrollado por [Claude](https://claude.ai) (Anthropic) en colaboración con Carlos Naveda (ToNextAxis). Es una primera versión funcional que se irá mejorando con el tiempo.

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

---

## Preparación

Antes de correr el script necesitas dos archivos:

- **Audio o video** de la canción (`.mp3`, `.mp4`, `.wav`, etc.)
- **Lyric en `.txt`** con una frase por línea, sin numeración ni timestamps. Ejemplo:

```
Últimamente voy a la deriva
Me estoy pasando un poco de impulsiva
Mandando el jueves al carajo, ventanas abajo, reggaetón Arriba
```

---

## Configuración

Edita las variables al inicio de `main.py`:

```python
AUDIO_PATH  = r"C:\ruta\a\tu\cancion.mp3"
LYRIC_PATH  = r"C:\ruta\a\tu\lyric.txt"
OUTPUT_ASS  = "output_karaoke.ass"
MODEL_SIZE  = "medium"   # tiny | base | small | medium | large
LANGUAGE    = "es"       # "en" para inglés, o elimina el parámetro para detección automática
```

### Modelos disponibles

| Modelo | Velocidad | Precisión | Tamaño |
|--------|-----------|-----------|--------|
| tiny   | Muy rápido | Baja      | ~75MB  |
| base   | Rápido     | Media     | ~145MB |
| small  | Normal     | Buena     | ~465MB |
| medium | Lento      | Muy buena | ~1.5GB |
| large  | Muy lento  | Excelente | ~3GB   |

> Para canciones en español se recomienda `medium` o `large`.

---

## Uso

```bash
python main.py
```

La primera vez que uses un modelo, Whisper lo descargará automáticamente. El script genera dos archivos:

- `output.srt` — subtítulos normales
- `output_karaoke.ass` — subtítulos con timing por sílaba para Aegisub

---

## Importar en Aegisub

1. Abre Aegisub
2. Abre el video: **Video → Abrir video**
3. Abre el `.ass`: **Archivo → Abrir subtítulos**
4. Ajusta los timings que necesites manualmente
5. Para aplicar efectos karaoke con el **Karaoke Templater**, agrega una línea `template syl` con tus tags de efecto
6. Exporta: **Archivo → Exportar subtítulos** → marca **Plantilla karaoke** → Exportar

---

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

## Roadmap

- [ ] Argumentos por línea de comandos (`python main.py audio.mp3 lyric.txt`)
- [ ] Mejor algoritmo de timing por sílaba (considerando sílaba tónica)
- [ ] Soporte para múltiples formatos de salida
- [ ] Interfaz CLI interactiva

---

## Créditos

Script desarrollado por [Claude](https://claude.ai) (Anthropic) · Proyecto mantenido por [Carlos Naveda / ToNextAxis](https://youtube.com/@ToNextAxis)