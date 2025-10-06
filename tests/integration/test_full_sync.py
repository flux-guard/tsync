"""
Интеграционные тесты полного цикла синхронизации.
"""
import pytest
import yaml
from pathlib import Path

from tsync.services.sync import SyncService


class TestFullSync:
    """Интеграционные тесты полного цикла."""

    def test_full_sync_simple(self, temp_dir, fs_service, git_service, template_service):
        """Тест: полная синхронизация простого проекта."""
        sync_service = SyncService(fs_service, git_service, template_service)

        # Создаем toolkit директорию
        toolkit_dir = temp_dir / "toolkit"
        toolkit_dir.mkdir()

        # Создаем .toolkit.yml
        toolkit_config = {
            "toolkit_version": "1.0.0",
            "aliases": {
                "simple": {
                    "description": "Simple config",
                    "components": [
                        {
                            "id": "files",
                            "description": "Simple files",
                            "files": [
                                {
                                    "source": "templates/test.txt",
                                    "destination": "test.txt",
                                    "policy": "sync-strict",
                                }
                            ],
                        }
                    ],
                }
            },
        }

        toolkit_config_file = toolkit_dir / ".toolkit.yml"
        with toolkit_config_file.open("w") as f:
            yaml.dump(toolkit_config, f)

        # Создаем templates
        templates_dir = toolkit_dir / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.txt").write_text("Test content from toolkit")

        # Создаем проект consumer
        project_dir = temp_dir / "project"
        project_dir.mkdir()

        consumer_config = {
            "provider": {
                "url": "file:///dummy",  # Не используется в тесте
                "version": "v1.0.0",
            },
            "sync": [
                {
                    "alias": "simple",
                }
            ],
        }

        consumer_config_file = project_dir / ".project.toolkit.yml"
        with consumer_config_file.open("w") as f:
            yaml.dump(consumer_config, f)

        # Загружаем конфигурации вручную (обходим git)
        consumer_cfg = sync_service._load_consumer_config(consumer_config_file)
        provider_cfg = sync_service._load_provider_config(toolkit_config_file)

        # Выполняем синхронизацию
        sync_service._process_sync_items(
            consumer_config=consumer_cfg,
            provider_config=provider_cfg,
            project_dir=project_dir,
            toolkit_dir=toolkit_dir,
        )

        # Проверяем результат
        result_file = project_dir / "test.txt"
        assert result_file.exists()
        assert result_file.read_text() == "Test content from toolkit"

    def test_full_sync_with_template(self, temp_dir, fs_service, git_service, template_service):
        """Тест: синхронизация с шаблонизацией."""
        sync_service = SyncService(fs_service, git_service, template_service)

        toolkit_dir = temp_dir / "toolkit"
        toolkit_dir.mkdir()

        toolkit_config = {
            "toolkit_version": "1.0.0",
            "aliases": {
                "templated": {
                    "description": "Templated config",
                    "components": [
                        {
                            "id": "dockerfile",
                            "description": "Dockerfile",
                            "var_schema": {
                                "python_version": {
                                    "description": "Python version",
                                    "required": True,
                                }
                            },
                            "files": [
                                {
                                    "source": "templates/Dockerfile.tpl",
                                    "destination": "Dockerfile",
                                    "policy": "template",
                                }
                            ],
                        }
                    ],
                }
            },
        }

        with (toolkit_dir / ".toolkit.yml").open("w") as f:
            yaml.dump(toolkit_config, f)

        templates_dir = toolkit_dir / "templates"
        templates_dir.mkdir()
        (templates_dir / "Dockerfile.tpl").write_text("FROM python:{{ python_version }}")

        project_dir = temp_dir / "project"
        project_dir.mkdir()

        consumer_config = {
            "provider": {
                "url": "file:///dummy",
                "version": "v1.0.0",
            },
            "vars": {
                "python_version": "3.11",
            },
            "sync": [
                {
                    "alias": "templated",
                }
            ],
        }

        with (project_dir / ".project.toolkit.yml").open("w") as f:
            yaml.dump(consumer_config, f)

        consumer_cfg = sync_service._load_consumer_config(project_dir / ".project.toolkit.yml")
        provider_cfg = sync_service._load_provider_config(toolkit_dir / ".toolkit.yml")

        sync_service._process_sync_items(
            consumer_config=consumer_cfg,
            provider_config=provider_cfg,
            project_dir=project_dir,
            toolkit_dir=toolkit_dir,
        )

        result_file = project_dir / "Dockerfile"
        assert result_file.exists()
        assert result_file.read_text() == "FROM python:3.11"

    def test_full_sync_with_skip(self, temp_dir, fs_service, git_service, template_service):
        """Тест: синхронизация с пропуском компонента."""
        sync_service = SyncService(fs_service, git_service, template_service)

        toolkit_dir = temp_dir / "toolkit"
        toolkit_dir.mkdir()

        toolkit_config = {
            "toolkit_version": "1.0.0",
            "aliases": {
                "multi": {
                    "description": "Multiple components",
                    "components": [
                        {
                            "id": "file1",
                            "description": "File 1",
                            "files": [
                                {
                                    "source": "templates/file1.txt",
                                    "destination": "file1.txt",
                                    "policy": "sync-strict",
                                }
                            ],
                        },
                        {
                            "id": "file2",
                            "description": "File 2",
                            "files": [
                                {
                                    "source": "templates/file2.txt",
                                    "destination": "file2.txt",
                                    "policy": "sync-strict",
                                }
                            ],
                        },
                    ],
                }
            },
        }

        with (toolkit_dir / ".toolkit.yml").open("w") as f:
            yaml.dump(toolkit_config, f)

        templates_dir = toolkit_dir / "templates"
        templates_dir.mkdir()
        (templates_dir / "file1.txt").write_text("File 1")
        (templates_dir / "file2.txt").write_text("File 2")

        project_dir = temp_dir / "project"
        project_dir.mkdir()

        consumer_config = {
            "provider": {
                "url": "file:///dummy",
                "version": "v1.0.0",
            },
            "sync": [
                {
                    "alias": "multi",
                    "overrides": [
                        {
                            "id": "file2",
                            "skip": True,  # Пропускаем file2
                        }
                    ],
                }
            ],
        }

        with (project_dir / ".project.toolkit.yml").open("w") as f:
            yaml.dump(consumer_config, f)

        consumer_cfg = sync_service._load_consumer_config(project_dir / ".project.toolkit.yml")
        provider_cfg = sync_service._load_provider_config(toolkit_dir / ".toolkit.yml")

        sync_service._process_sync_items(
            consumer_config=consumer_cfg,
            provider_config=provider_cfg,
            project_dir=project_dir,
            toolkit_dir=toolkit_dir,
        )

        # file1 должен быть синхронизирован
        assert (project_dir / "file1.txt").exists()
        assert (project_dir / "file1.txt").read_text() == "File 1"

        # file2 должен быть пропущен
        assert not (project_dir / "file2.txt").exists()
