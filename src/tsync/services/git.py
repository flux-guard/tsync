"""
Этот модуль содержит GitService, который инкапсулирует
все операции по взаимодействию с Git-репозиториями.
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List

class GitServiceError(Exception):
    """Специальное исключение для ошибок, возникших при работе GitService."""
    pass

class GitService:
    """
    Сервис для инкапсуляции всех операций с Git.

    Отвечает за клонирование, обновление и переключение версий
    в репозиториях.
    """
    def __init__(self, cache_dir: Path):
        """
        Инициализирует сервис.

        :param cache_dir: Путь к директории, где будут храниться
                          клонированные репозитории.
        """
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(__name__)

    def _run_command(self, command: List[str], cwd: Path, env: Dict[str, str] = None) -> None:
        """
        Вспомогательный метод для выполнения Git-команд.

        :param command: Команда для выполнения в виде списка аргументов.
        :param cwd: Рабочая директория, в которой будет выполнена команда.
        :param env: Дополнительные переменные окружения (опционально).
        :raises GitServiceError: Если команда завершилась с ошибкой.
        """
        # Подготавливаем окружение с защитой от интерактивных запросов SSH
        command_env = os.environ.copy()
        if env:
            command_env.update(env)

        # Добавляем GIT_SSH_COMMAND для неинтерактивной работы с SSH
        # BatchMode=yes предотвращает запрос пароля
        if "GIT_SSH_COMMAND" not in command_env:
            command_env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

        try:
            subprocess.run(
                command,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
                env=command_env
            )
        except subprocess.CalledProcessError as e:
            error_message = f"Git команда не выполнена: {' '.join(command)}\nОшибка: {e.stderr}"
            raise GitServiceError(error_message)

    def clone_or_update(self, url: str, destination: Path) -> None:
        """
        Клонирует репозиторий, если он не существует локально, или
        обновляет его (git fetch), если он уже есть.

        :param url: URL Git-репозитория.
        :param destination: Локальный путь, куда будет клонирован репозиторий.
        """
        if destination.exists():
            self._logger.info(f"Обновляю репозиторий в: {destination}")
            self._run_command(["git", "fetch", "--all", "--prune"], cwd=destination)
        else:
            self._logger.info(f"Клонирую репозиторий из '{url}' в '{destination}'")
            self._run_command(["git", "clone", url, str(destination)], cwd=self._cache_dir)

    def checkout(self, repo_path: Path, version: str) -> None:
        """
        Переключает локальный репозиторий на указанную версию.

        Это может быть тег, ветка или хеш коммита.

        :param repo_path: Путь к локальному репозиторию.
        :param version: Версия для переключения (например, "v1.2.0", "main").
        """
        self._logger.info(f"Переключаюсь на версию '{version}' в: {repo_path}")
        self._run_command(["git", "checkout", version], cwd=repo_path)