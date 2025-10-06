"""
Этот модуль содержит FileSystemService, который инкапсулирует
все операции с локальной файловой системой.
"""
import logging
import yaml
from pathlib import Path
from typing import Any, Dict


class FileSystemError(Exception):
    """Специальное исключение для ошибок файловой системы."""
    pass

class FileSystemService:
    """
    Сервис для инкапсуляции всех операций ввода-вывода, связанных
    с файловой системой. Предоставляет высокоуровневые методы для чтения,
    записи и проверки файлов, скрывая детали реализации.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def path_exists(self, path: Path) -> bool:
        """
        Проверяет, существует ли файл или директория по указанному пути.

        :param path: Путь для проверки.
        :return: True, если путь существует, иначе False.
        """
        return path.exists()

    def ensure_dir_exists(self, path: Path) -> None:
        """
        Гарантирует, что родительская директория для указанного пути файла
        существует. Если ее нет, она будет создана.

        :param path: Путь к файлу, для которого нужно создать родительскую директорию.
        """
        # .parent получает директорию, содержащую файл
        path.parent.mkdir(parents=True, exist_ok=True)

    def read_yaml(self, path: Path) -> Dict[str, Any]:
        """
        Читает YAML-файл и парсит его в Python-словарь.

        :param path: Путь к YAML-файлу.
        :return: Содержимое файла в виде словаря.
        :raises FileSystemError: Если файл не найден или невалидный YAML
        """
        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    raise FileSystemError(f"Пустой или невалидный YAML файл: {path}")
                return data
        except FileNotFoundError:
            raise FileSystemError(f"YAML файл не найден: {path}")
        except yaml.YAMLError as e:
            raise FileSystemError(f"Невалидный YAML в файле {path}: {e}")

    def read_file(self, path: Path) -> str:
        """
        Читает текстовый файл и возвращает его содержимое как строку.

        :param path: Путь к текстовому файлу.
        :return: Содержимое файла.
        :raises FileSystemError: Если файл не найден или недоступен
        """
        try:
            with path.open("r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileSystemError(f"Файл не найден: {path}")
        except Exception as e:
            raise FileSystemError(f"Ошибка чтения файла {path}: {e}")

    def validate_path_within_directory(self, path: Path, base_dir: Path) -> None:
        """
        Проверяет, что путь находится внутри указанной базовой директории.
        Защита от path traversal атак (../../etc/passwd).

        :param path: Путь для проверки.
        :param base_dir: Базовая директория, внутри которой должен находиться путь.
        :raises FileSystemError: Если путь выходит за пределы базовой директории.
        """
        try:
            path.resolve().relative_to(base_dir.resolve())
        except ValueError:
            raise FileSystemError(
                f"Путь '{path}' выходит за пределы разрешенной директории '{base_dir}'. "
                f"Это может быть попыткой path traversal атаки."
            )

    def write_file(self, path: Path, content: str) -> None:
        """
        Записывает строковый контент в файл.

        Перед записью гарантирует, что родительская директория существует.

        :param path: Путь к целевому файлу.
        :param content: Строковый контент для записи.
        :raises FileSystemError: Если не удалось записать файл
        """
        try:
            self.ensure_dir_exists(path)
            path.write_text(content, encoding="utf-8")
            self._logger.debug(f"Успешно записан файл: {path}")
        except Exception as e:
            raise FileSystemError(f"Ошибка записи файла {path}: {e}")

    def copy_file(self, source: Path, destination: Path) -> None:
        """
        Копирует файл из одного места в другое.

        Перед копированием гарантирует, что родительская директория
        для целевого файла существует.

        :param source: Путь к исходному файлу.
        :param destination: Путь к целевому файлу.
        :raises FileSystemError: Если не удалось скопировать файл
        """
        try:
            if not source.exists():
                raise FileSystemError(f"Исходный файл не существует: {source}")
            self.ensure_dir_exists(destination)
            destination.write_bytes(source.read_bytes())
            self._logger.debug(f"Успешно скопирован файл: {source} -> {destination}")
        except FileSystemError:
            raise
        except Exception as e:
            raise FileSystemError(f"Ошибка копирования файла из {source} в {destination}: {e}")