"""
Тесты для SyncStrictStrategy.
"""
import pytest
from pathlib import Path

from tsync.handlers.sync_strict import SyncStrictStrategy
from tsync.models.context import Context
from tsync.models.provider import File
from tsync.models.policy import Policy


class TestSyncStrictStrategy:
    """Тесты для SyncStrictStrategy."""

    def test_sync_strict_creates_new_file(self, temp_dir, fs_service):
        """Тест: создание нового файла."""
        strategy = SyncStrictStrategy(fs_service)

        # Создаем исходный файл
        source = temp_dir / "source.txt"
        source.write_text("Source content")

        # Целевой файл не существует
        destination = temp_dir / "destination.txt"

        file_config = File(
            source="source.txt",
            destination="destination.txt",
            policy=Policy.SYNC_STRICT,
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
        assert destination.read_text() == "Source content"

    def test_sync_strict_overwrites_existing_file(self, temp_dir, fs_service):
        """Тест: перезапись существующего файла."""
        strategy = SyncStrictStrategy(fs_service)

        # Создаем исходный файл
        source = temp_dir / "source.txt"
        source.write_text("New content from toolkit")

        # Создаем существующий целевой файл
        destination = temp_dir / "destination.txt"
        destination.write_text("Old local content")

        file_config = File(
            source="source.txt",
            destination="destination.txt",
            policy=Policy.SYNC_STRICT,
        )

        context = Context(
            source_path=source,
            destination_path=destination,
            file_config=file_config,
            variables={},
            destination_exists=True,
        )

        strategy.apply(context)

        # Файл должен быть перезаписан
        assert destination.exists()
        assert destination.read_text() == "New content from toolkit"

    def test_sync_strict_creates_nested_directories(self, temp_dir, fs_service):
        """Тест: создание вложенных директорий."""
        strategy = SyncStrictStrategy(fs_service)

        source = temp_dir / "source.txt"
        source.write_text("Content")

        destination = temp_dir / "nested" / "deep" / "destination.txt"

        file_config = File(
            source="source.txt",
            destination="nested/deep/destination.txt",
            policy=Policy.SYNC_STRICT,
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
        assert destination.read_text() == "Content"

    def test_sync_strict_binary_file(self, temp_dir, fs_service):
        """Тест: копирование бинарного файла."""
        strategy = SyncStrictStrategy(fs_service)

        source = temp_dir / "image.bin"
        binary_content = b"\x00\x01\x02\x03\xFF"
        source.write_bytes(binary_content)

        destination = temp_dir / "image_copy.bin"

        file_config = File(
            source="image.bin",
            destination="image_copy.bin",
            policy=Policy.SYNC_STRICT,
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
        assert destination.read_bytes() == binary_content
