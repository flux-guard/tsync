"""
Этот модуль содержит SyncService — главный сервис-оркестратор,
который управляет всем процессом синхронизации.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from tsync.models.consumer import ProjectToolkitConfig, ComponentOverride, FileOverride
from tsync.models.provider import ToolkitConfig, File as ProviderFile, Component as ProviderComponent
from tsync.models.context import Context
from tsync.models.policy import Policy
from tsync.handlers.base import BaseStrategy
from tsync.handlers.sync_strict import SyncStrictStrategy
from tsync.handlers.init import InitStrategy
from tsync.handlers.template import TemplateStrategy
from tsync.handlers.merge import MergeStrategy
from .fs import FileSystemService
from .git import GitService
from .template import TemplateService

class SyncService:
    """
    Главный сервис-оркестратор.
    Отвечает за весь жизненный цикл синхронизации: чтение конфигураций,
    получение toolkit-а, обработку правил и вызов нужных стратегий.
    """

    def __init__(
            self,
            fs_service: FileSystemService,
            git_service: GitService,
            template_service: TemplateService,
    ):
        self._fs = fs_service
        self._git = git_service
        self._logger = logging.getLogger(__name__)

        # Создаем "фабрику" обработчиков. Экземпляры создаются один раз
        # и используются повторно для каждого файла.
        self._handlers: Dict[Policy, BaseStrategy] = {
            Policy.SYNC_STRICT: SyncStrictStrategy(fs_service),
            Policy.INIT: InitStrategy(fs_service),
            Policy.TEMPLATE: TemplateStrategy(fs_service, template_service),
            Policy.MERGE: MergeStrategy(fs_service),
        }

    def run(self, project_dir: Path, toolkit_cache_dir: Path) -> None:
        """
        Запускает полный процесс синхронизации для указанного проекта.

        :raises Exception: При ошибках конфигурации или синхронизации
        """
        self._logger.info(f"Начало синхронизации проекта в директории: {project_dir}")

        try:
            # 1. Загружаем конфигурацию consumer-а
            consumer_config_path = project_dir / ".project.toolkit.yml"
            if not consumer_config_path.exists():
                raise FileNotFoundError(
                    f"Конфигурация consumer не найдена: {consumer_config_path}. "
                    f"Убедитесь, что в директории проекта есть .project.toolkit.yml"
                )
            consumer_config = self._load_consumer_config(consumer_config_path)
            provider_config = consumer_config.provider

            # 2. Получаем нужную версию toolkit-а
            toolkit_path = self._get_provider_toolkit(
                url=provider_config.url,
                version=provider_config.version,
                cache_dir=toolkit_cache_dir
            )

            # 3. Загружаем конфигурацию provider-а
            provider_config_path = toolkit_path / ".toolkit.yml"
            if not provider_config_path.exists():
                raise FileNotFoundError(
                    f"Конфигурация provider не найдена: {provider_config_path}. "
                    f"Убедитесь, что репозиторий toolkit содержит .toolkit.yml"
                )
            provider_config_model = self._load_provider_config(provider_config_path)

            # 4. Обрабатываем и синхронизируем файлы
            self._process_sync_items(
                consumer_config=consumer_config,
                provider_config=provider_config_model,
                project_dir=project_dir,
                toolkit_dir=toolkit_path,
            )
            self._logger.info("Синхронизация успешно завершена")

        except Exception as e:
            self._logger.error(f"Синхронизация не выполнена: {e}")
            raise

    def _load_consumer_config(self, path: Path) -> ProjectToolkitConfig:
        """
        Читает и парсит .project.toolkit.yml.

        :raises ValidationError: Если конфигурация невалидна
        """
        from pydantic import ValidationError

        self._logger.debug(f"Загружаю конфигурацию consumer из: {path}")
        data = self._fs.read_yaml(path)
        try:
            return ProjectToolkitConfig.model_validate(data)
        except ValidationError as e:
            self._logger.error(f"Невалидная конфигурация consumer в {path}: {e}")
            raise ValueError(f"Ошибка валидации конфигурации consumer: {e}") from e

    def _load_provider_config(self, path: Path) -> ToolkitConfig:
        """
        Читает и парсит .toolkit.yml.

        :raises ValidationError: Если конфигурация невалидна
        """
        from pydantic import ValidationError

        self._logger.debug(f"Загружаю конфигурацию provider из: {path}")
        data = self._fs.read_yaml(path)
        try:
            return ToolkitConfig.model_validate(data)
        except ValidationError as e:
            self._logger.error(f"Невалидная конфигурация provider в {path}: {e}")
            raise ValueError(f"Ошибка валидации конфигурации provider: {e}") from e

    def _get_provider_toolkit(self, url: str, version: str, cache_dir: Path) -> Path:
        """Клонирует или обновляет toolkit и переключается на нужную версию."""
        # Создаем уникальное имя папки для кэша на основе URL
        repo_dir_name = url.split('/')[-1].replace('.git', '')
        repo_path = cache_dir / repo_dir_name

        self._git.clone_or_update(url, repo_path)
        self._git.checkout(repo_path, version)
        return repo_path

    def _process_sync_items(
            self,
            consumer_config: ProjectToolkitConfig,
            provider_config: ToolkitConfig,
            project_dir: Path,
            toolkit_dir: Path,
    ) -> None:
        """
        Главный цикл, который итерируется по всем `sync` элементам
        из манифеста consumer-а.
        """
        for sync_item in consumer_config.sync:
            alias_name = sync_item.alias
            alias = provider_config.aliases.get(alias_name)
            if not alias:
                self._logger.warning(f"Alias '{alias_name}' не найден в provider, пропускаю.")
                continue

            self._logger.info(f"Обрабатываю alias: '{alias_name}'")

            # Получаем переменные из variant, если указан
            variant_vars = self._get_variant_variables(alias, sync_item.variant)

            # Объединяем глобальные переменные consumer с переменными из variant
            base_vars = {**(consumer_config.vars or {}), **variant_vars}

            for component in alias.components:
                override = self._find_override_for_component(sync_item.overrides, component.id)
                self._process_component(
                    component=component,
                    override=override,
                    global_vars=base_vars,
                    alias_vars=alias.vars or {},
                    project_dir=project_dir,
                    toolkit_dir=toolkit_dir,
                )

    def _get_variant_variables(self, alias, variant_name: Optional[str]) -> Dict[str, Any]:
        """
        Получает переменные из указанного variant'а.

        :param alias: Объект Alias из provider конфигурации
        :param variant_name: Имя variant'а или None
        :return: Словарь переменных из variant'а или пустой словарь
        """
        if not variant_name:
            return {}

        if not alias.variants or variant_name not in alias.variants:
            self._logger.warning(
                f"Variant '{variant_name}' не найден в alias '{alias}', "
                f"доступные варианты: {list(alias.variants.keys()) if alias.variants else []}"
            )
            return {}

        variant = alias.variants[variant_name]
        self._logger.info(f"Применяю variant '{variant_name}': {variant.description}")
        return variant.defaults.copy()

    def _find_override_for_component(
        self, overrides: Optional[List[ComponentOverride]], component_id: str
    ) -> Optional[ComponentOverride]:
        """Находит переопределение для компонента по его ID."""
        if not overrides:
            return None
        for override in overrides:
            if override.id == component_id:
                return override
        return None

    def _process_component(
            self,
            component: ProviderComponent,
            override: Optional[ComponentOverride],
            global_vars: Dict[str, Any],
            alias_vars: Dict[str, Any],
            project_dir: Path,
            toolkit_dir: Path,
    ) -> None:
        """Обрабатывает один компонент: фильтрует файлы и вызывает их синхронизацию."""
        if override and override.skip:
            self._logger.info(f"Пропускаю компонент: '{component.id}' из-за правила override.")
            return

        # Валидация schema переменных компонента
        self._validate_component_schema(component, global_vars, override)

        for file_config in component.files:
            # Проверка skip на уровне файла в override
            if override and override.files:
                file_skip = self._is_file_skipped(file_config.source, override.files)
                if file_skip:
                    self._logger.info(f"Пропускаю файл '{file_config.source}' из-за file-level skip в override")
                    continue

            # Фильтрация по тегам
            if not self._should_include_file(file_config, override):
                self._logger.debug(f"Пропускаю файл '{file_config.source}' из-за фильтрации по тегам")
                continue

            # Собираем итоговый словарь переменных
            variables = self._resolve_variables(global_vars, alias_vars, component, file_config, override)

            # Формируем контекст для этого файла
            source_path = toolkit_dir / file_config.source
            destination_path = self._build_destination_path(project_dir, file_config, override)

            # Валидация пути (защита от path traversal)
            self._fs.validate_path_within_directory(destination_path, project_dir)

            context = Context(
                source_path=source_path,
                destination_path=destination_path,
                file_config=file_config,
                variables=variables,
                destination_exists=self._fs.path_exists(destination_path)
            )

            # Выбираем и вызываем нужный обработчик
            handler = self._handlers.get(file_config.policy)
            if handler:
                handler.apply(context)
            else:
                self._logger.warning(
                    f"Обработчик для политики '{file_config.policy.value}' не найден, пропускаю файл '{source_path}'"
                )

    def _build_destination_path(
        self, project_dir: Path, file_config: ProviderFile, override: Optional[ComponentOverride]
    ) -> Path:
        """
        Строит финальный путь назначения с учетом всех возможных override'ов.

        Приоритет (от высокого к низкому):
        1. File-level destination override
        2. Component-level destination_root override
        3. Базовый destination из provider

        :param project_dir: Корневая директория проекта
        :param file_config: Конфигурация файла из provider
        :param override: Переопределение компонента из consumer (опционально)
        :return: Полный путь к файлу назначения
        """
        # Проверяем file-level destination override (наивысший приоритет)
        if override and override.files:
            for file_override in override.files:
                if file_override.source == file_config.source and file_override.destination:
                    return project_dir / file_override.destination

        # Проверяем component-level destination_root override
        if override and override.destination_root:
            return project_dir / override.destination_root / file_config.destination

        # Используем базовый destination из provider
        return project_dir / file_config.destination

    def _validate_component_schema(
        self,
        component: ProviderComponent,
        global_vars: Dict[str, Any],
        override: Optional[ComponentOverride]
    ) -> None:
        """
        Валидирует обязательные переменные согласно var_schema компонента.

        :param component: Компонент из provider
        :param global_vars: Глобальные переменные (включая variant)
        :param override: Переопределение компонента из consumer
        :raises ValueError: Если обязательная переменная не предоставлена
        """
        if not component.var_schema:
            return

        # Собираем все доступные переменные для проверки
        available_vars = global_vars.copy()
        if component.vars:
            available_vars.update(component.vars)
        if override and override.vars:
            available_vars.update(override.vars)

        # Проверяем обязательные переменные
        missing_vars = []
        for var_name, var_def in component.var_schema.items():
            if var_def.required and var_name not in available_vars:
                missing_vars.append(f"  - {var_name}: {var_def.description}")

        if missing_vars:
            raise ValueError(
                f"Компонент '{component.id}' требует обязательные переменные, которые не предоставлены:\n"
                + "\n".join(missing_vars)
            )

    def _is_file_skipped(self, file_source: str, file_overrides: List[FileOverride]) -> bool:
        """
        Проверяет, помечен ли файл как skip=True в file-level overrides.

        :param file_source: source файла из provider
        :param file_overrides: список FileOverride из consumer
        :return: True, если файл должен быть пропущен
        """
        for file_override in file_overrides:
            if file_override.source == file_source and file_override.skip:
                return True
        return False

    def _should_include_file(
        self, file_config: ProviderFile, override: Optional[ComponentOverride]
    ) -> bool:
        """
        Проверяет, должен ли файл быть синхронизирован на основе тегов.

        :param file_config: Конфигурация файла из provider
        :param override: Переопределение компонента из consumer
        :return: True, если файл должен быть синхронизирован
        """
        if not override:
            return True

        file_tags = set(file_config.tags or [])

        # Проверка include_tags: если указаны, файл должен иметь хотя бы один из этих тегов
        if override.include_tags:
            if not file_tags.intersection(override.include_tags):
                return False

        # Проверка exclude_tags: если файл имеет хотя бы один из этих тегов, он исключается
        if override.exclude_tags:
            if file_tags.intersection(override.exclude_tags):
                return False

        return True

    def _resolve_variables(
            self,
            global_vars: Dict[str, Any],
            alias_vars: Dict[str, Any],
            component: ProviderComponent,
            file_config: ProviderFile,
            override: Optional[ComponentOverride] = None,
    ) -> Dict[str, Any]:
        """
        Собирает итоговый словарь переменных, соблюдая иерархию приоритетов.

        Приоритет (от низкого к высокому):
        1. Глобальные переменные consumer (global_vars, включая variant)
        2. Переменные alias provider (alias.vars)
        3. Переменные компонента provider (component.vars)
        4. Переменные компонента consumer (override.vars)
        5. Переменные файла provider (file_config.vars)
        6. Переменные файла consumer (override.files.vars)
        """
        # Начинаем с глобальных переменных consumer (включая variant)
        resolved_vars = global_vars.copy()

        # Переменные alias provider
        if alias_vars:
            resolved_vars.update(alias_vars)

        # Переменные компонента provider
        if component.vars:
            resolved_vars.update(component.vars)

        # Переменные компонента consumer
        if override and override.vars:
            resolved_vars.update(override.vars)

        # Переменные файла provider
        if file_config.vars:
            resolved_vars.update(file_config.vars)

        # Переменные файла consumer (самый высокий приоритет)
        if override and override.files:
            for file_override in override.files:
                if file_override.source == file_config.source and file_override.vars:
                    resolved_vars.update(file_override.vars)
                    break

        return resolved_vars