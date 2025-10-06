"""
Этот модуль содержит реализацию стратегии InitStrategy.
"""
import logging

from tsync.models.context import Context
from .base import BaseStrategy


class InitStrategy(BaseStrategy):
    """
    Стратегия инициализации ('init').

    Эта стратегия копирует файл из toolkit в проект consumer-а только в том
    случае, если файл в месте назначения еще не существует. Если файл уже
    существует, стратегия ничего не делает, сохраняя любые локальные изменения.
    """

    def __init__(self, fs_service):
        super().__init__(fs_service)
        self._logger = logging.getLogger(__name__)

    def apply(self, context: Context) -> None:
        """
        Выполняет логику инициализации файла.

        Проверяет флаг `destination_exists` в контексте. Если он `False`,
        файл копируется. Если `True`, операция пропускается.

        :param context: Объект Context, содержащий все необходимые пути
                        и флаги для выполнения операции.
        """
        if context.destination_exists:
            self._logger.info(f"Файл '{context.destination_path}' уже существует, пропускаю (политика INIT)")
            return

        self._logger.info(f"Применяю INIT: Создаю новый файл '{context.destination_path}'")
        self._fs.copy_file(
            source=context.source_path,
            destination=context.destination_path
        )