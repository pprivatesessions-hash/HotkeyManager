import logging

import pytesseract
from PIL import Image

from .base import OCRProvider
from .preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)


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
