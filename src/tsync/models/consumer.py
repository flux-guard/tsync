"""
Этот модуль содержит Pydantic модели для парсинга и валидации
манифеста потребителя (`.project.toolkit.yml`).

Эти модели описывают, какой toolkit используется, какие алиасы и компоненты
из него синхронизируются, и как их свойства (пути, переменные, состав файлов)
переопределяются для конкретного проекта.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, model_validator


class FileOverride(BaseModel):
    """
    Контракт для переопределения свойств одного файла внутри компонента.
    """
    source: str
    """
    Что делает: Идентификатор файла. Указывает, какой именно файл из компонента
    мы переопределяем. Должен точно совпадать с `source` в манифесте provider-а.
    Форма: Строка-путь.
    Пример: "templates/python/Dockerfile.tpl"
    """
    destination: Optional[str] = None
    """
    Что делает: Новый путь назначения для файла, заменяющий `destination` из provider-а.
    Форма: Строка-путь.
    Пример: "build/Dockerfile.dev"
    """
    skip: bool = False
    """
    Что делает: Если `true`, этот файл не будет синхронизирован.
    Форма: `true` или `false`.
    """
    vars: Optional[Dict[str, Any]] = None
    """
    Что делает: Словарь переменных, применяемый только к этому файлу.
    Имеет самый высокий приоритет в иерархии переопределения.
    Форма: Словарь (ключ-значение).
    """

    @model_validator(mode="after")
    def validate_skip_and_destination(self) -> "FileOverride":
        """
        Валидация: если файл пропускается (skip=True),
        то другие переопределения не имеют смысла.
        """
        if self.skip:
            if self.destination is not None:
                raise ValueError(
                    f"Файл '{self.source}' помечен как пропускаемый (skip=True), "
                    f"но указан destination. Это не имеет смысла."
                )
            if self.vars is not None:
                raise ValueError(
                    f"Файл '{self.source}' помечен как пропускаемый (skip=True), "
                    f"но указаны vars. Это не имеет смысла."
                )
        return self


class ComponentOverride(BaseModel):
    """
    Контракт для переопределения свойств и поведения целого компонента.
    """
    id: str
    """
    Что делает: Идентификатор компонента. Указывает, какой компонент из alias-а
    мы настраиваем.
    Форма: Строка, совпадающая с `id` компонента у provider-а.
    Пример: "dockerfile"
    """
    skip: bool = False
    """
    Что делает: Если `true`, весь компонент (все его файлы) будет пропущен.
    Форма: `true` или `false`.
    """
    destination_root: Optional[str] = None
    """
    Что делает: Новая корневая директория для всех файлов компонента. Их пути
    `destination` будут вычислены относительно этого каталога.
    Форма: Строка-путь.
    Пример: "ci/configs"
    """
    include_tags: Optional[List[str]] = None
    """
    Что делает: Правило фильтрации. Синхронизирует *только* те файлы, у которых
    есть хотя бы один из указанных тегов.
    Форма: Список строк-тегов.
    Пример: ["lang:go", "common"]
    """
    exclude_tags: Optional[List[str]] = None
    """
    Что делает: Правило фильтрации. Исключает из синхронизации файлы,
    у которых есть хотя бы один из указанных тегов.
    Форма: Список строк-тегов.
    """
    vars: Optional[Dict[str, Any]] = None
    """
    Что делает: Словарь переменных, применяемый ко всем файлам компонента.
    Имеет приоритет над глобальными `vars`.
    Форма: Словарь (ключ-значение).
    """
    files: Optional[List[FileOverride]] = None
    """
    Что делает: Список для точечного переопределения файлов внутри компонента.
    Форма: Список объектов `FileOverride`.
    """

    @model_validator(mode="after")
    def validate_skip_and_other_fields(self) -> "ComponentOverride":
        """
        Валидация: если компонент пропускается (skip=True),
        то другие переопределения не имеют смысла и будут проигнорированы.
        Выдаем предупреждение в логах.
        """
        if self.skip:
            has_other_config = any([
                self.destination_root is not None,
                self.include_tags is not None,
                self.exclude_tags is not None,
                self.vars is not None,
                self.files is not None,
            ])
            if has_other_config:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Компонент '{self.id}' помечен как пропускаемый (skip=True), "
                    f"но указаны другие настройки (destination_root, tags, vars, files). "
                    f"Эти настройки будут проигнорированы."
                )
        return self

    @model_validator(mode="after")
    def validate_include_exclude_tags(self) -> "ComponentOverride":
        """
        Валидация: проверяем, что include_tags и exclude_tags не пересекаются.
        """
        if self.include_tags and self.exclude_tags:
            overlap = set(self.include_tags) & set(self.exclude_tags)
            if overlap:
                raise ValueError(
                    f"Компонент '{self.id}': теги не могут одновременно быть в include_tags "
                    f"и exclude_tags. Пересечение: {overlap}"
                )
        return self


class SyncItem(BaseModel):
    """
    Описывает один элемент в списке 'sync' в манифесте consumer-а,
    как правило, один запрашиваемый alias и его переопределения.
    """
    alias: str
    """
    Что делает: Имя alias'а из манифеста provider-а, который мы хотим синхронизировать.
    Форма: Строка.
    Пример: "python-service"
    """
    variant: Optional[str] = None
    """
    Что делает: Имя варианта (variant) для применения к этому alias'у.
    Если указан, будут применены дефолтные переменные из variant.
    Форма: Строка.
    Пример: "poetry"
    """
    overrides: Optional[List[ComponentOverride]] = None
    """
    Что делает: Список переопределений для компонентов внутри этого alias-а.
    Форма: Список объектов `ComponentOverride`.
    """


class ProviderConfig(BaseModel):
    """
    Описывает, откуда брать toolkit (репозиторий-поставщик).
    """
    url: str
    """
    Что делает: URL Git-репозитория, который является provider-ом.
    Форма: Строка с URL.
    Пример: "git@github.com:your-company/toolkit.git"
    """
    version: str
    """
    Что делает: Версия toolkit-а для использования (ветка, тег или хеш коммита).
    Форма: Строка.
    Пример: "v1.2.0"
    """


class ProjectToolkitConfig(BaseModel):
    """
    Корневая модель для всего манифеста .project.toolkit.yml.
    """
    provider: ProviderConfig
    """
    Что делает: Определяет, какой toolkit использовать.
    Форма: Объект `ProviderConfig`.
    """
    vars: Optional[Dict[str, Any]] = None
    """
    Что делает: Глобальные переменные для всего проекта. Имеют самый низкий
    приоритет среди переменных потребителя.
    Форма: Словарь (ключ-значение).
    """
    sync: List[SyncItem]
    """
    Что делает: Список того, что нужно синхронизировать из toolkit-а.
    Форма: Список объектов `SyncItem`.
    """