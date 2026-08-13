import os
import sys
from pathlib import Path

import pytesseract

_configurado = False


def configurar_tesseract() -> None:
    global _configurado
    if _configurado:
        return
    _configurado = True

    if getattr(sys, "frozen", False):
        # No onedir, o PyInstaller agrupa binaries/datas em _internal/ (contents_directory),
        # nao ao lado do .exe — sys._MEIPASS aponta para essa pasta em onedir e onefile.
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[2] / "vendor"

    pasta = base / "tesseract"
    executavel = pasta / "tesseract.exe"
    if executavel.exists():
        pytesseract.pytesseract.tesseract_cmd = str(executavel)
        os.environ["TESSDATA_PREFIX"] = str(pasta / "tessdata")
