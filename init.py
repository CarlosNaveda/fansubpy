import sys
import shutil
from pathlib import Path

def init_proyecto(nombre: str):
    base      = Path(__file__).parent / "fansubs"
    plantilla = base / "plantilla"
    destino   = base / nombre

    if destino.exists():
        print(f"❌ Ya existe el proyecto '{nombre}' en fansubs/")
        sys.exit(1)

    if not plantilla.exists():
        print(f"❌ No se encontró la carpeta plantilla en {plantilla}")
        sys.exit(1)

    shutil.copytree(plantilla, destino)
    print(f"✅ Proyecto creado: fansubs/{nombre}/")
    print(f"   Agrega tu audio en:  fansubs/{nombre}/audio/")
    print(f"   Agrega tu lyric en:  fansubs/{nombre}/lyrics/  (opcional)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python init.py <nombre-del-proyecto>")
        sys.exit(1)
    init_proyecto(sys.argv[1])