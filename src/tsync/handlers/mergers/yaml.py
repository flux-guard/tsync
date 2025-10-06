"""
Этот модуль содержит реализацию YamlMerger, который отвечает
за "умное" слияние YAML-файлов.
"""
import yaml
from pathlib import Path

from tsync.models.merge import MergePriority
from .base import BaseMerger


class YamlMerger(BaseMerger):
    """
    Обработчик, реализующий рекурсивное "глубокое" слияние для YAML-файлов.
    """

    def merge(self, source_path: Path, destination_path: Path, priority: MergePriority) -> None:
        """
        Выполняет слияние двух YAML-файлов.

        1. Читает исходный (из toolkit) и целевой (из проекта) файлы.
        2. Рекурсивно объединяет их содержимое с помощью _deep_merge_dicts из BaseMerger.
        3. Записывает результат обратно в целевой файл.
        """
        source_data = self._fs.read_yaml(source_path)
        destination_data = self._fs.read_yaml(destination_path)

        merged_data = self._deep_merge_dicts(
            destination_data,
            source_data,
            priority
        )

        final_content = yaml.dump(merged_data, indent=2, sort_keys=False, allow_unicode=True)
        self._fs.write_file(destination_path, final_content)