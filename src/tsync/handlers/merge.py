"""
Этот модуль содержит стратегию-диспетчер MergeStrategy, которая выбирает
и делегирует операцию слияния специализированным обработчикам.
"""
import logging
from typing import Dict

from tsync.models.context import Context
from tsync.models.merge import MergeType, MergePriority
from tsync.services.fs import FileSystemService
from .base import BaseStrategy
from .mergers.base import BaseMerger
from .mergers.yaml import YamlMerger
from .mergers.text import TextMerger
from .mergers.json import JsonMerger



class MergeStrategy(BaseStrategy):
    """
    Стратегия-диспетчер для "умного" слияния ('merge').

    Оптимизация: Merger'ы создаются один раз при инициализации и переиспользуются.
    """

    def __init__(self, fs_service: FileSystemService):
        super().__init__(fs_service)
        self._logger = logging.getLogger(__name__)

        # Создаем экземпляры merger'ов один раз для переиспользования
        self._mergers: Dict[MergeType, BaseMerger] = {
            MergeType.YAML: YamlMerger(fs_service),
            MergeType.JSON: JsonMerger(fs_service),
            MergeType.TEXT: TextMerger(fs_service),
        }
        """
        Что делает: Карта с готовыми экземплярами обработчиков слияния.
        Создаются один раз при инициализации для лучшей производительности.
        """

        self._extension_to_type: Dict[str, MergeType] = {
            ".yaml": MergeType.YAML,
            ".yml": MergeType.YAML,
            ".json": MergeType.JSON,
            ".gitignore": MergeType.TEXT,
            ".dockerignore": MergeType.TEXT,
        }
        """
        Что делает: Карта, сопоставляющая расширение файла с конкретным
        типом обработчика слияния.
        """

    def apply(self, context: Context) -> None:
        destination_path = context.destination_path

        if not context.destination_exists:
            self._logger.info(f"Применяю MERGE: Целевой файл не существует, копирую '{context.source_path}'")
            self._fs.copy_file(context.source_path, destination_path)
            return

        # Определяем тип merger'а
        if context.file_config.merge_as:
            merge_type = context.file_config.merge_as
        else:
            suffix = destination_path.suffix.lower()
            merge_type = self._extension_to_type.get(suffix, MergeType.TEXT)

        if not merge_type:
            self._logger.debug(
                f"Не могу определить тип слияния по расширению для '{destination_path}', использую текстовый merger"
            )
            merge_type = MergeType.TEXT

        self._logger.info(f"Применяю MERGE ({merge_type.value}): {context.source_path} в {destination_path}")

        # Используем приоритет по умолчанию, если не указан
        priority = context.file_config.merge_priority or MergePriority.TOOLKIT
        merger = self._mergers[merge_type]
        merger.merge(context.source_path, destination_path, priority)