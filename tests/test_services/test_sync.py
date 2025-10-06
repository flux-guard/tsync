"""
Тесты для SyncService.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from tsync.services.sync import SyncService
from tsync.models.provider import (
    ToolkitConfig, Alias, Component, File as ProviderFile, VarDefinition, Variant
)
from tsync.models.consumer import (
    ProjectToolkitConfig, ProviderConfig, SyncItem, ComponentOverride, FileOverride
)
from tsync.models.policy import Policy
from tsync.models.merge import MergePriority


@pytest.fixture
def mock_services():
    """Создает mock-объекты для всех зависимостей SyncService."""
    fs_service = Mock()
    git_service = Mock()
    template_service = Mock()
    return fs_service, git_service, template_service


@pytest.fixture
def sync_service(mock_services):
    """Создает экземпляр SyncService с mock-зависимостями."""
    fs, git, template = mock_services
    return SyncService(fs, git, template)


class TestVariableResolution:
    """Тесты для правильной иерархии разрешения переменных."""

    def test_resolve_variables_hierarchy(self, sync_service):
        """Проверяет корректность иерархии переменных."""
        component = Component(
            id="test-component",
            description="Test",
            files=[],
            vars={"comp_var": "comp_value", "override_me": "component"}
        )

        file_config = ProviderFile(
            source="test.txt",
            destination="test.txt",
            policy=Policy.SYNC_STRICT,
            vars={"file_var": "file_value", "override_me": "file"}
        )

        override = ComponentOverride(
            id="test-component",
            vars={"override_var": "override_value"}
        )

        global_vars = {"global_var": "global_value"}
        alias_vars = {"alias_var": "alias_value"}

        result = sync_service._resolve_variables(
            global_vars, alias_vars, component, file_config, override
        )

        assert result["global_var"] == "global_value"
        assert result["alias_var"] == "alias_value"
        assert result["comp_var"] == "comp_value"
        assert result["file_var"] == "file_value"
        assert result["override_var"] == "override_value"
        # Файловые переменные имеют наивысший приоритет
        assert result["override_me"] == "file"

    def test_resolve_variables_with_file_override(self, sync_service):
        """Проверяет, что file-level vars имеют наивысший приоритет."""
        component = Component(
            id="test",
            description="Test",
            files=[],
            vars={"key": "component"}
        )

        file_config = ProviderFile(
            source="test.txt",
            destination="test.txt",
            policy=Policy.TEMPLATE,
            vars={"key": "file"}
        )

        file_override = FileOverride(
            source="test.txt",
            vars={"key": "file_override"}
        )

        override = ComponentOverride(
            id="test",
            vars={"key": "component_override"},
            files=[file_override]
        )

        result = sync_service._resolve_variables(
            {}, {}, component, file_config, override
        )

        # File-level override должен побеждать всех
        assert result["key"] == "file_override"


class TestVariantSupport:
    """Тесты для поддержки variants."""

    def test_get_variant_variables_success(self, sync_service):
        """Проверяет успешное получение переменных из variant."""
        variant = Variant(
            description="Poetry variant",
            defaults={"package_manager": "poetry", "python_version": "3.11"}
        )

        alias = Mock()
        alias.variants = {"poetry": variant}

        result = sync_service._get_variant_variables(alias, "poetry")

        assert result == {"package_manager": "poetry", "python_version": "3.11"}

    def test_get_variant_variables_not_found(self, sync_service, caplog):
        """Проверяет обработку несуществующего variant."""
        alias = Mock()
        alias.variants = {"poetry": Mock()}

        result = sync_service._get_variant_variables(alias, "pip")

        assert result == {}
        assert "Variant 'pip' не найден" in caplog.text

    def test_get_variant_variables_none(self, sync_service):
        """Проверяет поведение при variant=None."""
        alias = Mock()
        result = sync_service._get_variant_variables(alias, None)
        assert result == {}


class TestSchemaValidation:
    """Тесты для валидации schema переменных."""

    def test_validate_schema_all_required_provided(self, sync_service):
        """Проверяет успешную валидацию при наличии всех обязательных переменных."""
        component = Component(
            id="test",
            description="Test",
            files=[],
            var_schema={
                "required_var": VarDefinition(
                    description="Required variable",
                    required=True
                )
            }
        )

        global_vars = {"required_var": "value"}

        # Не должно быть исключения
        sync_service._validate_component_schema(component, global_vars, None)

    def test_validate_schema_missing_required(self, sync_service):
        """Проверяет, что отсутствие обязательной переменной вызывает ошибку."""
        component = Component(
            id="test",
            description="Test",
            files=[],
            var_schema={
                "required_var": VarDefinition(
                    description="This is required",
                    required=True
                )
            }
        )

        global_vars = {}

        with pytest.raises(ValueError) as exc_info:
            sync_service._validate_component_schema(component, global_vars, None)

        assert "required_var" in str(exc_info.value)
        assert "This is required" in str(exc_info.value)

    def test_validate_schema_optional_missing_ok(self, sync_service):
        """Проверяет, что отсутствие опциональной переменной не вызывает ошибку."""
        component = Component(
            id="test",
            description="Test",
            files=[],
            var_schema={
                "optional_var": VarDefinition(
                    description="Optional",
                    required=False,
                    default="default_value"
                )
            }
        )

        # Не должно быть исключения
        sync_service._validate_component_schema(component, {}, None)


class TestPathBuilding:
    """Тесты для построения путей назначения."""

    def test_build_destination_path_no_override(self, sync_service):
        """Проверяет базовый путь без override."""
        project_dir = Path("/project")
        file_config = ProviderFile(
            source="src/file.txt",
            destination="dest/file.txt",
            policy=Policy.SYNC_STRICT
        )

        result = sync_service._build_destination_path(project_dir, file_config, None)

        assert result == Path("/project/dest/file.txt")

    def test_build_destination_path_with_destination_root(self, sync_service):
        """Проверяет путь с destination_root override."""
        project_dir = Path("/project")
        file_config = ProviderFile(
            source="src/file.txt",
            destination="file.txt",
            policy=Policy.SYNC_STRICT
        )
        override = ComponentOverride(
            id="test",
            destination_root="custom/dir"
        )

        result = sync_service._build_destination_path(project_dir, file_config, override)

        assert result == Path("/project/custom/dir/file.txt")

    def test_build_destination_path_file_level_override(self, sync_service):
        """Проверяет file-level destination override (наивысший приоритет)."""
        project_dir = Path("/project")
        file_config = ProviderFile(
            source="src/file.txt",
            destination="original.txt",
            policy=Policy.SYNC_STRICT
        )

        file_override = FileOverride(
            source="src/file.txt",
            destination="completely/different/path.txt"
        )

        override = ComponentOverride(
            id="test",
            destination_root="ignored/root",
            files=[file_override]
        )

        result = sync_service._build_destination_path(project_dir, file_config, override)

        # File-level override должен иметь приоритет над destination_root
        assert result == Path("/project/completely/different/path.txt")


class TestTagFiltering:
    """Тесты для фильтрации файлов по тегам."""

    def test_should_include_file_no_override(self, sync_service):
        """Без override все файлы включаются."""
        file_config = ProviderFile(
            source="test.txt",
            destination="test.txt",
            policy=Policy.SYNC_STRICT,
            tags=["python", "docker"]
        )

        assert sync_service._should_include_file(file_config, None) is True

    def test_should_include_file_with_include_tags_match(self, sync_service):
        """Файл включается если хотя бы один тег совпадает с include_tags."""
        file_config = ProviderFile(
            source="test.txt",
            destination="test.txt",
            policy=Policy.SYNC_STRICT,
            tags=["python", "docker"]
        )

        override = ComponentOverride(
            id="test",
            include_tags=["python", "go"]
        )

        assert sync_service._should_include_file(file_config, override) is True

    def test_should_include_file_with_include_tags_no_match(self, sync_service):
        """Файл исключается если ни один тег не совпадает с include_tags."""
        file_config = ProviderFile(
            source="test.txt",
            destination="test.txt",
            policy=Policy.SYNC_STRICT,
            tags=["python"]
        )

        override = ComponentOverride(
            id="test",
            include_tags=["go", "rust"]
        )

        assert sync_service._should_include_file(file_config, override) is False

    def test_should_include_file_with_exclude_tags(self, sync_service):
        """Файл исключается если хотя бы один тег в exclude_tags."""
        file_config = ProviderFile(
            source="test.txt",
            destination="test.txt",
            policy=Policy.SYNC_STRICT,
            tags=["python", "docker"]
        )

        override = ComponentOverride(
            id="test",
            exclude_tags=["docker"]
        )

        assert sync_service._should_include_file(file_config, override) is False

    def test_exclude_takes_precedence_over_include(self, sync_service):
        """exclude_tags имеет приоритет над include_tags."""
        file_config = ProviderFile(
            source="test.txt",
            destination="test.txt",
            policy=Policy.SYNC_STRICT,
            tags=["python", "docker"]
        )

        override = ComponentOverride(
            id="test",
            include_tags=["python"],  # Совпадает
            exclude_tags=["docker"]    # Тоже совпадает - должен исключить
        )

        assert sync_service._should_include_file(file_config, override) is False
