"""
Тесты для модели Context.
"""
from pathlib import Path
import pytest

from tsync.models.context import Context
from tsync.models.provider import File
from tsync.models.policy import Policy


class TestContext:
    """Тесты для Context."""

    def test_valid_context(self):
        """Тест: валидный контекст."""
        file_config = File(
            source="templates/test.txt",
            destination="test.txt",
            policy=Policy.SYNC_STRICT,
        )

        context = Context(
            source_path=Path("/toolkit/templates/test.txt"),
            destination_path=Path("/project/test.txt"),
            file_config=file_config,
            variables={"var1": "value1"},
            destination_exists=False,
        )

        assert context.source_path == Path("/toolkit/templates/test.txt")
        assert context.destination_path == Path("/project/test.txt")
        assert context.file_config.policy == Policy.SYNC_STRICT
        assert context.variables == {"var1": "value1"}
        assert context.destination_exists is False

    def test_context_with_existing_destination(self):
        """Тест: контекст с существующим файлом назначения."""
        file_config = File(
            source="templates/existing.txt",
            destination="existing.txt",
            policy=Policy.INIT,
        )

        context = Context(
            source_path=Path("/toolkit/templates/existing.txt"),
            destination_path=Path("/project/existing.txt"),
            file_config=file_config,
            variables={},
            destination_exists=True,
        )

        assert context.destination_exists is True

    def test_context_with_merge_policy(self):
        """Тест: контекст для файла с merge политикой."""
        from tsync.models.merge import MergePriority

        file_config = File(
            source="templates/config.yaml",
            destination="config.yaml",
            policy=Policy.MERGE,
            merge_priority=MergePriority.PROJECT,
        )

        context = Context(
            source_path=Path("/toolkit/templates/config.yaml"),
            destination_path=Path("/project/config.yaml"),
            file_config=file_config,
            variables={},
            destination_exists=True,
        )

        assert context.file_config.merge_priority == MergePriority.PROJECT
