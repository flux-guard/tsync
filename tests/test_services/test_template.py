"""
Тесты для TemplateService.
"""
import pytest
from jinja2 import TemplateError

from tsync.services.template import TemplateService


class TestTemplateService:
    """Тесты для TemplateService."""

    def test_render_simple_template(self, template_service):
        """Тест: рендеринг простого шаблона."""
        template = "Hello, {{ name }}!"
        variables = {"name": "World"}

        result = template_service.render(template, variables)
        assert result == "Hello, World!"

    def test_render_multiline_template(self, template_service):
        """Тест: рендеринг многострочного шаблона."""
        template = """FROM python:{{ python_version }}
WORKDIR {{ workdir }}
CMD ["python", "{{ entrypoint }}"]"""

        variables = {
            "python_version": "3.11",
            "workdir": "/app",
            "entrypoint": "main.py",
        }

        result = template_service.render(template, variables)

        assert "FROM python:3.11" in result
        assert "WORKDIR /app" in result
        assert 'CMD ["python", "main.py"]' in result

    def test_render_with_loops(self, template_service):
        """Тест: рендеринг с циклами."""
        template = """packages:
{% for pkg in packages %}
  - {{ pkg }}
{% endfor %}"""

        variables = {
            "packages": ["pytest", "black", "ruff"],
        }

        result = template_service.render(template, variables)

        assert "pytest" in result
        assert "black" in result
        assert "ruff" in result

    def test_render_with_conditionals(self, template_service):
        """Тест: рендеринг с условиями."""
        template = """{% if env == "production" %}
PRODUCTION MODE
{% else %}
DEVELOPMENT MODE
{% endif %}"""

        # Production
        result_prod = template_service.render(template, {"env": "production"})
        assert "PRODUCTION MODE" in result_prod
        assert "DEVELOPMENT MODE" not in result_prod

        # Development
        result_dev = template_service.render(template, {"env": "development"})
        assert "DEVELOPMENT MODE" in result_dev
        assert "PRODUCTION MODE" not in result_dev

    def test_render_missing_variable(self, template_service):
        """Тест: ошибка при отсутствии переменной."""
        template = "Hello, {{ missing_var }}!"
        variables = {}

        # С StrictUndefined должна быть ошибка при отсутствующих переменных
        from jinja2 import UndefinedError
        with pytest.raises(UndefinedError):
            template_service.render(template, variables)

    def test_render_with_filters(self, template_service):
        """Тест: рендеринг с фильтрами."""
        template = "{{ name | upper }}"
        variables = {"name": "test"}

        result = template_service.render(template, variables)
        assert result == "TEST"

    def test_render_with_nested_variables(self, template_service):
        """Тест: рендеринг с вложенными переменными."""
        template = "{{ config.database.host }}:{{ config.database.port }}"
        variables = {
            "config": {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                }
            }
        }

        result = template_service.render(template, variables)
        assert result == "localhost:5432"

    def test_render_empty_template(self, template_service):
        """Тест: рендеринг пустого шаблона."""
        template = ""
        variables = {"var": "value"}

        result = template_service.render(template, variables)
        assert result == ""

    def test_render_no_variables(self, template_service):
        """Тест: рендеринг без переменных."""
        template = "Static content"
        variables = {}

        result = template_service.render(template, variables)
        assert result == "Static content"
