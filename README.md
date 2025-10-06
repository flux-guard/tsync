# tsync

**Система синхронизации toolkit** для управления общими конфигурациями, шаблонами и файлами между несколькими проектами.

## 📋 Содержание

- [О проекте](#о-проекте)
- [Ключевые возможности](#ключевые-возможности)
- [Установка](#установка)
- [Быстрый старт](#быстрый-старт)
- [Концепции](#концепции)
- [Политики синхронизации](#политики-синхронизации)
- [Конфигурация](#конфигурация)
- [Использование CLI](#использование-cli)
- [Примеры](#примеры)
- [Разработка](#разработка)

## О проекте

`tsync` решает проблему дублирования конфигураций между проектами. Вместо копирования файлов вручную или использования git submodules, tsync позволяет создать централизованный toolkit-репозиторий и синхронизировать из него файлы в ваши проекты с гибкими правилами и переопределениями.

### Проблема

В компаниях с множеством микросервисов часто возникает необходимость:
- Использовать одинаковые конфигурации линтеров (ruff, black, mypy)
- Синхронизировать CI/CD пайплайны
- Поддерживать единый стиль Dockerfile и docker-compose
- Обновлять общие шаблоны и скрипты

### Решение

tsync предоставляет:
- **Централизованное хранилище** конфигураций (toolkit)
- **Версионирование** через git (теги, ветки, коммиты)
- **Гибкие политики синхронизации** (принудительная, инициализация, шаблонизация, слияние)
- **Переопределения** на уровне проекта
- **Фильтрацию по тегам** для выборочной синхронизации

## Ключевые возможности

✅ **Четыре политики синхронизации:**
- `sync-strict` — принудительная перезапись
- `init` — создание файла только если его нет
- `template` — рендеринг Jinja2-шаблонов с переменными
- `merge` — умное слияние (YAML, JSON, текстовые файлы)

✅ **Гибкая система переменных** с иерархией приоритетов

✅ **Фильтрация файлов по тегам** (include/exclude)

✅ **Поддержка версий toolkit** через git

✅ **Локальное кэширование** репозиториев toolkit

## Установка

### Из исходников

```bash
# Клонировать репозиторий
git clone https://github.com/flux-guard/tsync.git
cd tsync

# Установить в режиме разработки
pip install -e .

# Или с dev-зависимостями
pip install -e ".[dev]"
```

### Проверка установки

```bash
tsync --version
```

## Быстрый старт

### 1. Создайте toolkit-репозиторий

Создайте Git-репозиторий с файлом `.toolkit.yml`:

```yaml
toolkit_version: "1.0.0"

aliases:
  python-service:
    description: "Базовая конфигурация для Python-сервиса"
    components:
      - id: "linters"
        description: "Конфигурация линтеров"
        files:
          - source: "templates/python/.ruff.toml"
            destination: ".ruff.toml"
            policy: "sync-strict"

      - id: "dockerfile"
        description: "Dockerfile для сервиса"
        var_schema:
          python_version:
            description: "Версия Python"
            required: true
        files:
          - source: "templates/python/Dockerfile.tpl"
            destination: "Dockerfile"
            policy: "template"
```

### 2. Создайте файл конфигурации в проекте

В вашем проекте создайте `.project.toolkit.yml`:

```yaml
provider:
  url: "git@github.com:your-company/toolkit.git"
  version: "v1.0.0"

vars:
  python_version: "3.11"

sync:
  - alias: "python-service"
```

### 3. Запустите синхронизацию

```bash
tsync
```

Готово! Файлы синхронизированы из toolkit в ваш проект.

## Концепции

### Provider (Поставщик)

**Provider** — это Git-репозиторий, содержащий централизованный набор конфигураций (toolkit). Определяется файлом `.toolkit.yml`.

**Структура:**
- **Aliases** — именованные наборы компонентов
- **Components** — логические группы файлов
- **Files** — физические файлы с политиками синхронизации
- **Schema** — контракты переменных

### Consumer (Потребитель)

**Consumer** — это проект, который использует toolkit. Определяется файлом `.project.toolkit.yml`.

**Возможности:**
- Выбор alias для синхронизации
- Переопределение путей назначения
- Фильтрация файлов по тегам
- Переопределение переменных

### Context (Контекст)

**Context** — объект, передаваемый стратегиям синхронизации, содержащий:
- Путь к исходному файлу (в toolkit)
- Путь к целевому файлу (в проекте)
- Конфигурацию файла
- Объединенные переменные
- Флаг существования целевого файла

## Политики синхронизации

### 1. `sync-strict` — Принудительная синхронизация

Файл всегда перезаписывается версией из toolkit. Локальные изменения теряются.

**Применение:** конфигурации линтеров, CI/CD, которые должны быть едиными.

```yaml
files:
  - source: "configs/.ruff.toml"
    destination: ".ruff.toml"
    policy: "sync-strict"
```

### 2. `init` — Инициализация

Файл создается только если его нет. Существующие файлы не трогаются.

**Применение:** файлы-шаблоны, которые всегда кастомизируются (например, `.env.example`).

```yaml
files:
  - source: "templates/.env.example"
    destination: ".env"
    policy: "init"
```

### 3. `template` — Шаблонизация

Файл рендерится как Jinja2-шаблон с подстановкой переменных.

**Применение:** Dockerfile, Makefile, конфигурации с параметрами проекта.

```yaml
files:
  - source: "templates/Dockerfile.tpl"
    destination: "Dockerfile"
    policy: "template"
```

**Пример шаблона:**
```dockerfile
FROM python:{{ python_version }}-slim
WORKDIR {{ workdir }}
```

### 4. `merge` — Умное слияние

Слияние содержимого с существующим файлом:
- **YAML/JSON**: рекурсивное объединение ключей
- **Текст**: добавление уникальных строк

**Применение:** `.gitignore`, `pyproject.toml`, `package.json`.

```yaml
files:
  - source: "templates/.gitignore"
    destination: ".gitignore"
    policy: "merge"
    merge_priority: "toolkit"  # или "project"
```

## Конфигурация

### Манифест Provider (.toolkit.yml)

```yaml
toolkit_version: "1.0.0"

aliases:
  service-name:
    description: "Описание набора"
    vars:
      # Глобальные переменные для alias
      default_var: "value"

    components:
      - id: "component-id"
        description: "Описание компонента"

        var_schema:
          # Контракт переменных
          required_var:
            description: "Описание переменной"
            required: true
          optional_var:
            description: "Опциональная переменная"
            required: false
            default: "default_value"

        vars:
          # Переменные компонента
          component_var: "value"

        files:
          - source: "path/in/toolkit"
            destination: "path/in/project"
            policy: "sync-strict"  # или "init", "template", "merge"
            merge_as: "yaml"  # для policy: merge
            merge_priority: "toolkit"  # или "project"
            tags: ["tag1", "tag2"]
            vars:
              file_var: "value"
```

### Манифест Consumer (.project.toolkit.yml)

```yaml
provider:
  url: "git@github.com:company/toolkit.git"
  version: "v1.0.0"  # тег, ветка или commit hash

vars:
  # Глобальные переменные проекта
  python_version: "3.11"

sync:
  - alias: "python-service"
    overrides:
      - id: "dockerfile"
        skip: false
        destination_root: "docker/"
        include_tags: ["production"]
        exclude_tags: ["development"]
        vars:
          # Переопределение переменных компонента
          python_version: "3.12"
        files:
          - source: "templates/Dockerfile.tpl"
            destination: "Dockerfile.prod"
            skip: false
            vars:
              # Переопределение переменных файла
              workdir: "/app"
```

### Иерархия переменных (приоритет от низкого к высокому)

1. Глобальные переменные consumer (`vars` в корне) — включая переменные из variant
2. Переменные alias provider (`alias.vars`)
3. Переменные компонента provider (`component.vars`)
4. Переменные компонента consumer (`override.vars`)
5. Переменные файла provider (`file.vars`)
6. **Переменные файла consumer** (`override.files[].vars`) — наивысший приоритет

## Использование CLI

```bash
# Синхронизация текущего проекта
tsync

# Указать директорию проекта
tsync --project-dir /path/to/project

# Указать кэш для toolkit
tsync --cache-dir ~/.tsync/cache

# Подробное логирование
tsync --verbose
tsync -v

# Показать версию
tsync --version

# Справка
tsync --help
```

### Расположение файлов

- **Конфигурация проекта:** `.project.toolkit.yml` (в корне проекта)
- **Кэш toolkit:** `~/.tsync/cache/` (по умолчанию)

## Примеры

### Пример 1: Общие линтеры для Python-проектов

**Toolkit (.toolkit.yml):**
```yaml
toolkit_version: "1.0.0"

aliases:
  python-linters:
    description: "Стандартные линтеры для Python"
    components:
      - id: "linters"
        description: "Конфигурации ruff, black, mypy"
        files:
          - source: "python/.ruff.toml"
            destination: ".ruff.toml"
            policy: "sync-strict"

          - source: "python/pyproject.toml"
            destination: "pyproject.toml"
            policy: "merge"
            merge_as: "yaml"
```

**Проект (.project.toolkit.yml):**
```yaml
provider:
  url: "git@github.com:company/toolkit.git"
  version: "main"

sync:
  - alias: "python-linters"
```

### Пример 2: Dockerfile с переменными

**Toolkit — Dockerfile.tpl:**
```dockerfile
FROM python:{{ python_version }}-slim

WORKDIR {{ workdir }}

RUN pip install --no-cache-dir poetry=={{ poetry_version }}

COPY . .

RUN poetry install --no-dev

CMD ["python", "{{ entrypoint }}"]
```

**Toolkit (.toolkit.yml):**
```yaml
aliases:
  python-service:
    components:
      - id: "dockerfile"
        var_schema:
          python_version:
            description: "Версия Python"
            required: true
          workdir:
            description: "Рабочая директория"
            default: "/app"
          poetry_version:
            description: "Версия Poetry"
            default: "1.7.1"
          entrypoint:
            description: "Точка входа приложения"
            required: true
        files:
          - source: "templates/Dockerfile.tpl"
            destination: "Dockerfile"
            policy: "template"
```

**Проект (.project.toolkit.yml):**
```yaml
provider:
  url: "git@github.com:company/toolkit.git"
  version: "v2.0.0"

vars:
  python_version: "3.11"
  entrypoint: "main.py"

sync:
  - alias: "python-service"
```

### Пример 3: Фильтрация по тегам

**Toolkit (.toolkit.yml):**
```yaml
aliases:
  full-stack:
    components:
      - id: "configs"
        files:
          - source: "backend/Dockerfile"
            destination: "backend/Dockerfile"
            policy: "sync-strict"
            tags: ["backend", "docker"]

          - source: "frontend/Dockerfile"
            destination: "frontend/Dockerfile"
            policy: "sync-strict"
            tags: ["frontend", "docker"]

          - source: "nginx/nginx.conf"
            destination: "nginx.conf"
            policy: "init"
            tags: ["nginx", "production"]
```

**Проект (только backend):**
```yaml
sync:
  - alias: "full-stack"
    overrides:
      - id: "configs"
        include_tags: ["backend"]  # Только backend файлы
```

**Проект (без production):**
```yaml
sync:
  - alias: "full-stack"
    overrides:
      - id: "configs"
        exclude_tags: ["production"]  # Всё кроме production
```

### Пример 4: Использование Alias vars для общих настроек

**Toolkit (.toolkit.yml):**
```yaml
aliases:
  python-app:
    description: "Python приложение"
    vars:
      # Общие переменные для всех компонентов в этом alias
      python_version: "3.11"
      app_env: "production"
      log_level: "INFO"
    components:
      - id: "dockerfile"
        files:
          - source: "templates/Dockerfile.j2"
            destination: "Dockerfile"
            policy: "template"

      - id: "config"
        files:
          - source: "templates/config.yaml.j2"
            destination: "config/app.yaml"
            policy: "template"
```

**Проект (.project.toolkit.yml):**
```yaml
provider:
  url: "git@github.com:company/toolkit.git"
  version: "v1.0.0"

vars:
  app_name: "my-service"  # Глобальная переменная проекта

sync:
  - alias: "python-app"
    # python_version, app_env, log_level наследуются из alias.vars
    # и будут доступны во всех компонентах
    overrides:
      - id: "config"
        vars:
          log_level: "DEBUG"  # Переопределяем для конкретного компонента
```

В этом примере:
- `python_version: "3.11"` и `app_env: "production"` доступны во всех компонентах alias
- `log_level: "INFO"` переопределяется на `"DEBUG"` для компонента `config`
- `app_name: "my-service"` доступен глобально из корня `.project.toolkit.yml`

## Разработка

### Требования

- Python >= 3.10
- Git

### Установка зависимостей

```bash
# Установить с dev-зависимостями
pip install -e ".[dev]"
```

### Запуск тестов

```bash
pytest
pytest --cov=tsync --cov-report=html
```

### Форматирование кода

```bash
# Форматирование
black src/

# Проверка стиля
ruff check src/

# Автоисправление
ruff check --fix src/
```

### Проверка типов

```bash
mypy src/
```

### Структура проекта

```
tsync/
├── src/
│   └── tsync/
│       ├── __init__.py
│       ├── cli.py              # CLI интерфейс
│       ├── app.py              # Главное приложение
│       ├── models/             # Pydantic модели
│       │   ├── consumer.py     # Модели consumer
│       │   ├── provider.py     # Модели provider
│       │   ├── context.py      # Контекст синхронизации
│       │   ├── policy.py       # Политики
│       │   └── merge.py        # Типы слияния
│       ├── handlers/           # Стратегии синхронизации
│       │   ├── base.py         # Базовый класс
│       │   ├── sync_strict.py  # sync-strict
│       │   ├── init.py         # init
│       │   ├── template.py     # template
│       │   ├── merge.py        # merge (диспетчер)
│       │   └── mergers/        # Обработчики слияния
│       │       ├── yaml.py
│       │       ├── json.py
│       │       └── text.py
│       └── services/           # Сервисы
│           ├── sync.py         # Оркестратор синхронизации
│           ├── git.py          # Git операции
│           ├── fs.py           # Файловая система
│           └── template.py     # Рендеринг шаблонов
├── tests/                      # Тесты
├── pyproject.toml             # Конфигурация проекта
├── README.md                  # Этот файл
└── CLAUDE.md                  # Документация для Claude Code
```

### Архитектура

- **Strategy Pattern**: Каждая политика — отдельная стратегия
- **Service Layer**: Изоляция бизнес-логики
- **Dependency Injection**: Сервисы инжектятся в конструкторы
- **Pydantic Models**: Валидация конфигураций

## Лицензия

MIT License. См. [LICENSE](LICENSE) для деталей.

## Авторы

- **flux-guard** - [GitHub](https://github.com/flux-guard)

## Поддержка

Если у вас возникли проблемы или вопросы:
- Создайте [Issue](https://github.com/flux-guard/tsync/issues)
- Прочитайте [CLAUDE.md](CLAUDE.md) для разработчиков

---

**tsync** — синхронизация конфигураций должна быть простой! 🚀
