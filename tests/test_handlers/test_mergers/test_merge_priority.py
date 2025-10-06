"""
Тесты для проверки корректной работы MergePriority в merger'ах.
"""
import pytest
from pathlib import Path
import tempfile
import yaml
import json

from tsync.services.fs import FileSystemService
from tsync.handlers.mergers.yaml import YamlMerger
from tsync.handlers.mergers.json import JsonMerger
from tsync.models.merge import MergePriority


@pytest.fixture
def fs_service():
    """Создает экземпляр FileSystemService."""
    return FileSystemService()


@pytest.fixture
def temp_dir():
    """Создает временную директорию."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestYamlMergerPriority:
    """Тесты для YamlMerger с различными приоритетами."""

    def test_yaml_merge_toolkit_priority(self, fs_service, temp_dir):
        """При TOOLKIT priority значения из toolkit перезаписывают project."""
        source_file = temp_dir / "source.yml"
        dest_file = temp_dir / "dest.yml"

        # Toolkit содержит обновленную версию
        source_data = {
            "shared_key": "toolkit_value",
            "toolkit_only": "new_feature"
        }

        # Project имеет старое значение
        dest_data = {
            "shared_key": "project_value",
            "project_only": "keep_this"
        }

        source_file.write_text(yaml.dump(source_data), encoding="utf-8")
        dest_file.write_text(yaml.dump(dest_data), encoding="utf-8")

        merger = YamlMerger(fs_service)
        merger.merge(source_file, dest_file, MergePriority.TOOLKIT)

        result = yaml.safe_load(dest_file.read_text(encoding="utf-8"))

        # shared_key должен быть перезаписан значением из toolkit
        assert result["shared_key"] == "toolkit_value"
        # toolkit_only должен быть добавлен
        assert result["toolkit_only"] == "new_feature"
        # project_only должен остаться
        assert result["project_only"] == "keep_this"

    def test_yaml_merge_project_priority(self, fs_service, temp_dir):
        """При PROJECT priority значения project сохраняются."""
        source_file = temp_dir / "source.yml"
        dest_file = temp_dir / "dest.yml"

        source_data = {
            "shared_key": "toolkit_value",
            "toolkit_only": "new_feature"
        }

        dest_data = {
            "shared_key": "project_value",
            "project_only": "keep_this"
        }

        source_file.write_text(yaml.dump(source_data), encoding="utf-8")
        dest_file.write_text(yaml.dump(dest_data), encoding="utf-8")

        merger = YamlMerger(fs_service)
        merger.merge(source_file, dest_file, MergePriority.PROJECT)

        result = yaml.safe_load(dest_file.read_text(encoding="utf-8"))

        # shared_key должен сохранить значение из project
        assert result["shared_key"] == "project_value"
        # toolkit_only всё равно должен быть добавлен (новый ключ)
        assert result["toolkit_only"] == "new_feature"
        # project_only должен остаться
        assert result["project_only"] == "keep_this"

    def test_yaml_deep_merge_nested_dicts(self, fs_service, temp_dir):
        """Проверяет глубокое слияние вложенных словарей."""
        source_file = temp_dir / "source.yml"
        dest_file = temp_dir / "dest.yml"

        source_data = {
            "database": {
                "host": "new-host",
                "port": 5432,
                "ssl": True
            }
        }

        dest_data = {
            "database": {
                "host": "old-host",
                "username": "admin"
            }
        }

        source_file.write_text(yaml.dump(source_data), encoding="utf-8")
        dest_file.write_text(yaml.dump(dest_data), encoding="utf-8")

        merger = YamlMerger(fs_service)
        merger.merge(source_file, dest_file, MergePriority.TOOLKIT)

        result = yaml.safe_load(dest_file.read_text(encoding="utf-8"))

        # Глубокое слияние должно объединить все ключи
        assert result["database"]["host"] == "new-host"  # Перезаписан
        assert result["database"]["port"] == 5432  # Добавлен
        assert result["database"]["ssl"] is True  # Добавлен
        assert result["database"]["username"] == "admin"  # Сохранен


class TestJsonMergerPriority:
    """Тесты для JsonMerger с различными приоритетами."""

    def test_json_merge_toolkit_priority(self, fs_service, temp_dir):
        """При TOOLKIT priority значения из toolkit перезаписывают project."""
        source_file = temp_dir / "source.json"
        dest_file = temp_dir / "dest.json"

        source_data = {
            "version": "2.0",
            "features": ["new_feature"]
        }

        dest_data = {
            "version": "1.0",
            "author": "me"
        }

        source_file.write_text(json.dumps(source_data), encoding="utf-8")
        dest_file.write_text(json.dumps(dest_data), encoding="utf-8")

        merger = JsonMerger(fs_service)
        merger.merge(source_file, dest_file, MergePriority.TOOLKIT)

        result = json.loads(dest_file.read_text(encoding="utf-8"))

        assert result["version"] == "2.0"  # Обновлено
        assert result["features"] == ["new_feature"]  # Добавлено
        assert result["author"] == "me"  # Сохранено

    def test_json_merge_project_priority(self, fs_service, temp_dir):
        """При PROJECT priority локальные изменения сохраняются."""
        source_file = temp_dir / "source.json"
        dest_file = temp_dir / "dest.json"

        source_data = {
            "scripts": {
                "test": "jest",
                "build": "webpack"
            }
        }

        dest_data = {
            "scripts": {
                "test": "vitest",  # Локальная кастомизация
                "dev": "vite"
            }
        }

        source_file.write_text(json.dumps(source_data), encoding="utf-8")
        dest_file.write_text(json.dumps(dest_data), encoding="utf-8")

        merger = JsonMerger(fs_service)
        merger.merge(source_file, dest_file, MergePriority.PROJECT)

        result = json.loads(dest_file.read_text(encoding="utf-8"))

        # Локальное изменение должно сохраниться
        assert result["scripts"]["test"] == "vitest"
        # Новые ключи добавляются
        assert result["scripts"]["build"] == "webpack"
        # Существующие ключи сохраняются
        assert result["scripts"]["dev"] == "vite"


class TestMergerEdgeCases:
    """Тесты граничных случаев для merger'ов."""

    def test_merge_with_null_values(self, fs_service, temp_dir):
        """Проверяет обработку null значений."""
        source_file = temp_dir / "source.yml"
        dest_file = temp_dir / "dest.yml"

        source_data = {"key": None}
        dest_data = {"key": "value"}

        source_file.write_text(yaml.dump(source_data), encoding="utf-8")
        dest_file.write_text(yaml.dump(dest_data), encoding="utf-8")

        merger = YamlMerger(fs_service)
        merger.merge(source_file, dest_file, MergePriority.TOOLKIT)

        result = yaml.safe_load(dest_file.read_text(encoding="utf-8"))
        # null из toolkit должен перезаписать значение
        assert result["key"] is None

    def test_merge_empty_source(self, fs_service, temp_dir):
        """Проверяет слияние с пустым source."""
        source_file = temp_dir / "source.yml"
        dest_file = temp_dir / "dest.yml"

        source_data = {}
        dest_data = {"keep": "this"}

        source_file.write_text(yaml.dump(source_data), encoding="utf-8")
        dest_file.write_text(yaml.dump(dest_data), encoding="utf-8")

        merger = YamlMerger(fs_service)
        merger.merge(source_file, dest_file, MergePriority.TOOLKIT)

        result = yaml.safe_load(dest_file.read_text(encoding="utf-8"))
        # Destination должен остаться неизменным
        assert result == {"keep": "this"}
