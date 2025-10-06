"""
Этот модуль содержит реализацию TextMerger, который отвечает
за слияние текстовых файлов путем добавления уникальных строк.
"""
from pathlib import Path
from typing import List

from tsync.models.merge import MergePriority
from .base import BaseMerger

class TextMerger(BaseMerger):
    """
    Обработчик для текстовых файлов. Добавляет уникальные строки из
    исходного файла в конец целевого. Идеально для .gitignore, .dockerignore.
    """
    def merge(self, source_path: Path, destination_path: Path, priority: MergePriority) -> None:
        """
        Выполняет слияние двух текстовых файлов, оркеструя вспомогательные методы.

        Поле `priority` здесь не используется, так как эта стратегия
        только добавляет новые строки и никогда не перезаписывает существующие.
        """
        source_content = self._fs.read_file(source_path)
        destination_content = self._fs.read_file(destination_path)

        # 1. Логическая проверка: определяем, какие строки нужно добавить.
        lines_to_add = self._get_lines_to_add(source_content, destination_content)

        # 2. Проверка-прерыватель: если добавлять нечего, выходим.
        if not lines_to_add:
            return

        # 3. Форматирование: собираем итоговое содержимое файла.
        final_content = self._prepare_final_content(destination_content, lines_to_add)

        # 4. Запись: сохраняем результат.
        self._fs.write_file(destination_path, final_content)

    def _get_lines_to_add(self, source_content: str, destination_content: str) -> List[str]:
        """
        Сравнивает два текстовых блока и возвращает список строк, которые
        присутствуют в `source_content`, но отсутствуют в `destination_content`.
        """
        base_lines = destination_content.splitlines()
        incoming_lines = source_content.splitlines()

        # Используем множество для быстрой и эффективной проверки на уникальность
        base_set = set(base_lines)

        unique_lines = []
        for line in incoming_lines:
            if line not in base_set:
                unique_lines.append(line)

        return unique_lines

    def _prepare_final_content(self, base_content: str, lines_to_add: List[str]) -> str:
        """
        Форматирует итоговое содержимое файла, добавляя новые строки
        и обеспечивая корректные переносы строк.
        """
        final_lines = base_content.splitlines()

        # Добавляем пустую строку перед новыми записями для лучшей читаемости,
        # если ее там еще нет и файл не пустой.
        if final_lines and final_lines[-1]:
            final_lines.append("")

        final_lines.extend(lines_to_add)

        # Гарантируем, что в конце файла есть перенос строки для чистоты,
        # что является стандартной практикой для текстовых конфиг. файлов.
        if final_lines and final_lines[-1]:
            final_lines.append("")

        return "\n".join(final_lines)