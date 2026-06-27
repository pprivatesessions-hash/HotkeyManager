import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class OCRCache:
    def __init__(self, cache_dir: str = "cache", max_age_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)

    def _get_key(self, pdf_path: str, page_num: int) -> str:
        content = f"{pdf_path}:{page_num}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, pdf_path: str, page_num: int) -> str | None:
        key = self._get_key(pdf_path, page_num)
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, encoding="utf-8") as f:
                data = json.load(f)

            cached_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - cached_time > self.max_age:
                cache_path.unlink()
                logger.debug(f"Кэш просрочен: стр.{page_num}")
                return None

            logger.debug(f"Кэш попадание: стр.{page_num}")
            return data["text"]
        except Exception as e:
            logger.warning(f"Ошибка чтения кэша: {e}")
            return None

    def set(self, pdf_path: str, page_num: int, text: str) -> None:
        key = self._get_key(pdf_path, page_num)
        cache_path = self._get_cache_path(key)

        data = {
            "pdf_path": pdf_path,
            "page": page_num,
            "text": text,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Сохранено в кэш: стр.{page_num}")
        except Exception as e:
            logger.warning(f"Ошибка записи кэша: {e}")

    def clear(self) -> int:
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        logger.info(f"Очищено {count} файлов кэша")
        return count
