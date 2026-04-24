"""
Regenera las secciones dinámicas del README.md:
  - <!-- AUTO:estructura --> ... <!-- /AUTO:estructura -->
  - <!-- AUTO:efectos -->   ... <!-- /AUTO:efectos -->

Uso:
    python generate_readme.py

Ejecutar desde la raíz del proyecto. También se puede invocar
desde GitHub Actions después de cada push.
"""

import ast
import re
import sys
from pathlib import Path

ROOT    = Path(__file__).parent
README  = ROOT / "README.md"
FX_DIR  = ROOT / "fx"
FANSUBS = ROOT / "fansubs"


# ── Helpers ───────────────────────────────────────────────────────

def replace_section(content: str, tag: str, new_block: str) -> str:
    """Reemplaza el contenido entre <!-- AUTO:tag --> y <!-- /AUTO:tag -->."""
    pattern = rf"(<!-- AUTO:{tag} -->).*?(<!-- /AUTO:{tag} -->)"
    replacement = rf"\1\n{new_block}\n\2"
    result, n = re.subn(pattern, replacement, content, flags=re.DOTALL)
    if n == 0:
        print(f"⚠️  Marcador AUTO:{tag} no encontrado en el README.")
    return result


def get_docstring(filepath: Path) -> str:
    """Extrae la primera línea del docstring de un archivo .py."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
                doc = ast.get_docstring(node)
                if doc:
                    return doc.splitlines()[0].strip()
    except Exception:
        pass
    return "—"


def get_function_name(filepath: Path) -> str:
    """Devuelve el nombre de la primera función pública definida en el archivo."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                return node.name
    except Exception:
        pass
    return filepath.stem


# ── Sección: estructura de archivos ──────────────────────────────

def build_tree(path: Path, prefix: str = "", root: Path = None) -> list[str]:
    """
    Genera un árbol de directorios estilo unicode para el README.
    Ignora: __pycache__, .git, archivos generados (*_fx.ass),
            audio (*.mp3, *.mp4, *.wav), modelos (*.pt).
    """
    if root is None:
        root = path

    IGNORE_DIRS  = {"__pycache__", ".git", "venv", ".env", "node_modules"}
    IGNORE_EXTS  = {".pyc", ".pyo", ".mp3", ".mp4", ".wav", ".mkv", ".pt"}
    IGNORE_NAMES = lambda n: n.endswith("_fx.ass")

    entries = sorted(
        [e for e in path.iterdir()
         if e.name not in IGNORE_DIRS
         and e.suffix not in IGNORE_EXTS
         and not IGNORE_NAMES(e.name)
         and not e.name.startswith(".")],
        key=lambda e: (e.is_file(), e.name.lower())
    )

    lines = []
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        extension = "    " if i == len(entries) - 1 else "│   "

        # Anotaciones inline para archivos conocidos
        comment = _inline_comment(entry, root)
        suffix  = f"  # {comment}" if comment else ""

        lines.append(f"{prefix}{connector}{entry.name}{suffix}")

        if entry.is_dir():
            lines.extend(build_tree(entry, prefix + extension, root))

    return lines


def _inline_comment(entry: Path, root: Path) -> str:
    """Comentario inline para archivos/carpetas conocidos."""
    rel = entry.relative_to(root)
    comments = {
        "constants.py":      "constantes globales de animación",
        "particles.py":      "helpers de partículas compartidos",
        "run.py":            "punto de entrada — genera el _fx.ass",
        "main.py":           "genera output_karaoke.ass con Whisper",
        "generate_readme.py":"regenera las secciones dinámicas del README",
        ".gitignore":        "",
        "README.md":         "",
        "audio":             ".mp3 del video (ignorado en git)",
        "lyrics":            ".txt con la letra línea por línea",
        "styles":            "styles.ass con los estilos de Aegisub",
        "timings":           "output_karaoke.ass (timeos crudos)",
    }
    # Efectos: leer primera línea del docstring
    if entry.suffix == ".py" and entry.parent.name == "effects" and entry.stem != "__init__":
        return get_docstring(entry)

    return comments.get(entry.name, "")


def build_estructura() -> str:
    lines = []
    for top in sorted(ROOT.iterdir()):
        if top.name.startswith(".") or top.name in {"__pycache__", "venv"}:
            continue
        if top.suffix in {".py", ".md", ".zip"}:
            comment = _inline_comment(top, ROOT)
            suffix  = f"  # {comment}" if comment else ""
            lines.append(f"{top.name}{suffix}")
        elif top.is_dir():
            lines.append(f"{top.name}/")
            lines.extend(build_tree(top, prefix="    "))

    return "```\n" + "\n".join(lines) + "\n```"


# ── Sección: tabla de efectos ─────────────────────────────────────

def build_efectos() -> str:
    effects_dir = FX_DIR / "effects"
    if not effects_dir.exists():
        return "_No se encontró fx/effects/_"

    rows = []
    for f in sorted(effects_dir.glob("*.py")):
        if f.stem == "__init__":
            continue
        fn_name = get_function_name(f)
        doc     = get_docstring(f)
        rows.append(f"| `{f.name}` | `{fn_name}` | {doc} |")

    if not rows:
        return "_No hay efectos definidos todavía._"

    header = "| Archivo | Función | Descripción |\n|---|---|---|"
    return header + "\n" + "\n".join(rows)


# ── Main ──────────────────────────────────────────────────────────

def main():
    if not README.exists():
        print(f"❌ No se encontró {README}")
        sys.exit(1)

    content = README.read_text(encoding="utf-8")

    content = replace_section(content, "estructura", build_estructura())
    content = replace_section(content, "efectos",    build_efectos())

    README.write_text(content, encoding="utf-8")
    print("✅ README.md actualizado.")


if __name__ == "__main__":
    main()
