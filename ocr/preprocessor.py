import logging
from typing import Tuple

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    def __init__(self, target_dpi: int = 300):
        self.target_dpi = target_dpi

    def process(self, image: Image.Image) -> Image.Image:
        logger.debug("Начало предобработки изображения")

        image = self._to_grayscale(image)
        image = self._adjust_dpi(image)
        image = self._remove_noise(image)
        image = self._enhance_contrast(image)
        image = self._binarize(image)
        image = self._correct_rotation(image)

        logger.debug("Предобработка завершена")
        return image

    def _to_grayscale(self, image: Image.Image) -> Image.Image:
        if image.mode != "L":
            return image.convert("L")
        return image

    def _adjust_dpi(self, image: Image.Image) -> Image.Image:
        current_dpi = image.info.get("dpi", (72, 72))[0]
        if current_dpi < self.target_dpi:
            scale = self.target_dpi / current_dpi
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.LANCZOS)
            logger.debug(f"Масштабирование: {current_dpi} -> {self.target_dpi} DPI")
        return image

    def _remove_noise(self, image: Image.Image) -> Image.Image:
        image = image.filter(ImageFilter.MedianFilter(size=3))
        return image

    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)

        return image

    def _binarize(self, image: Image.Image) -> Image.Image:
        threshold = self._otsu_threshold(image)
        image = image.point(lambda x: 0 if x < threshold else 255, "1")
        return image

    def _otsu_threshold(self, image: Image.Image) -> int:
        histogram = image.histogram()
        total = sum(histogram)

        sum_total = sum(i * h for i, h in enumerate(histogram))

        sum_bg = 0
        weight_bg = 0
        max_variance = 0
        threshold = 0

        for i in range(256):
            weight_bg += histogram[i]
            if weight_bg == 0:
                continue

            weight_fg = total - weight_bg
            if weight_fg == 0:
                break

            sum_bg += i * histogram[i]

            mean_bg = sum_bg / weight_bg
            mean_fg = (sum_total - sum_bg) / weight_fg

            variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2

            if variance > max_variance:
                max_variance = variance
                threshold = i

        return threshold

    def _correct_rotation(self, image: Image.Image) -> Image.Image:
        try:
            from scipy import ndimage
            import numpy as np

            array = np.array(image)
            edges = np.gradient(array.astype(float))

            angle = np.arctan2(edges[0].mean(), edges[1].mean())
            angle_degrees = np.degrees(angle)

            if abs(angle_degrees) > 0.5 and abs(angle_degrees) < 15:
                image = image.rotate(angle_degrees, expand=True, fillcolor=255)
                logger.debug(f"Коррекция поворота: {angle_degrees:.1f}°")
        except ImportError:
            logger.debug("scipy не установлен, поворот не корректируется")

        return image
