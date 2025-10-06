"""
Тесты для YamlMerger.
"""
import pytest
import yaml
from pathlib import Path

from tsync.handlers.mergers.yaml import YamlMerger
from tsync.models.merge import MergePriority


class TestYamlMerger:
    """Тесты для YamlMerger."""

    def test_merge_yaml_toolkit_priority(self, temp_dir, fs_service):
        """Тест: слияние YAML с приоритетом toolkit."""
        merger = YamlMerger(fs_service)

        # Исходный файл из toolkit
        source = temp_dir / "source.yaml"
        source_data = {
            "name": "toolkit",
            "version": "2.0.0",
            "new_field": "new_value",
        }
        with source.open("w") as f:
            yaml.dump(source_data, f)

        # Существующий файл в проекте
        destination = temp_dir / "destination.yaml"
        dest_data = {
            "name": "project",
            "version": "1.0.0",
            "local_field": "local_value",
        }
        with destination.open("w") as f:
            yaml.dump(dest_data, f)

        merger.merge(source, destination, MergePriority.TOOLKIT)

        # Читаем результат
        with destination.open("r") as f:
            result = yaml.safe_load(f)

        # Toolkit перезаписывает конфликтующие поля
        assert result["name"] == "toolkit"
        assert result["version"] == "2.0.0"
        # Локальное поле сохранено
        assert result["local_field"] == "local_value"
        # Новое поле добавлено
        assert result["new_field"] == "new_value"

    def test_merge_yaml_project_priority(self, temp_dir, fs_service):
        """Тест: слияние YAML с приоритетом project."""
        merger = YamlMerger(fs_service)

        source = temp_dir / "source.yaml"
        source_data = {
            "name": "toolkit",
            "version": "2.0.0",
            "new_field": "new_value",
        }
        with source.open("w") as f:
            yaml.dump(source_data, f)

        destination = temp_dir / "destination.yaml"
        dest_data = {
            "name": "project",
            "version": "1.0.0",
            "local_field": "local_value",
        }
        with destination.open("w") as f:
            yaml.dump(dest_data, f)

        merger.merge(source, destination, MergePriority.PROJECT)

        with destination.open("r") as f:
            result = yaml.safe_load(f)

        # Project сохраняет свои значения
        assert result["name"] == "project"
        assert result["version"] == "1.0.0"
        # Локальное поле сохранено
        assert result["local_field"] == "local_value"
        # Новое поле добавлено
        assert result["new_field"] == "new_value"

    def test_merge_yaml_nested_dicts(self, temp_dir, fs_service):
        """Тест: слияние вложенных словарей."""
        merger = YamlMerger(fs_service)

        source = temp_dir / "source.yaml"
        source_data = {
            "database": {
                "host": "new-host",
                "port": 5432,
                "new_option": "value",
            }
        }
        with source.open("w") as f:
            yaml.dump(source_data, f)

        destination = temp_dir / "destination.yaml"
        dest_data = {
            "database": {
                "host": "localhost",
                "user": "admin",
            }
        }
        with destination.open("w") as f:
            yaml.dump(dest_data, f)

        merger.merge(source, destination, MergePriority.TOOLKIT)

        with destination.open("r") as f:
            result = yaml.safe_load(f)

        # Вложенные поля объединены
        assert result["database"]["host"] == "new-host"  # перезаписано
        assert result["database"]["port"] == 5432  # добавлено
        assert result["database"]["user"] == "admin"  # сохранено
        assert result["database"]["new_option"] == "value"  # добавлено

    def test_merge_yaml_with_lists(self, temp_dir, fs_service):
        """Тест: слияние с списками (списки заменяются, не сливаются)."""
        merger = YamlMerger(fs_service)

        source = temp_dir / "source.yaml"
        source_data = {
            "dependencies": ["pkg1", "pkg2", "pkg3"],
        }
        with source.open("w") as f:
            yaml.dump(source_data, f)

        destination = temp_dir / "destination.yaml"
        dest_data = {
            "dependencies": ["pkg1", "old-pkg"],
        }
        with destination.open("w") as f:
            yaml.dump(dest_data, f)

        merger.merge(source, destination, MergePriority.TOOLKIT)

        with destination.open("r") as f:
            result = yaml.safe_load(f)

        # Список полностью заменяется при приоритете toolkit
        assert result["dependencies"] == ["pkg1", "pkg2", "pkg3"]
