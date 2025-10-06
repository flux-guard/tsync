"""
Тесты для JsonMerger.
"""
import pytest
import json
from pathlib import Path

from tsync.handlers.mergers.json import JsonMerger
from tsync.models.merge import MergePriority


class TestJsonMerger:
    """Тесты для JsonMerger."""

    def test_merge_json_toolkit_priority(self, temp_dir, fs_service):
        """Тест: слияние JSON с приоритетом toolkit."""
        merger = JsonMerger(fs_service)

        source = temp_dir / "source.json"
        source_data = {
            "name": "toolkit",
            "version": "2.0.0",
            "new_field": "new_value",
        }
        with source.open("w") as f:
            json.dump(source_data, f)

        destination = temp_dir / "destination.json"
        dest_data = {
            "name": "project",
            "version": "1.0.0",
            "local_field": "local_value",
        }
        with destination.open("w") as f:
            json.dump(dest_data, f)

        merger.merge(source, destination, MergePriority.TOOLKIT)

        with destination.open("r") as f:
            result = json.load(f)

        assert result["name"] == "toolkit"
        assert result["version"] == "2.0.0"
        assert result["local_field"] == "local_value"
        assert result["new_field"] == "new_value"

    def test_merge_json_project_priority(self, temp_dir, fs_service):
        """Тест: слияние JSON с приоритетом project."""
        merger = JsonMerger(fs_service)

        source = temp_dir / "source.json"
        source_data = {
            "name": "toolkit",
            "version": "2.0.0",
            "new_field": "new_value",
        }
        with source.open("w") as f:
            json.dump(source_data, f)

        destination = temp_dir / "destination.json"
        dest_data = {
            "name": "project",
            "version": "1.0.0",
            "local_field": "local_value",
        }
        with destination.open("w") as f:
            json.dump(dest_data, f)

        merger.merge(source, destination, MergePriority.PROJECT)

        with destination.open("r") as f:
            result = json.load(f)

        assert result["name"] == "project"
        assert result["version"] == "1.0.0"
        assert result["local_field"] == "local_value"
        assert result["new_field"] == "new_value"

    def test_merge_json_nested_objects(self, temp_dir, fs_service):
        """Тест: слияние вложенных объектов."""
        merger = JsonMerger(fs_service)

        source = temp_dir / "source.json"
        source_data = {
            "config": {
                "api": {
                    "url": "https://new-api.com",
                    "timeout": 30,
                }
            }
        }
        with source.open("w") as f:
            json.dump(source_data, f)

        destination = temp_dir / "destination.json"
        dest_data = {
            "config": {
                "api": {
                    "url": "https://localhost",
                    "key": "secret",
                }
            }
        }
        with destination.open("w") as f:
            json.dump(dest_data, f)

        merger.merge(source, destination, MergePriority.TOOLKIT)

        with destination.open("r") as f:
            result = json.load(f)

        assert result["config"]["api"]["url"] == "https://new-api.com"
        assert result["config"]["api"]["timeout"] == 30
        assert result["config"]["api"]["key"] == "secret"

    def test_merge_json_package_json(self, temp_dir, fs_service):
        """Тест: реальный пример - package.json."""
        merger = JsonMerger(fs_service)

        source = temp_dir / "toolkit_package.json"
        source_data = {
            "scripts": {
                "lint": "eslint .",
                "format": "prettier --write .",
            },
            "devDependencies": {
                "eslint": "^8.0.0",
            }
        }
        with source.open("w") as f:
            json.dump(source_data, f)

        destination = temp_dir / "package.json"
        dest_data = {
            "name": "my-project",
            "version": "1.0.0",
            "scripts": {
                "test": "jest",
            },
            "devDependencies": {
                "jest": "^29.0.0",
            }
        }
        with destination.open("w") as f:
            json.dump(dest_data, f)

        merger.merge(source, destination, MergePriority.TOOLKIT)

        with destination.open("r") as f:
            result = json.load(f)

        # Проектные поля сохранены
        assert result["name"] == "my-project"
        assert result["version"] == "1.0.0"

        # Scripts объединены
        assert result["scripts"]["test"] == "jest"
        assert result["scripts"]["lint"] == "eslint ."
        assert result["scripts"]["format"] == "prettier --write ."

        # DevDependencies объединены
        assert result["devDependencies"]["jest"] == "^29.0.0"
        assert result["devDependencies"]["eslint"] == "^8.0.0"
