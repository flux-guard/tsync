"""
Тесты для InitStrategy.
"""
import pytest
from pathlib import Path

from tsync.handlers.init import InitStrategy
from tsync.models.context import Context
from tsync.models.provider import File
from tsync.models.policy import Policy


class TestInitStrategy:
    """Тесты для InitStrategy."""

    def test_init_creates_file_if_not_exists(self, temp_dir, fs_service):
        """Тест: создание файла, если его нет."""
        strategy = InitStrategy(fs_service)

        source = temp_dir / "source.txt"
        source.write_text("Initial content")

        destination = temp_dir / "destination.txt"

        file_config = File(
            source="source.txt",
            destination="destination.txt",
            policy=Policy.INIT,
        )

        context = Context(
            source_path=source,
            destination_path=destination,
            file_config=file_config,
            variables={},
            destination_exists=False,
        )

        strategy.apply(context)

        assert destination.exists()
        assert destination.read_text() == "Initial content"

    def test_init_skips_if_exists(self, temp_dir, fs_service):
        """Тест: пропуск, если файл уже существует."""
        strategy = InitStrategy(fs_service)

        source = temp_dir / "source.txt"
        source.write_text("New content")

        # Создаем существующий файл с другим содержимым
        destination = temp_dir / "destination.txt"
        destination.write_text("Existing content")

        file_config = File(
            source="source.txt",
            destination="destination.txt",
            policy=Policy.INIT,
        )

        context = Context(
            source_path=source,
            destination_path=destination,
            file_config=file_config,
            variables={},
            destination_exists=True,
        )

        strategy.apply(context)

        # Файл не должен быть изменен
        assert destination.exists()
        assert destination.read_text() == "Existing content"

    def test_init_creates_nested_directories(self, temp_dir, fs_service):
        """Тест: создание вложенных директорий."""
        strategy = InitStrategy(fs_service)

        source = temp_dir / "source.txt"
        source.write_text("Content")

        destination = temp_dir / "a" / "b" / "c" / "destination.txt"

        file_config = File(
            source="source.txt",
            destination="a/b/c/destination.txt",
            policy=Policy.INIT,
        )

        context = Context(
            source_path=source,
            destination_path=destination,
            file_config=file_config,
            variables={},
            destination_exists=False,
        )

        strategy.apply(context)

        assert destination.exists()
        assert destination.parent.exists()
