from src.gui.app import main
from src.ocr.tesseract_setup import configurar_tesseract

if __name__ == "__main__":
    configurar_tesseract()
    main()
