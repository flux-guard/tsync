"""
Этот модуль содержит реализацию JsonMerger, который отвечает
за "умное" слияние JSON-файлов.
"""
import json
from pathlib import Path

from tsync.models.merge import MergePriority
from .base import BaseMerger


class JsonMerger(BaseMerger):
    """
    Обработчик, реализующий рекурсивное "глубокое" слияние для JSON-файлов.
    """

    def merge(self, source_path: Path, destination_path: Path, priority: MergePriority) -> None:
        """
        Выполняет слияние двух JSON-файлов.

        1. Читает и парсит исходный и целевой файлы.
        2. Рекурсивно объединяет их содержимое с помощью _deep_merge_dicts из BaseMerger.
        3. Записывает результат обратно в целевой файл с красивым форматированием.
        """
        source_content = self._fs.read_file(source_path)
        destination_content = self._fs.read_file(destination_path)

        source_data = json.loads(source_content)
        destination_data = json.loads(destination_content)

        merged_data = self._deep_merge_dicts(
            destination_data,
            source_data,
            priority
        )

        final_content = json.dumps(merged_data, indent=2, ensure_ascii=False)
        self._fs.write_file(destination_path, final_content)