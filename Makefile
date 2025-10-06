# ==============================================================================
#                           Главный Makefile проекта
# ==============================================================================
#
# Назначение:
#   Главный Makefile проекта, который включает модульные .mk файлы и
#   предоставляет унифицированный интерфейс для всех операций проекта.
#
# Использование:
#   make tk-help              # Показать все доступные команды
#   make tk-<target>          # Выполнить конкретную команду
#
# Структура:
#   - Makefile (этот файл) - главная точка входа
#   - build/make/*.mk - модульные файлы с командами
#
# Документация: https://www.gnu.org/software/make/manual/
# ==============================================================================

# PHONY targets - не являются файлами
.PHONY: tk-help tk-all tk-clean

# По умолчанию показать help
.DEFAULT_GOAL := tk-help

# --- Переменные проекта (с префиксом TK_) ---
TK_PROJECT_NAME ?= $(shell basename $(CURDIR))
TK_VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
TK_BUILD_TIME := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
TK_GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# --- Пути ---
TK_BUILD_DIR := build
TK_MAKE_DIR := $(TK_BUILD_DIR)/make
TK_BIN_DIR := $(TK_BUILD_DIR)/bin
TK_DIST_DIR := $(TK_BUILD_DIR)/dist

# --- Цвета для вывода (опционально) ---
TK_COLOR_RESET := \033[0m
TK_COLOR_BOLD := \033[1m
TK_COLOR_GREEN := \033[32m
TK_COLOR_YELLOW := \033[33m
TK_COLOR_BLUE := \033[34m

# ==============================================================================
#                           ПОДКЛЮЧЕНИЕ МОДУЛЕЙ
# ==============================================================================
# Включить модульные Makefile'ы, если они существуют

-include $(TK_MAKE_DIR)/help.mk
-include $(TK_MAKE_DIR)/golang.mk
-include $(TK_MAKE_DIR)/docker.mk
-include $(TK_MAKE_DIR)/commits.mk

# ==============================================================================
#                           ОСНОВНЫЕ ЦЕЛИ
# ==============================================================================

## Показать help (по умолчанию)
tk-help:
	@echo "$(TK_COLOR_BOLD)$(TK_PROJECT_NAME) - Доступные команды$(TK_COLOR_RESET)"
	@echo ""
	@echo "$(TK_COLOR_BLUE)Основные цели:$(TK_COLOR_RESET)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^tk-[a-zA-Z_-]+:.*?##/ { printf "  $(TK_COLOR_GREEN)%-20s$(TK_COLOR_RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(TK_COLOR_YELLOW)Подключенные модули:$(TK_COLOR_RESET)"
	@ls -1 $(TK_MAKE_DIR)/*.mk 2>/dev/null | xargs -n1 basename | sed 's/^/  - /' || echo "  Модули не найдены"
	@echo ""
	@echo "Запустите 'make tk-<модуль>-help' для команд модуля (например, 'make tk-go-help')"

## Собрать всё
tk-all: tk-deps tk-build tk-test ## Собрать всё (зависимости + сборка + тесты)

## Очистить build артефакты
tk-clean: ## Очистить build артефакты
	@echo "$(TK_COLOR_YELLOW)Очистка build артефактов...$(TK_COLOR_RESET)"
	rm -rf $(TK_BUILD_DIR)/bin $(TK_BUILD_DIR)/dist
	rm -rf coverage.out coverage.html coverage.txt
	rm -f *.log
	@echo "$(TK_COLOR_GREEN)✓ Очистка завершена$(TK_COLOR_RESET)"

## Глубокая очистка (включая зависимости)
tk-clean-all: tk-clean ## Глубокая очистка (включая зависимости)
	@echo "$(TK_COLOR_YELLOW)Глубокая очистка...$(TK_COLOR_RESET)"
	rm -rf vendor/
	rm -rf node_modules/
	go clean -cache -testcache -modcache 2>/dev/null || true
	@echo "$(TK_COLOR_GREEN)✓ Глубокая очистка завершена$(TK_COLOR_RESET)"

## Версия проекта
tk-version: ## Показать версию проекта
	@echo "$(TK_COLOR_BOLD)Информация о версии:$(TK_COLOR_RESET)"
	@echo "  Проект:        $(TK_PROJECT_NAME)"
	@echo "  Версия:        $(TK_VERSION)"
	@echo "  Коммит:        $(TK_GIT_COMMIT)"
	@echo "  Время сборки:  $(TK_BUILD_TIME)"

# ==============================================================================
#                           СЛУЖЕБНЫЕ ЦЕЛИ
# ==============================================================================

## Проверить необходимые инструменты
tk-check-tools: ## Проверить установку необходимых инструментов
	@echo "$(TK_COLOR_YELLOW)Проверка необходимых инструментов...$(TK_COLOR_RESET)"
	@command -v go >/dev/null 2>&1 || { echo "❌ Go не установлен"; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo "❌ Git не установлен"; exit 1; }
	@echo "$(TK_COLOR_GREEN)✓ Все необходимые инструменты установлены$(TK_COLOR_RESET)"

## Настроить окружение разработки
tk-setup: tk-check-tools ## Настроить окружение разработки
	@echo "$(TK_COLOR_YELLOW)Настройка окружения разработки...$(TK_COLOR_RESET)"
	@$(MAKE) tk-deps
	@command -v pre-commit >/dev/null 2>&1 && pre-commit install || echo "⚠️  pre-commit не установлен, пропуск"
	@echo "$(TK_COLOR_GREEN)✓ Окружение разработки готово$(TK_COLOR_RESET)"
