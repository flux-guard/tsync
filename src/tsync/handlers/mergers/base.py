"""
Базовый класс для всех обработчиков слияния.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from tsync.models.merge import MergePriority
from tsync.services.fs import FileSystemService


class BaseMerger(ABC):
    """
    Абстрактный базовый класс для всех специализированных обработчиков слияния.
    """

    def __init__(self, fs_service: FileSystemService):
        self._fs = fs_service
        """
        Что делает: Экземпляр сервиса для работы с файловой системой.
        """

    @abstractmethod
    def merge(self, source_path: Path, destination_path: Path, priority: MergePriority) -> None:
        """Основной метод, выполняющий слияние с учетом приоритета."""
        pass

    def _deep_merge_dicts(
        self, base: Dict[str, Any], incoming: Dict[str, Any], priority: MergePriority
    ) -> Dict[str, Any]:
        """
        Рекурсивно сливает два словаря с учетом приоритета.

        - Если ключ существует только в одном из словарей, он добавляется в результат.
        - Если ключ существует в обоих и оба значения - словари, рекурсивно вызываем слияние.
        - Если ключ существует в обоих, но значения не словари:
          * При priority=TOOLKIT: значение из incoming (toolkit) перезаписывает base (project)
          * При priority=PROJECT: значение из base (project) сохраняется

        :param base: Базовый словарь (обычно из project)
        :param incoming: Входящий словарь (обычно из toolkit)
        :param priority: Приоритет при конфликтах
        :return: Объединенный словарь
        """
        for key, value in incoming.items():
            # Если оба значения - словари, рекурсивно сливаем
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                base[key] = self._deep_merge_dicts(base[key], value, priority)
            # Если ключа нет в base, просто добавляем
            elif key not in base:
                base[key] = value
            # Если ключ есть в обоих, применяем приоритет
            elif priority == MergePriority.TOOLKIT:
                base[key] = value
            # При priority=PROJECT оставляем значение из base без изменений

        return base
