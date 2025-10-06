"""
CLI интерфейс для tsync.
"""
import argparse
import sys
from pathlib import Path

from tsync.app import TsyncApp


def main() -> int:
    """
    Главная точка входа для CLI tsync.

    :return: Код возврата (0 при успехе, 1 при ошибке)
    """
    parser = argparse.ArgumentParser(
        prog="tsync",
        description="Система синхронизации toolkit для управления общими конфигурациями между проектами",
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Путь к директории проекта-потребителя (по умолчанию: текущая директория)",
    )

    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.home() / ".tsync" / "cache",
        help="Путь к директории кэша для репозиториев toolkit (по умолчанию: ~/.tsync/cache)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Включить подробное логирование",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="tsync 0.1.0",
    )

    args = parser.parse_args()

    try:
        app = TsyncApp()
        app.run(
            project_dir=args.project_dir,
            cache_dir=args.cache_dir,
            verbose=args.verbose,
        )
        return 0
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
