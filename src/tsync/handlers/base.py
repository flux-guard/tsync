"""
Этот модуль содержит абстрактный базовый класс для всех стратегий синхронизации.
"""
from abc import ABC, abstractmethod

from tsync.models.context import Context
from tsync.services.fs import FileSystemService

class BaseStrategy(ABC):
    """
    Абстрактный базовый класс (контракт) для всех стратегий синхронизации.

    Каждая конкретная стратегия (sync_strict, init, template и т.д.) должна
    наследоваться от этого класса и реализовать метод `apply`.
    """

    def __init__(self, fs_service: FileSystemService):
        """
        Каждая стратегия получает необходимые ей сервисы при создании.

        :param fs_service: Экземпляр сервиса для работы с файловой системой.
        """
        self._fs = fs_service

    @abstractmethod
    def apply(self, context: Context) -> None:
        """
        Основной метод, который выполняет логику стратегии.

        :param context: Объект Context, содержащий все данные,
                        необходимые для выполнения операции.
        """
        pass