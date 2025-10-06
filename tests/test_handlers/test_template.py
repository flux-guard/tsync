"""
Тесты для TemplateStrategy.
"""
import pytest
from pathlib import Path

from tsync.handlers.template import TemplateStrategy
from tsync.models.context import Context
from tsync.models.provider import File
from tsync.models.policy import Policy


class TestTemplateStrategy:
    """Тесты для TemplateStrategy."""

    def test_template_renders_simple_template(self, temp_dir, fs_service, template_service):
        """Тест: рендеринг простого шаблона."""
        strategy = TemplateStrategy(fs_service, template_service)

        # Создаем шаблон
        source = temp_dir / "template.txt"
        source.write_text("Hello, {{ name }}!")

        destination = temp_dir / "output.txt"

        file_config = File(
            source="template.txt",
            destination="output.txt",
            policy=Policy.TEMPLATE,
        )

        context = Context(
            source_path=source,
            destination_path=destination,
            file_config=file_config,
            variables={"name": "World"},
            destination_exists=False,
        )

        strategy.apply(context)

        assert destination.exists()
        assert destination.read_text() == "Hello, World!"

    def test_template_renders_dockerfile(self, temp_dir, fs_service, template_service):
        """Тест: рендеринг Dockerfile шаблона."""
        strategy = TemplateStrategy(fs_service, template_service)

        # Создаем Dockerfile шаблон
        source = temp_dir / "Dockerfile.tpl"
        template_content = """FROM python:{{ python_version }}-slim
WORKDIR {{ workdir }}
COPY . .
CMD ["python", "{{ entrypoint }}"]
"""
        source.write_text(template_content)

        destination = temp_dir / "Dockerfile"

        file_config = File(
            source="Dockerfile.tpl",
            destination="Dockerfile",
            policy=Policy.TEMPLATE,
        )

        context = Context(
            source_path=source,
            destination_path=destination,
            file_config=file_config,
            variables={
                "python_version": "3.11",
                "workdir": "/app",
                "entrypoint": "main.py",
            },
            destination_exists=False,
        )

        strategy.apply(context)

        result = destination.read_text()
        assert "FROM python:3.11-slim" in result
        assert "WORKDIR /app" in result
        assert 'CMD ["python", "main.py"]' in result

    def test_template_overwrites_existing_file(self, temp_dir, fs_service, template_service):
        """Тест: перезапись существующего файла."""
        strategy = TemplateStrategy(fs_service, template_service)

        source = temp_dir / "template.txt"
        source.write_text("Version: {{ version }}")

        # Создаем существующий файл
        destination = temp_dir / "output.txt"
        destination.write_text("Old version")

        file_config = File(
            source="template.txt",
            destination="output.txt",
            policy=Policy.TEMPLATE,
        )

        context = Context(
            source_path=source,
            destination_path=destination,
            file_config=file_config,
            variables={"version": "2.0.0"},
            destination_exists=True,
        )

        strategy.apply(context)

        assert destination.read_text() == "Version: 2.0.0"

    def test_template_with_loops(self, temp_dir, fs_service, template_service):
        """Тест: шаблон с циклами."""
        strategy = TemplateStrategy(fs_service, template_service)

        source = temp_dir / "list.txt"
        template_content = """Dependencies:
{% for dep in dependencies %}
- {{ dep }}
{% endfor %}"""
        source.write_text(template_content)

        destination = temp_dir / "output.txt"

        file_config = File(
            source="list.txt",
            destination="output.txt",
            policy=Policy.TEMPLATE,
        )

        context = Context(
            source_path=source,
            destination_path=destination,
            file_config=file_config,
            variables={
                "dependencies": ["pytest", "black", "ruff"],
            },
            destination_exists=False,
        )

        strategy.apply(context)

        result = destination.read_text()
        assert "- pytest" in result
        assert "- black" in result
        assert "- ruff" in result

    def test_template_with_conditionals(self, temp_dir, fs_service, template_service):
        """Тест: шаблон с условиями."""
        strategy = TemplateStrategy(fs_service, template_service)

        source = temp_dir / "config.txt"
        template_content = """{% if env == "production" %}
PRODUCTION CONFIG
{% else %}
DEVELOPMENT CONFIG
{% endif %}"""
        source.write_text(template_content)

        destination = temp_dir / "output.txt"

        file_config = File(
            source="config.txt",
            destination="output.txt",
            policy=Policy.TEMPLATE,
        )

        context = Context(
            source_path=source,
            destination_path=destination,
            file_config=file_config,
            variables={"env": "production"},
            destination_exists=False,
        )

        strategy.apply(context)

        result = destination.read_text()
        assert "PRODUCTION CONFIG" in result
        assert "DEVELOPMENT CONFIG" not in result
