from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from PIL import Image


class OCRProvider(ABC):
    @abstractmethod
    def recognize(self, image: Image.Image) -> str:
        pass

    @abstractmethod
    def recognize_file(self, file_path: str) -> str:
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        pass
