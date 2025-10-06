"""
Этот модуль содержит реализацию стратегии TemplateStrategy.
"""
import logging

from tsync.models.context import Context
from tsync.services.fs import FileSystemService
from tsync.services.template import TemplateService
from .base import BaseStrategy


class TemplateStrategy(BaseStrategy):
    """
    Стратегия шаблонизации ('template').

    Эта стратегия читает исходный файл как шаблон Jinja2, рендерит его
    с использованием переменных из контекста и записывает результат
    в целевой файл.
    """

    def __init__(self, fs_service: FileSystemService, template_service: TemplateService):
        """
        Стратегия шаблонизации зависит от двух сервисов:
        один для работы с файлами, другой для рендеринга.

        :param fs_service: Сервис для операций с файловой системой.
        :param template_service: Сервис для рендеринга шаблонов.
        """
        super().__init__(fs_service)
        self._template_service = template_service
        self._logger = logging.getLogger(__name__)

    def apply(self, context: Context) -> None:
        """
        Выполняет логику рендеринга шаблона.

        1. Читает содержимое исходного файла.
        2. Использует TemplateService для подстановки переменных.
        3. Записывает результат в целевой файл.

        :param context: Объект Context, содержащий пути и словарь переменных.
        """
        self._logger.info(f"Применяю TEMPLATE: Рендерю '{context.source_path}' в '{context.destination_path}'")

        template_content = self._fs.read_file(context.source_path)
        rendered_content = self._template_service.render(
            template_content=template_content,
            variables=context.variables
        )

        self._fs.write_file(
            path=context.destination_path,
            content=rendered_content
        )