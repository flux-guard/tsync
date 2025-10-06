"""
Главный модуль приложения tsync, координирующий работу всех сервисов.
"""
import logging
from pathlib import Path

from tsync.services.fs import FileSystemService
from tsync.services.git import GitService
from tsync.services.sync import SyncService
from tsync.services.template import TemplateService


class TsyncApp:
    """
    Главный класс приложения tsync.

    Отвечает за инициализацию всех сервисов и запуск процесса синхронизации.
    """

    def __init__(self) -> None:
        """Инициализирует приложение."""
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        project_dir: Path,
        cache_dir: Path,
        verbose: bool = False,
    ) -> None:
        """
        Запускает процесс синхронизации.

        :param project_dir: Путь к директории проекта-потребителя
        :param cache_dir: Путь к директории кэша для репозиториев toolkit
        :param verbose: Включить подробное логирование
        """
        self._setup_logging(verbose)

        self.logger.info(f"Запускаю tsync для проекта: {project_dir}")
        self.logger.info(f"Директория кэша: {cache_dir}")

        # Инициализация сервисов
        fs_service = FileSystemService()
        git_service = GitService(cache_dir)
        template_service = TemplateService()
        sync_service = SyncService(fs_service, git_service, template_service)

        # Запуск синхронизации
        sync_service.run(project_dir=project_dir, toolkit_cache_dir=cache_dir)

        self.logger.info("Синхронизация успешно завершена")

    def _setup_logging(self, verbose: bool) -> None:
        """
        Настраивает систему логирования.

        :param verbose: Если True, устанавливает уровень DEBUG, иначе INFO
        """
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
