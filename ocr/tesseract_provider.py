import logging
from pathlib import Path

import pytesseract
from PIL import Image

from .base import OCRProvider
from .preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)

TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Tesseract-OCR\tesseract.exe",
]


def _find_tesseract() -> str | None:
    for path in TESSERACT_PATHS:
        if Path(path).exists():
            return path
    return None


class TesseractProvider(OCRProvider):
    def __init__(
        self,
        languages: list[str] = None,
        dpi: int = 300,
        preprocess: bool = True,
    ):
        self.languages = languages or ["rus", "eng"]
        self.dpi = dpi
        self.preprocess = preprocess
        self.preprocessor = ImagePreprocessor(target_dpi=dpi)

        tesseract_path = _find_tesseract()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"Tesseract найден: {tesseract_path}")
        else:
            logger.warning("Tesseract не найден, попытка использовать PATH")

        logger.info(f"Tesseract инициализирован: языки={self.languages}, DPI={self.dpi}")

    def recognize(self, image: Image.Image) -> str:
        if self.preprocess:
            image = self.preprocessor.process(image)

        lang = "+".join(self.languages)

        try:
            text = pytesseract.image_to_string(image, lang=lang)
            logger.debug(f"Распознано {len(text)} символов")
            return text
        except Exception as e:
            logger.error(f"Ошибка OCR: {e}")
            return ""

    def recognize_file(self, file_path: str) -> str:
        image = Image.open(file_path)
        return self.recognize(image)

    def get_supported_languages(self) -> list[str]:
        try:
            return pytesseract.get_languages()
        except Exception:
            return self.languages
