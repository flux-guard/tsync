# Contributing to tsync

Это руководство поможет вам начать разработку и внести вклад в проект tsync.

## Быстрый старт

### Установка для разработки

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd tsync

# Установите зависимости для разработки
pip install -e ".[dev]"

# Проверьте установку
tsync --version
```

### Запуск тестов

```bash
# Запустить все тесты
pytest

# Запустить с покрытием кода
pytest --cov=tsync --cov-report=html

# Запустить конкретный тестовый файл
pytest tests/test_services/test_sync.py

# Запустить с маркерами
pytest -m unit  # Только unit тесты
pytest -m integration  # Только интеграционные тесты
```

### Проверка качества кода

```bash
# Форматирование кода
black src/ tests/

# Проверка стиля кода
ruff check src/ tests/

# Проверка типов
mypy src/
```

## Архитектура проекта

### Основные компоненты

**Models** (`src/tsync/models/`)
- Определяют структуру данных с помощью Pydantic
- `provider.py` - схема `.toolkit.yml`
- `consumer.py` - схема `.project.toolkit.yml`
- `policy.py` - политики синхронизации
- `context.py` - контекст выполнения

**Services** (`src/tsync/services/`)
- Содержат бизнес-логику
- `sync.py` - главный оркестратор
- `fs.py` - файловые операции
- `git.py` - операции с Git
- `template.py` - рендеринг Jinja2 шаблонов

**Handlers** (`src/tsync/handlers/`)
- Реализация паттерна Strategy для разных политик
- `base.py` - базовый класс
- `sync_strict.py`, `init.py`, `template.py`, `merge.py` - конкретные стратегии
- `mergers/` - обработчики для разных типов файлов при merge

### Паттерны проектирования

1. **Strategy Pattern**: Разные политики синхронизации (sync-strict, init, template, merge)
2. **Dependency Injection**: Сервисы передаются через конструкторы
3. **Factory Pattern**: MergeStrategy выбирает подходящий merger
4. **Single Responsibility**: Каждый класс отвечает за одну область

## Как добавить новую функциональность

### Добавление новой Policy (стратегии синхронизации)

1. **Добавьте enum в `models/policy.py`:**
```python
class Policy(enum.Enum):
    # ... существующие политики
    MY_POLICY = "my-policy"
```

2. **Создайте handler в `handlers/my_policy.py`:**
```python
from .base import BaseStrategy
from tsync.models.context import Context

class MyPolicyStrategy(BaseStrategy):
    def apply(self, context: Context) -> None:
        # Ваша логика
        pass
```

3. **Зарегистрируйте в `services/sync.py`:**
```python
from tsync.handlers.my_policy import MyPolicyStrategy

class SyncService:
    def __init__(self, ...):
        self._handlers = {
            # ... существующие
            Policy.MY_POLICY: MyPolicyStrategy(fs_service),
        }
```

4. **Добавьте тесты в `tests/test_handlers/test_my_policy.py`:**
```python
def test_my_policy_basic():
    strategy = MyPolicyStrategy(mock_fs_service)
    context = Context(...)
    strategy.apply(context)
    # assertions
```

### Добавление нового типа Merger

1. **Добавьте enum в `models/merge.py`:**
```python
class MergeType(enum.Enum):
    # ... существующие типы
    TOML = "toml"
```

2. **Создайте merger в `handlers/mergers/toml.py`:**
```python
from .base import BaseMerger
from tsync.models.merge import MergePriority

class TomlMerger(BaseMerger):
    def merge(self, source_path, destination_path, priority: MergePriority):
        # Используйте self._deep_merge_dicts для словарей
        # Используйте self._fs для файловых операций
        pass
```

3. **Зарегистрируйте в `handlers/merge.py`:**
```python
from .mergers.toml import TomlMerger

class MergeStrategy(BaseStrategy):
    def __init__(self, fs_service):
        self._mergers = {
            # ... существующие
            MergeType.TOML: TomlMerger(fs_service),
        }

        self._extension_to_type = {
            # ... существующие
            ".toml": MergeType.TOML,
        }
```

4. **Добавьте тесты в `tests/test_handlers/test_mergers/test_toml.py`**

### Добавление нового сервиса

1. **Создайте сервис в `services/my_service.py`:**
```python
class MyService:
    def __init__(self, dependency_service):
        self._dep = dependency_service
        self._logger = logging.getLogger(__name__)

    def do_something(self) -> None:
        # Ваша логика
        pass
```

2. **Инициализируйте в `app.py`:**
```python
my_service = MyService(other_service)
sync_service = SyncService(..., my_service)
```

3. **Добавьте тесты в `tests/test_services/test_my_service.py`**

## Правила разработки

### Стиль кода

- Используйте **docstrings** для всех публичных методов и классов
- Комментарии на русском языке (как в существующем коде)
- Следуйте PEP 8 (автоформатирование через black)
- Максимальная длина строки: 120 символов
- Используйте type hints для всех публичных методов

### Обработка ошибок

- Используйте кастомные исключения (`FileSystemError`, `GitServiceError`)
- Всегда логируйте ошибки перед поднятием исключения
- Предоставляйте описательные сообщения об ошибках

```python
# Хорошо
if not path.exists():
    self._logger.error(f"Файл не найден: {path}")
    raise FileSystemError(f"Файл не найден: {path}")

# Плохо
if not path.exists():
    raise Exception("error")
```

### Логирование

- Используйте `logging` вместо `print`
- Уровни логирования:
  - `DEBUG`: Детальная отладочная информация
  - `INFO`: Прогресс выполнения операций
  - `WARNING`: Неожиданные ситуации, но продолжение возможно
  - `ERROR`: Серьезные ошибки

```python
self._logger.debug(f"Загружаю конфигурацию из {path}")
self._logger.info(f"Обрабатываю компонент '{component_id}'")
self._logger.warning(f"Alias '{name}' не найден")
self._logger.error(f"Синхронизация не выполнена: {e}")
```

### Тестирование

- **Unit тесты**: Тестируют отдельные методы с mock-зависимостями
- **Integration тесты**: Тестируют взаимодействие компонентов
- Покрытие кода должно быть не менее 80%
- Используйте фикстуры pytest для переиспользования кода
- Называйте тесты описательно: `test_<что_тестируем>_<ожидаемый_результат>`

```python
# Хорошо
def test_resolve_variables_file_level_override_has_highest_priority():
    ...

# Плохо
def test_vars():
    ...
```

### Безопасность

- **Всегда** валидируйте пути через `fs_service.validate_path_within_directory()`
- Не доверяйте пользовательскому вводу
- Избегайте использования `eval()`, `exec()`, `os.system()`
- Используйте `subprocess.run()` с `check=True` и `capture_output=True`

## Рабочий процесс

### Создание Pull Request

1. Создайте ветку от `main`:
```bash
git checkout -b feature/my-feature
```

2. Внесите изменения и добавьте тесты

3. Убедитесь, что все проверки проходят:
```bash
black src/ tests/
ruff check src/ tests/
mypy src/
pytest
```

4. Создайте коммит с описательным сообщением:
```bash
git commit -m "Добавить поддержку TOML файлов в MergeStrategy"
```

5. Отправьте изменения и создайте PR:
```bash
git push origin feature/my-feature
```

### Структура коммита

- Используйте повелительное наклонение ("Добавить", а не "Добавлен")
- Первая строка - краткое описание (до 72 символов)
- При необходимости добавьте детальное описание через пустую строку

```
Добавить валидацию schema переменных

- Реализован метод _validate_component_schema в SyncService
- Добавлены тесты для обязательных и опциональных переменных
- Обновлена документация
```

## Полезные ресурсы

- [Pydantic документация](https://docs.pydantic.dev/)
- [Pytest документация](https://docs.pytest.org/)
- [Jinja2 документация](https://jinja.palletsprojects.com/)
- [Python logging](https://docs.python.org/3/library/logging.html)

## Вопросы?

Если у вас возникли вопросы или проблемы:
1. Проверьте существующие issues
2. Изучите примеры в тестах
3. Создайте новый issue с подробным описанием
