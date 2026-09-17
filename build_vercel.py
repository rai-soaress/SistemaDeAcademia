"""Prepara os arquivos estaticos e o esquema antes do deploy."""
import shutil
from pathlib import Path


def main():
    from app import app, inicializar_banco

    with app.app_context():
        inicializar_banco()
    root = Path(__file__).resolve().parent
    shutil.copytree(root / "static", root / "public" / "static", dirs_exist_ok=True)


if __name__ == "__main__":
    main()
