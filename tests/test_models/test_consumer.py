"""
Тесты для моделей consumer.
"""
import pytest
from pydantic import ValidationError

from tsync.models.consumer import (
    FileOverride,
    ComponentOverride,
    SyncItem,
    ProviderConfig,
    ProjectToolkitConfig,
)


class TestFileOverride:
    """Тесты для FileOverride."""

    def test_valid_file_override(self):
        """Тест: валидное переопределение файла."""
        override = FileOverride(
            source="templates/Dockerfile.tpl",
            destination="docker/Dockerfile",
            vars={"python_version": "3.12"},
        )
        assert override.source == "templates/Dockerfile.tpl"
        assert override.destination == "docker/Dockerfile"
        assert override.skip is False

    def test_file_override_skip(self):
        """Тест: пропуск файла."""
        override = FileOverride(
            source="templates/unnecessary.txt",
            skip=True,
        )
        assert override.skip is True

    def test_invalid_skip_with_destination(self):
        """Тест: ошибка при skip=True и destination."""
        with pytest.raises(ValidationError) as exc_info:
            FileOverride(
                source="templates/test.txt",
                skip=True,
                destination="test.txt",
            )
        assert "пропускаемый" in str(exc_info.value)

    def test_invalid_skip_with_vars(self):
        """Тест: ошибка при skip=True и vars."""
        with pytest.raises(ValidationError) as exc_info:
            FileOverride(
                source="templates/test.txt",
                skip=True,
                vars={"var": "value"},
            )
        assert "пропускаемый" in str(exc_info.value)


class TestComponentOverride:
    """Тесты для ComponentOverride."""

    def test_valid_component_override(self):
        """Тест: валидное переопределение компонента."""
        override = ComponentOverride(
            id="dockerfile",
            destination_root="docker/",
            vars={"python_version": "3.12"},
        )
        assert override.id == "dockerfile"
        assert override.destination_root == "docker/"
        assert override.skip is False

    def test_component_override_with_tags(self):
        """Тест: переопределение с фильтрацией по тегам."""
        override = ComponentOverride(
            id="configs",
            include_tags=["production"],
            exclude_tags=["development"],
        )
        assert override.include_tags == ["production"]
        assert override.exclude_tags == ["development"]

    def test_invalid_overlapping_tags(self):
        """Тест: ошибка при пересечении include и exclude тегов."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentOverride(
                id="configs",
                include_tags=["docker", "production"],
                exclude_tags=["docker", "development"],
            )
        assert "не могут одновременно" in str(exc_info.value)
        assert "docker" in str(exc_info.value)

    def test_component_override_skip(self):
        """Тест: пропуск всего компонента."""
        override = ComponentOverride(
            id="unnecessary-component",
            skip=True,
        )
        assert override.skip is True

    def test_component_override_with_file_overrides(self):
        """Тест: переопределение с file-level overrides."""
        override = ComponentOverride(
            id="dockerfile",
            files=[
                FileOverride(
                    source="templates/Dockerfile.tpl",
                    destination="Dockerfile.prod",
                    vars={"env": "production"},
                )
            ],
        )
        assert len(override.files) == 1
        assert override.files[0].destination == "Dockerfile.prod"


class TestSyncItem:
    """Тесты для SyncItem."""

    def test_valid_sync_item(self):
        """Тест: валидный элемент синхронизации."""
        item = SyncItem(
            alias="python-service",
        )
        assert item.alias == "python-service"
        assert item.overrides is None

    def test_sync_item_with_overrides(self):
        """Тест: элемент синхронизации с переопределениями."""
        item = SyncItem(
            alias="python-service",
            overrides=[
                ComponentOverride(
                    id="dockerfile",
                    destination_root="docker/",
                ),
                ComponentOverride(
                    id="linters",
                    skip=True,
                ),
            ],
        )
        assert len(item.overrides) == 2
        assert item.overrides[0].id == "dockerfile"
        assert item.overrides[1].skip is True


class TestProviderConfig:
    """Тесты для ProviderConfig."""

    def test_valid_provider_config(self):
        """Тест: валидная конфигурация provider."""
        config = ProviderConfig(
            url="git@github.com:company/toolkit.git",
            version="v1.0.0",
        )
        assert config.url == "git@github.com:company/toolkit.git"
        assert config.version == "v1.0.0"

    def test_provider_config_with_branch(self):
        """Тест: конфигурация с веткой."""
        config = ProviderConfig(
            url="https://github.com/company/toolkit.git",
            version="main",
        )
        assert config.version == "main"

    def test_provider_config_with_commit_hash(self):
        """Тест: конфигурация с commit hash."""
        config = ProviderConfig(
            url="git@github.com:company/toolkit.git",
            version="abc123def456",
        )
        assert config.version == "abc123def456"


class TestProjectToolkitConfig:
    """Тесты для ProjectToolkitConfig."""

    def test_valid_project_config(self):
        """Тест: валидная конфигурация проекта."""
        config = ProjectToolkitConfig(
            provider=ProviderConfig(
                url="git@github.com:company/toolkit.git",
                version="v1.0.0",
            ),
            vars={"python_version": "3.11"},
            sync=[
                SyncItem(alias="python-service"),
            ],
        )
        assert config.provider.url == "git@github.com:company/toolkit.git"
        assert config.vars["python_version"] == "3.11"
        assert len(config.sync) == 1

    def test_project_config_without_vars(self):
        """Тест: конфигурация без глобальных переменных."""
        config = ProjectToolkitConfig(
            provider=ProviderConfig(
                url="git@github.com:company/toolkit.git",
                version="main",
            ),
            sync=[
                SyncItem(alias="minimal-config"),
            ],
        )
        assert config.vars is None

    def test_project_config_multiple_sync_items(self):
        """Тест: конфигурация с несколькими sync items."""
        config = ProjectToolkitConfig(
            provider=ProviderConfig(
                url="git@github.com:company/toolkit.git",
                version="v2.0.0",
            ),
            sync=[
                SyncItem(alias="python-service"),
                SyncItem(alias="docker-configs"),
                SyncItem(
                    alias="ci-cd",
                    overrides=[
                        ComponentOverride(id="github-actions", include_tags=["production"]),
                    ],
                ),
            ],
        )
        assert len(config.sync) == 3
        assert config.sync[2].overrides is not None
