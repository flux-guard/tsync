"""
Общие fixtures для всех тестов tsync.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict

from tsync.services.fs import FileSystemService
from tsync.services.git import GitService
from tsync.services.template import TemplateService
from tsync.services.sync import SyncService


@pytest.fixture
def temp_dir():
    """Создает временную директорию для тестов."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def fs_service():
    """Возвращает экземпляр FileSystemService."""
    return FileSystemService()


@pytest.fixture
def template_service():
    """Возвращает экземпляр TemplateService."""
    return TemplateService()


@pytest.fixture
def git_service(temp_dir):
    """Возвращает экземпляр GitService с временным кэшем."""
    cache_dir = temp_dir / "git_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return GitService(cache_dir)


@pytest.fixture
def sync_service(fs_service, git_service, template_service):
    """Возвращает экземпляр SyncService."""
    return SyncService(fs_service, git_service, template_service)


@pytest.fixture
def sample_provider_config() -> Dict[str, Any]:
    """Возвращает пример конфигурации provider."""
    return {
        "toolkit_version": "1.0.0",
        "aliases": {
            "test-alias": {
                "description": "Test alias",
                "components": [
                    {
                        "id": "test-component",
                        "description": "Test component",
                        "var_schema": {
                            "test_var": {
                                "description": "Test variable",
                                "required": True,
                            }
                        },
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


@pytest.fixture
def sample_consumer_config() -> Dict[str, Any]:
    """Возвращает пример конфигурации consumer."""
    return {
        "provider": {
            "url": "git@github.com:test/toolkit.git",
            "version": "v1.0.0",
        },
        "vars": {
            "test_var": "test_value",
        },
        "sync": [
            {
                "alias": "test-alias",
            }
        ],
    }


@pytest.fixture
def provider_toolkit_dir(temp_dir, sample_provider_config, fs_service):
    """Создает временную директорию toolkit с конфигурацией."""
    toolkit_dir = temp_dir / "provider_toolkit"
    toolkit_dir.mkdir(parents=True, exist_ok=True)

    # Создаем .toolkit.yml
    import yaml
    config_path = toolkit_dir / ".toolkit.yml"
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(sample_provider_config, f, allow_unicode=True)

    # Создаем templates директорию
    templates_dir = toolkit_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Создаем тестовый файл
    test_file = templates_dir / "test.txt"
    test_file.write_text("Test content from toolkit", encoding="utf-8")

    return toolkit_dir


@pytest.fixture
def consumer_project_dir(temp_dir, sample_consumer_config):
    """Создает временную директорию проекта consumer."""
    project_dir = temp_dir / "consumer_project"
    project_dir.mkdir(parents=True, exist_ok=True)

    # Создаем .project.toolkit.yml
    import yaml
    config_path = project_dir / ".project.toolkit.yml"
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(sample_consumer_config, f, allow_unicode=True)

    return project_dir


@pytest.fixture
def sample_yaml_content() -> str:
    """Возвращает пример YAML содержимого."""
    return """
name: test
version: 1.0.0
dependencies:
  - package1
  - package2
"""


@pytest.fixture
def sample_json_content() -> str:
    """Возвращает пример JSON содержимого."""
    return """{
  "name": "test",
  "version": "1.0.0",
  "dependencies": ["package1", "package2"]
}"""


@pytest.fixture
def sample_template_content() -> str:
    """Возвращает пример шаблона Jinja2."""
    return """
FROM python:{{ python_version }}
WORKDIR {{ workdir }}
CMD ["python", "{{ entrypoint }}"]
"""


@pytest.fixture
def sample_template_vars() -> Dict[str, str]:
    """Возвращает переменные для шаблона."""
    return {
        "python_version": "3.11",
        "workdir": "/app",
        "entrypoint": "main.py",
    }
