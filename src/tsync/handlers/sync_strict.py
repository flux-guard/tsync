"""
Этот модуль содержит реализацию стратегии SyncStrictStrategy.
"""
import logging

from tsync.models.context import Context
from .base import BaseStrategy

class SyncStrictStrategy(BaseStrategy):
    """
    Стратегия принудительной синхронизации ('sync-strict').

    Эта стратегия гарантирует, что файл в проекте consumer-а всегда будет
    точной копией файла из toolkit. Любые локальные изменения в целевом
    файле будут безвозвратно стерты при каждой синхронизации.
    """

    def __init__(self, fs_service):
        super().__init__(fs_service)
        self._logger = logging.getLogger(__name__)

    def apply(self, context: Context) -> None:
        """
        Выполняет логику принудительного копирования файла из источника
        в место назначения.

        Использует FileSystemService для выполнения файловых операций,
        чтобы оставаться независимой от деталей реализации ввода-вывода.

        :param context: Объект Context, содержащий все необходимые пути
                        и конфигурации для выполнения операции.
        """
        self._logger.info(f"Применяю SYNC_STRICT: {context.source_path} -> {context.destination_path}")
        self._fs.copy_file(
            source=context.source_path,
            destination=context.destination_path
        )