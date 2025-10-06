"""
Этот модуль содержит Pydantic модели для парсинга и валидации
манифеста поставщика (`.toolkit.yml`).

Эти модели описывают "каталог" доступных для синхронизации файлов,
компонентов и алиасов, а также их свойства, зависимости и контракты
переменных.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from .policy import Policy
from .merge import MergeType, MergePriority


class VarDefinition(BaseModel):
    """
    Контракт, описывающий одну переменную в схеме компонента.
    Определяет, является ли она обязательной, ее описание
    и значение по умолчанию.
    """
    description: str
    """
    Что делает: Человекочитаемое описание переменной, объясняющее ее назначение.
    Форма: Строка.
    Пример: "Версия Python для базового Docker-образа"
    """
    required: bool = False
    """
    Что делает: Указывает, обязан ли потребитель предоставить значение.
    Если `True`, и значение не предоставлено, tsync должен выдать ошибку.
    Форма: `true` или `false`.
    """
    default: Optional[Any] = None
    """
    Что делает: Значение по умолчанию, если `required: false` и потребитель
    не предоставил своего значения.
    Форма: Любой валидный тип YAML (строка, число, список).
    Пример: "/app"
    """

    @model_validator(mode="after")
    def validate_required_and_default(self) -> "VarDefinition":
        """
        Валидация: если переменная обязательна (required=True),
        то значение по умолчанию должно быть None.
        """
        if self.required and self.default is not None:
            raise ValueError(
                f"Переменная '{self.description}' не может быть одновременно обязательной "
                f"(required=True) и иметь значение по умолчанию. "
                f"Либо установите required=False, либо уберите default."
            )
        return self


class File(BaseModel):
    """
    Контракт, описывающий один физический файл, его расположение,
    стратегию синхронизации, теги и переменные.
    """
    source: str
    """
    Что делает: Относительный путь к исходному файлу внутри репозитория provider-а.
    Форма: Строка-путь.
    Пример: "templates/python/Dockerfile.tpl"
    """
    destination: str
    """
    Что делает: Относительный путь, по которому файл будет создан в репозитории
    consumer-а. Потребитель может переопределить это значение.
    Форма: Строка-путь.
    Пример: "Dockerfile"
    """
    policy: Policy
    """
    Что делает: Стратегия синхронизации, определяющая, как tsync будет
    обращаться с файлом.
    Форма: Одна из строк: "sync-strict", "init", "template", "merge".
    """
    merge_as: Optional[MergeType] = None
    """
    Что делает: Позволяет принудительно указать, какой тип обработчика
    слияния использовать для этого файла, игнорируя его расширение.
    Форма: Строка, например "yaml", "json", "text".
    """
    merge_priority: Optional[MergePriority] = MergePriority.TOOLKIT
    """
    Что делает: Определяет, чьи изменения имеют приоритет при слиянии.
    'toolkit' (по умолчанию): значения из toolkit перезаписывают локальные.
    'project': локальные значения в файле проекта сохраняются.
    Форма: "toolkit" или "project".
    """
    tags: Optional[List[str]] = None
    """
    Что делает: Список тегов для маркировки файла, позволяющий потребителю
    фильтровать файлы внутри компонента.
    Форма: Список строк.
    Пример: ["lang:python", "docker"]
    """
    vars: Optional[Dict[str, Any]] = None
    """
    Что делает: Словарь переменных, специфичных только для этого файла.
    Имеет самый низкий приоритет в каскаде переменных provider-а.
    Форма: Словарь (ключ-значение).
    """

    @field_validator("policy")
    @classmethod
    def validate_policy(cls, v: Policy) -> Policy:
        """Проверка, что политика является валидным значением Policy enum."""
        if not isinstance(v, Policy):
            raise ValueError(f"Недопустимое значение политики: {v}")
        return v

    @model_validator(mode="after")
    def validate_merge_fields(self) -> "File":
        """
        Валидация: merge_as и merge_priority имеют смысл только для policy='merge'.
        """
        if self.policy != Policy.MERGE:
            if self.merge_as is not None:
                raise ValueError(
                    f"Поле 'merge_as' может использоваться только с policy='merge', "
                    f"но установлено policy='{self.policy.value}'"
                )
            if self.merge_priority != MergePriority.TOOLKIT:
                raise ValueError(
                    f"Поле 'merge_priority' может использоваться только с policy='merge', "
                    f"но установлено policy='{self.policy.value}'"
                )
        return self


class Component(BaseModel):
    """
    Контракт, описывающий один логический компонент.

    Компонент - это именованная группа из одного или нескольких файлов,
    объединенных общей целью (например, 'linters', 'dockerfile').
    Именно компонент определяет схему переменных, необходимых
    для его рендеринга.
    """
    id: str
    """
    Что делает: Уникальный идентификатор компонента в рамках alias-а.
    Форма: Строка без пробелов.
    Пример: "dockerfile"
    """
    description: str
    """
    Что делает: Описание назначения компонента.
    Форма: Строка.
    Пример: "Dockerfile для запуска сервиса в контейнере"
    """
    var_schema: Optional[Dict[str, VarDefinition]] = None
    """
    Что делает: "Контракт" переменных, которые ожидает компонент для своей работы.
    Форма: Словарь, где ключ — имя переменной, а значение — объект `VarDefinition`.
    """
    vars: Optional[Dict[str, Any]] = None
    """
    Что делает: Общие переменные по умолчанию для всех файлов внутри этого компонента.
    Форма: Словарь (ключ-значение).
    """
    files: List[File]
    """
    Что делает: Список объектов `File`, которые входят в состав этого компонента.
    Форма: Список объектов `File`.
    """


class Variant(BaseModel):
    """
    Контракт, описывающий один "вариант" (например, язык или фреймворк)
    внутри alias'а.
    """
    description: str
    """
    Что делает: Описание варианта.
    Форма: Строка.
    Пример: "Использовать Poetry для управления зависимостями"
    """
    defaults: Dict[str, Any] = Field(default_factory=dict)
    """
    Что делает: Словарь переменных по умолчанию, которые активируются
    при выборе этого варианта потребителем.
    Форма: Словарь (ключ-значение).
    Пример: { "package_manager": "poetry" }
    """


class Alias(BaseModel):
    """
    Контракт, описывающий один alias в манифесте `.toolkit.yml`.

    Alias - это именованный набор компонентов, который consumer может
    запросить как единое целое. Например, 'python-service'.
    """
    description: str
    """
    Что делает: Описание всего набора компонентов.
    Форма: Строка.
    Пример: "Базовая конфигурация для Python-сервиса"
    """
    vars: Optional[Dict[str, Any]] = None
    """
    Что делает: Переменные, общие для всех компонентов этого alias-а.
    Форма: Словарь (ключ-значение).
    """
    components: List[Component]
    """
    Что делает: Список компонентов, входящих в alias.
    Форма: Список объектов `Component`.
    """
    variants: Optional[Dict[str, Variant]] = None
    """
    Что делает: Доступные вариации для этого alias-а.
    Форма: Словарь, где ключ — имя варианта, а значение — объект `Variant`.
    """


class ToolkitConfig(BaseModel):
    """
    Корневая модель для всего манифеста .toolkit.yml.
    """
    toolkit_version: str
    """
    Что делает: Версия самого toolkit-а, позволяющая потребителям
    закрепиться на определенной версии.
    Форма: Строка (рекомендуется семантическое версионирование).
    Пример: "1.2.0"
    """
    aliases: Dict[str, Alias]
    """
    Что делает: Все доступные наборы конфигураций (алиасы).
    Форма: Словарь, где ключ — имя alias-а, а значение — объект `Alias`.
    """