"""
Тесты для моделей provider.
"""
import pytest
from pydantic import ValidationError

from tsync.models.provider import (
    VarDefinition,
    File,
    Component,
    Alias,
    ToolkitConfig,
    Variant,
)
from tsync.models.policy import Policy
from tsync.models.merge import MergePriority, MergeType


class TestVarDefinition:
    """Тесты для VarDefinition."""

    def test_valid_required_var(self):
        """Тест: валидная обязательная переменная."""
        var = VarDefinition(
            description="Test variable",
            required=True,
        )
        assert var.required is True
        assert var.default is None

    def test_valid_optional_var_with_default(self):
        """Тест: валидная опциональная переменная с default."""
        var = VarDefinition(
            description="Test variable",
            required=False,
            default="default_value",
        )
        assert var.required is False
        assert var.default == "default_value"

    def test_invalid_required_with_default(self):
        """Тест: ошибка при required=True и наличии default."""
        with pytest.raises(ValidationError) as exc_info:
            VarDefinition(
                description="Test variable",
                required=True,
                default="some_value",
            )
        assert "не может быть одновременно обязательной" in str(exc_info.value)


class TestFile:
    """Тесты для File."""

    def test_valid_sync_strict_file(self):
        """Тест: валидный файл с sync-strict."""
        file = File(
            source="templates/test.txt",
            destination="test.txt",
            policy=Policy.SYNC_STRICT,
        )
        assert file.policy == Policy.SYNC_STRICT
        assert file.merge_as is None
        assert file.merge_priority == MergePriority.TOOLKIT

    def test_valid_merge_file(self):
        """Тест: валидный файл с merge."""
        file = File(
            source="templates/config.yaml",
            destination="config.yaml",
            policy=Policy.MERGE,
            merge_as=MergeType.YAML,
            merge_priority=MergePriority.PROJECT,
        )
        assert file.policy == Policy.MERGE
        assert file.merge_as == MergeType.YAML
        assert file.merge_priority == MergePriority.PROJECT

    def test_invalid_merge_as_without_merge_policy(self):
        """Тест: ошибка при merge_as без policy=merge."""
        with pytest.raises(ValidationError) as exc_info:
            File(
                source="templates/test.txt",
                destination="test.txt",
                policy=Policy.SYNC_STRICT,
                merge_as=MergeType.YAML,
            )
        assert "может использоваться только с policy='merge'" in str(exc_info.value)

    def test_invalid_merge_priority_without_merge_policy(self):
        """Тест: ошибка при merge_priority без policy=merge."""
        with pytest.raises(ValidationError) as exc_info:
            File(
                source="templates/test.txt",
                destination="test.txt",
                policy=Policy.INIT,
                merge_priority=MergePriority.PROJECT,
            )
        assert "может использоваться только с policy='merge'" in str(exc_info.value)

    def test_file_with_tags(self):
        """Тест: файл с тегами."""
        file = File(
            source="templates/docker/Dockerfile",
            destination="Dockerfile",
            policy=Policy.TEMPLATE,
            tags=["docker", "production"],
        )
        assert file.tags == ["docker", "production"]

    def test_file_with_vars(self):
        """Тест: файл с переменными."""
        file = File(
            source="templates/Dockerfile.tpl",
            destination="Dockerfile",
            policy=Policy.TEMPLATE,
            vars={"python_version": "3.11"},
        )
        assert file.vars == {"python_version": "3.11"}


class TestComponent:
    """Тесты для Component."""

    def test_valid_component(self):
        """Тест: валидный компонент."""
        component = Component(
            id="test-component",
            description="Test component",
            var_schema={
                "var1": VarDefinition(description="Variable 1", required=True),
                "var2": VarDefinition(description="Variable 2", required=False, default="default"),
            },
            vars={"var2": "overridden"},
            files=[
                File(
                    source="templates/file1.txt",
                    destination="file1.txt",
                    policy=Policy.SYNC_STRICT,
                )
            ],
        )
        assert component.id == "test-component"
        assert len(component.var_schema) == 2
        assert len(component.files) == 1
        assert component.vars["var2"] == "overridden"

    def test_component_without_schema(self):
        """Тест: компонент без var_schema."""
        component = Component(
            id="simple-component",
            description="Simple component",
            files=[
                File(
                    source="templates/file1.txt",
                    destination="file1.txt",
                    policy=Policy.INIT,
                )
            ],
        )
        assert component.var_schema is None


class TestAlias:
    """Тесты для Alias."""

    def test_valid_alias(self):
        """Тест: валидный alias."""
        alias = Alias(
            description="Test alias",
            components=[
                Component(
                    id="component1",
                    description="Component 1",
                    files=[
                        File(
                            source="templates/file1.txt",
                            destination="file1.txt",
                            policy=Policy.SYNC_STRICT,
                        )
                    ],
                )
            ],
        )
        assert len(alias.components) == 1

    def test_alias_with_variants(self):
        """Тест: alias с вариантами."""
        alias = Alias(
            description="Python service",
            components=[
                Component(
                    id="dockerfile",
                    description="Dockerfile",
                    files=[
                        File(
                            source="templates/Dockerfile.tpl",
                            destination="Dockerfile",
                            policy=Policy.TEMPLATE,
                        )
                    ],
                )
            ],
            variants={
                "poetry": Variant(
                    description="Use Poetry",
                    defaults={"package_manager": "poetry"},
                )
            },
        )
        assert "poetry" in alias.variants
        assert alias.variants["poetry"].defaults["package_manager"] == "poetry"


class TestToolkitConfig:
    """Тесты для ToolkitConfig."""

    def test_valid_toolkit_config(self):
        """Тест: валидная конфигурация toolkit."""
        config = ToolkitConfig(
            toolkit_version="1.0.0",
            aliases={
                "python-service": Alias(
                    description="Python service",
                    components=[
                        Component(
                            id="linters",
                            description="Linters",
                            files=[
                                File(
                                    source="python/.ruff.toml",
                                    destination=".ruff.toml",
                                    policy=Policy.SYNC_STRICT,
                                )
                            ],
                        )
                    ],
                )
            },
        )
        assert config.toolkit_version == "1.0.0"
        assert "python-service" in config.aliases
