# fansubs-project

Proyecto de karaoke animado con pyonfx. Separa timeos, efectos y canciones en carpetas independientes.

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

## Añadir una canción nueva

```
fansubs/
└── nueva-cancion/    
    ├── lyrics/  → pega el .txt con la letra aquí
    ├── styles/  → exporta los estilos desde Aegisub
    └── timings/ → se genera automáticamente
```
