"""
Тесты для TextMerger.
"""
import pytest
from pathlib import Path

from tsync.handlers.mergers.text import TextMerger
from tsync.models.merge import MergePriority


class TestTextMerger:
    """Тесты для TextMerger."""

    def test_merge_text_adds_unique_lines(self, temp_dir, fs_service):
        """Тест: добавление уникальных строк."""
        merger = TextMerger(fs_service)

        source = temp_dir / "source.txt"
        source.write_text("line1\nline2\nline3\n")

        destination = temp_dir / "destination.txt"
        destination.write_text("line1\nline4\n")

        merger.merge(source, destination, MergePriority.TOOLKIT)

        result = destination.read_text()
        lines = result.strip().split("\n")

        # Проверяем, что добавлены только уникальные строки
        assert "line1" in lines
        assert "line4" in lines
        assert "line2" in lines
        assert "line3" in lines

    def test_merge_text_no_duplicates(self, temp_dir, fs_service):
        """Тест: не добавляет дубликаты."""
        merger = TextMerger(fs_service)

        source = temp_dir / "source.txt"
        source.write_text("line1\nline2\n")

        destination = temp_dir / "destination.txt"
        destination.write_text("line1\nline2\n")

        # Получаем исходное содержимое
        original_content = destination.read_text()

        merger.merge(source, destination, MergePriority.TOOLKIT)

        # Содержимое не должно измениться
        result = destination.read_text()
        assert result == original_content

    def test_merge_text_gitignore_example(self, temp_dir, fs_service):
        """Тест: реальный пример - .gitignore."""
        merger = TextMerger(fs_service)

        # Toolkit .gitignore
        source = temp_dir / "toolkit.gitignore"
        source.write_text("""__pycache__/
*.pyc
.pytest_cache/
.coverage
""")

        # Проектный .gitignore
        destination = temp_dir / ".gitignore"
        destination.write_text(""".env
__pycache__/
my_local_file.txt
""")

        merger.merge(source, destination, MergePriority.TOOLKIT)

        result = destination.read_text()
        lines = [line for line in result.split("\n") if line.strip()]

        # Оригинальные строки сохранены
        assert ".env" in lines
        assert "my_local_file.txt" in lines

        # Уникальные строки из toolkit добавлены
        assert "*.pyc" in lines
        assert ".pytest_cache/" in lines
        assert ".coverage" in lines

        # Дубликат не добавлен
        assert lines.count("__pycache__/") == 1

    def test_merge_text_empty_source(self, temp_dir, fs_service):
        """Тест: пустой исходный файл."""
        merger = TextMerger(fs_service)

        source = temp_dir / "source.txt"
        source.write_text("")

        destination = temp_dir / "destination.txt"
        original = "line1\nline2\n"
        destination.write_text(original)

        merger.merge(source, destination, MergePriority.TOOLKIT)

        # Destination не изменился
        assert destination.read_text() == original

    def test_merge_text_empty_destination(self, temp_dir, fs_service):
        """Тест: пустой целевой файл."""
        merger = TextMerger(fs_service)

        source = temp_dir / "source.txt"
        source_content = "line1\nline2\nline3\n"
        source.write_text(source_content)

        destination = temp_dir / "destination.txt"
        destination.write_text("")

        merger.merge(source, destination, MergePriority.TOOLKIT)

        result = destination.read_text()
        lines = [line for line in result.split("\n") if line.strip()]

        assert "line1" in lines
        assert "line2" in lines
        assert "line3" in lines

    def test_merge_text_priority_irrelevant(self, temp_dir, fs_service):
        """Тест: приоритет не влияет на text merger (только добавление)."""
        merger = TextMerger(fs_service)

        source = temp_dir / "source.txt"
        source.write_text("new_line\n")

        destination = temp_dir / "destination.txt"
        destination.write_text("existing_line\n")

        # Проверяем с обоими приоритетами
        merger.merge(source, destination, MergePriority.TOOLKIT)
        result_toolkit = destination.read_text()

        destination.write_text("existing_line\n")
        merger.merge(source, destination, MergePriority.PROJECT)
        result_project = destination.read_text()

        # Результат одинаковый независимо от приоритета
        assert result_toolkit == result_project
        assert "existing_line" in result_toolkit
        assert "new_line" in result_toolkit
