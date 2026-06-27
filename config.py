import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import yaml

from .models.category import DEFAULT_CATEGORIES, Category

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent / "config.yaml"


@dataclass
class StrategyConfig:
    use_semantic: bool = True
    use_category_weight: bool = True
    use_frequency: bool = False
    prefer_key_proximity: bool = True


@dataclass
class OCRConfig:
    engine: str = "tesseract"
    languages: List[str] = field(default_factory=lambda: ["rus", "eng"])
    dpi: int = 300
    preprocess: bool = True


@dataclass
class CacheConfig:
    enabled: bool = True
    directory: str = "cache"
    max_age_hours: int = 24


@dataclass
class HotkeyConfig:
    prefix_combos: List[str] = field(default_factory=lambda: ["Ctrl+Alt", "Ctrl+Shift+Alt"])
    exclude_keys: List[str] = field(default_factory=list)
    category_weights: Dict[str, float] = field(default_factory=dict)
    semantic_hints: Dict[str, str] = field(default_factory=dict)
    command_keywords: Dict[str, str] = field(default_factory=dict)
    keyboard_layout: Dict[str, str] = field(default_factory=dict)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)


def load_config(config_path: Optional[str] = None) -> HotkeyConfig:
    path = Path(config_path) if config_path else CONFIG_FILE

    if not path.exists():
        logger.warning(f"Конфиг не найден: {path}, используются значения по умолчанию")
        return _default_config()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения конфига: {e}")
        return _default_config()

    return _parse_config(data)


def _parse_config(data: dict) -> HotkeyConfig:
    hm = data.get("hotkey_manager", {})

    strategy_data = hm.get("strategy", {})
    strategy = StrategyConfig(
        use_semantic=strategy_data.get("use_semantic", True),
        use_category_weight=strategy_data.get("use_category_weight", True),
        use_frequency=strategy_data.get("use_frequency", False),
        prefer_key_proximity=strategy_data.get("prefer_key_proximity", True),
    )

    ocr_data = data.get("ocr", {})
    ocr = OCRConfig(
        engine=ocr_data.get("engine", "tesseract"),
        languages=ocr_data.get("languages", ["rus", "eng"]),
        dpi=ocr_data.get("dpi", 300),
        preprocess=ocr_data.get("preprocess", True),
    )

    cache_data = data.get("cache", {})
    cache = CacheConfig(
        enabled=cache_data.get("enabled", True),
        directory=cache_data.get("directory", "cache"),
        max_age_hours=cache_data.get("max_age_hours", 24),
    )

    semantic_hints = data.get("semantic_hints", {})
    command_keywords = data.get("command_keywords", {})
    keyboard_layout = data.get("keyboard_layout", {})

    config = HotkeyConfig(
        prefix_combos=hm.get("prefix_combos", ["Ctrl+Alt", "Ctrl+Shift+Alt"]),
        exclude_keys=hm.get("exclude_keys", []),
        category_weights=hm.get("category_weights", {}),
        semantic_hints=semantic_hints,
        command_keywords=command_keywords,
        keyboard_layout=keyboard_layout,
        strategy=strategy,
        ocr=ocr,
        cache=cache,
    )

    logger.info(
        f"Конфиг загружен: {len(config.prefix_combos)} префиксов, "
        f"{len(config.semantic_hints)} семантических подсказок, "
        f"{len(config.command_keywords)} ключевых слов"
    )

    return config


def _default_config() -> HotkeyConfig:
    return HotkeyConfig(
        category_weights={name: cat.weight for name, cat in DEFAULT_CATEGORIES.items()},
    )


DEFAULT_CONFIG = load_config()
