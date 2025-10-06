"""
Этот модуль содержит TemplateService, который инкапсулирует
логику рендеринга шаблонов с использованием Jinja2.
"""
from typing import Any, Dict
from jinja2 import Environment, StrictUndefined

class TemplateService:
    """
    Сервис для рендеринга шаблонов.

    Использует библиотеку Jinja2 для подстановки переменных в
    строки-шаблоны. Работает напрямую со строками без использования
    файлового загрузчика.
    """
    def __init__(self):
        # Используем базовый Environment без FileSystemLoader для работы со строками
        # StrictUndefined генерирует ошибку при отсутствующих переменных
        self._env = Environment(undefined=StrictUndefined)

    def render(self, template_content: str, variables: Dict[str, Any]) -> str:
        """
        Рендерит строку-шаблон с предоставленными переменными.

        :param template_content: Строка, содержащая синтаксис шаблона Jinja2.
        :param variables: Словарь с переменными для подстановки.
        :return: Готовая строка с подставленными значениями.
        :raises jinja2.UndefinedError: Если в шаблоне используется неопределенная переменная
        """
        template = self._env.from_string(template_content)
        return template.render(**variables)