# Тесты для tsync

Этот каталог содержит все тесты для проекта tsync.

## Структура

```
tests/
├── conftest.py                  # Общие fixtures для всех тестов
├── test_models/                 # Тесты моделей Pydantic
│   ├── test_consumer.py         # Тесты моделей consumer
│   ├── test_provider.py         # Тесты моделей provider
│   └── test_context.py          # Тесты модели Context
├── test_services/               # Тесты сервисов
│   ├── test_fs.py               # Тесты FileSystemService
│   └── test_template.py         # Тесты TemplateService
├── test_handlers/               # Тесты стратегий синхронизации
│   ├── test_sync_strict.py      # Тесты SyncStrictStrategy
│   ├── test_init.py             # Тесты InitStrategy
│   ├── test_template.py         # Тесты TemplateStrategy
│   └── test_mergers/            # Тесты обработчиков слияния
│       ├── test_yaml.py         # Тесты YamlMerger
│       ├── test_json.py         # Тесты JsonMerger
│       └── test_text.py         # Тесты TextMerger
└── integration/                 # Интеграционные тесты
    └── test_full_sync.py        # Тесты полного цикла синхронизации
```

## Запуск тестов

### Все тесты

```bash
pytest
```

### Конкретная категория тестов

```bash
# Только unit тесты
pytest -m unit

# Только интеграционные тесты
pytest -m integration

# Тесты конкретного модуля
pytest tests/test_models/
pytest tests/test_services/test_fs.py
```

### С покрытием кода

```bash
# Покрытие в терминале
pytest --cov=tsync --cov-report=term-missing

# Покрытие с HTML отчетом
pytest --cov=tsync --cov-report=html
# Откройте htmlcov/index.html в браузере
```

### Подробный вывод

```bash
# Показать все тесты (включая проходящие)
pytest -v

# Показать print statements
pytest -s

# Остановиться на первой ошибке
pytest -x

# Запустить последние упавшие тесты
pytest --lf
```

### Параллельный запуск

```bash
# Установите pytest-xdist
pip install pytest-xdist

# Запуск в несколько процессов
pytest -n auto
```

## Написание новых тестов

### Использование fixtures

Все общие fixtures определены в `conftest.py`:

```python
def test_my_feature(temp_dir, fs_service):
    """temp_dir и fs_service доступны автоматически."""
    test_file = temp_dir / "test.txt"
    fs_service.write_file(test_file, "content")
    assert test_file.exists()
```

### Доступные fixtures

- `temp_dir` — временная директория, автоматически удаляется
- `fs_service` — FileSystemService
- `template_service` — TemplateService
- `git_service` — GitService с временным кэшем
- `sync_service` — SyncService
- `sample_provider_config` — пример конфигурации provider
- `sample_consumer_config` — пример конфигурации consumer
- `provider_toolkit_dir` — временная директория toolkit
- `consumer_project_dir` — временная директория проекта

### Структура теста

```python
class TestMyFeature:
    """Группа тестов для конкретной функциональности."""

    def test_positive_case(self):
        """Тест: позитивный сценарий."""
        # Arrange (подготовка)
        data = {"key": "value"}

        # Act (действие)
        result = process_data(data)

        # Assert (проверка)
        assert result["key"] == "value"

    def test_error_case(self):
        """Тест: проверка ошибки."""
        with pytest.raises(ValueError) as exc_info:
            invalid_function()

        assert "expected error" in str(exc_info.value)
```

### Маркировка тестов

```python
import pytest

@pytest.mark.unit
def test_unit_test():
    """Unit тест."""
    pass

@pytest.mark.integration
def test_integration():
    """Интеграционный тест."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Медленный тест."""
    pass
```

## Покрытие кода

Целевое покрытие: **≥ 80%**

Текущее покрытие можно проверить:

```bash
pytest --cov=tsync --cov-report=term-missing
```

## CI/CD

Тесты автоматически запускаются при:
- Push в любую ветку
- Создании Pull Request
- Перед релизом

## Отладка тестов

### В VSCode

1. Установите расширение Python
2. Поставьте breakpoint в тесте
3. Запустите "Python: Debug Test" из контекстного меню

### В командной строке

```bash
# Запустить с отладчиком Python
pytest --pdb

# Войти в отладчик при ошибке
pytest --pdb-trace
```

### Логирование

```python
import logging

def test_with_logging(caplog):
    """Тест с проверкой логов."""
    with caplog.at_level(logging.INFO):
        my_function_that_logs()

    assert "expected log message" in caplog.text
```

## Советы

1. **Именование**: Называйте тесты понятно: `test_<что_тестируем>_<ожидаемый_результат>`
2. **Изоляция**: Каждый тест должен быть независимым
3. **Fixture scope**: Используйте `scope="module"` для дорогих fixture
4. **Parametrize**: Используйте `@pytest.mark.parametrize` для множественных входов
5. **Mock**: Используйте `unittest.mock` или `pytest-mock` для мокирования

## Пример параметризованного теста

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    """Тест: преобразование в верхний регистр."""
    assert input.upper() == expected
```

## Проблемы и решения

### Тесты падают локально, но проходят в CI

- Проверьте версии зависимостей
- Проверьте переменные окружения
- Убедитесь, что тесты не зависят от внешних сервисов

### Медленные тесты

- Используйте `@pytest.mark.slow` для долгих тестов
- Запускайте их отдельно: `pytest -m "not slow"`
- Рассмотрите использование `pytest-xdist` для параллелизации

### Проблемы с временными файлами

- Всегда используйте `temp_dir` fixture
- Убедитесь, что cleanup происходит автоматически
- Не полагайтесь на конкретные пути файловой системы
